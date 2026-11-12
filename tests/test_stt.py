import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from talkeys import paths, stt


@pytest.fixture
def fake_model(monkeypatch):
    model = MagicMock()
    fake_onnx_asr = MagicMock()
    fake_onnx_asr.load_model.return_value.with_timestamps.return_value = model
    monkeypatch.setitem(sys.modules, "onnx_asr", fake_onnx_asr)
    return fake_onnx_asr, model


def test_load_picks_the_model_and_quantization_for_the_language(fake_model):
    fake_onnx_asr, _model = fake_model

    stt.load("en")

    model_name, quantization = stt.MODEL_BY_LANG["en"]
    assert fake_onnx_asr.load_model.call_args.args == (model_name, paths.MODELS_DIR / model_name)
    assert fake_onnx_asr.load_model.call_args.kwargs["quantization"] == quantization


def test_without_context_the_phrase_is_recognized_alone(fake_model):
    _fake_onnx_asr, model = fake_model
    model.recognize.return_value = SimpleNamespace(text="Привет.", tokens=None, timestamps=None)

    text = stt.load("ru")(np.array([0, 16384, -16384], dtype=np.int16).tobytes())

    assert text == "Привет."
    waveform = model.recognize.call_args.args[0]
    assert waveform.dtype == np.float32
    assert list(waveform) == [0.0, 0.5, -0.5]


def test_with_context_only_the_words_of_the_new_audio_are_returned(fake_model):
    _fake_onnx_asr, model = fake_model
    one_second = b"\0\0" * stt.SAMPLE_RATE
    model.recognize.return_value = SimpleNamespace(
        text="новым, скажем, движком",
        tokens=[" новым", ",", " скаж", "ем", ",", " движ", "ком"],
        timestamps=[0.2, 0.6, 0.9, 1.1, 1.3, 1.5, 1.7],
    )

    text = stt.load("ru")(one_second, context=one_second)

    assert text == "движком"
    assert len(model.recognize.call_args.args[0]) == 2 * stt.SAMPLE_RATE  # context + phrase


def test_with_context_a_model_without_timestamps_falls_back_to_the_phrase_alone(fake_model):
    _fake_onnx_asr, model = fake_model
    model.recognize.side_effect = [
        SimpleNamespace(text="контекст и фраза", tokens=None, timestamps=None),
        SimpleNamespace(text="фраза", tokens=None, timestamps=None),
    ]

    text = stt.load("ru")(b"\0\0", context=b"\0\0")

    assert text == "фраза"


def test_a_word_cut_by_the_boundary_stays_with_the_context():
    tokens = [" скаж", "ем", " движ", "ком"]

    assert stt.text_after(tokens, [0.9, 1.1, 1.5, 1.7], seconds=1.0) == "движком"


def test_punctuation_right_after_the_boundary_is_glued_without_a_space():
    assert stt.text_after([" да", "?", " Нет", "."], [0.5, 1.2, 1.4, 1.6], 1.0) == "Нет."


def test_nothing_after_the_boundary_gives_empty_text():
    assert stt.text_after([" да"], [0.5], 1.0) == ""


def test_every_language_the_user_can_switch_to_has_a_model():
    assert set(stt.MODEL_BY_LANG) == set(paths.LANGS)
