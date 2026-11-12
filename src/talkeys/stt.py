"""Offline speech-to-text via onnx-asr: GigaAM-v3 for Russian (punctuation
and capitalization built in), Parakeet TDT v3 for English. Models are
downloaded from Hugging Face into `paths.MODELS_DIR` on first use (install.sh
does it up front) — plain files, not the shared Hugging Face cache, whose
blob symlinks onnxruntime rejects ("External data path escapes model
directory")."""
import os
import re
from collections.abc import Callable
from typing import Final

from . import paths

SAMPLE_RATE: Final = 16000
BYTES_PER_SECOND = SAMPLE_RATE * 2  # mono s16le
# (onnx-asr model name, quantization). Parakeet's full-precision encoder is
# 2.4GB; int8 is a quarter of that and plenty for English.
MODEL_BY_LANG = {
    "ru": ("gigaam-v3-e2e-rnnt", None),
    "en": ("nemo-parakeet-tdt-0.6b-v3", "int8"),
}
# onnx-asr's own rule for gluing tokens into text: a token's leading space
# starts a new word, except at the very start and before punctuation.
_SPACE_PATTERN = re.compile(r"\A\s|\s\B|(\s)\b")


def load(lang: str) -> Callable[[bytes, bytes], str]:
    """Loads the model for `lang` and returns `transcribe(pcm, context)`:
    16 kHz mono s16le `pcm` to text. `context` is audio said right before
    `pcm` (already typed): it is recognized together with `pcm` so the model
    hears the whole sentence, but only the words of `pcm` are returned."""
    import numpy as np
    import onnx_asr
    import onnxruntime

    options = onnxruntime.SessionOptions()
    # Leave half the cores to the desktop: dictation must never make the
    # machine stutter.
    options.intra_op_num_threads = max(1, (os.cpu_count() or 2) // 2)
    model_name, quantization = MODEL_BY_LANG[lang]
    model = onnx_asr.load_model(
        model_name, paths.MODELS_DIR / model_name, quantization=quantization, sess_options=options
    ).with_timestamps()

    def recognize(audio: bytes):
        waveform = (np.frombuffer(audio, dtype=np.int16) / 32768).astype(np.float32)
        return model.recognize(waveform, sample_rate=SAMPLE_RATE)

    def transcribe(pcm: bytes, context: bytes = b"") -> str:
        if context:
            result = recognize(context + pcm)
            if result.tokens is not None and result.timestamps is not None:
                return text_after(result.tokens, result.timestamps, len(context) / BYTES_PER_SECOND)
        return recognize(pcm).text  # no context, or a model without timestamps

    return transcribe


def text_after(tokens: list[str], timestamps: list[float], seconds: float) -> str:
    """The text of the words that start at or after `seconds`. A word cut by
    the boundary belongs to the context: it was already typed."""
    start = next(
        (
            index
            for index, (token, timestamp) in enumerate(zip(tokens, timestamps))
            if timestamp >= seconds and (index == 0 or token[:1].isspace())
        ),
        len(tokens),
    )
    return re.sub(_SPACE_PATTERN, lambda match: " " if match.group(1) else "", "".join(tokens[start:]))
