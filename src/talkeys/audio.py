"""Pure audio-analysis helpers shared by the silence watchdog."""
import array


def rms(pcm_s16le_mono: bytes) -> float:
    """Root-mean-square amplitude of 16-bit signed little-endian mono PCM.

    Returns 0.0 for empty input. A trailing odd byte (a truncated final
    sample) is ignored rather than raising.
    """
    whole_samples_byte_count = len(pcm_s16le_mono) - (len(pcm_s16le_mono) % 2)
    samples = array.array("h")
    samples.frombytes(pcm_s16le_mono[:whole_samples_byte_count])
    if not samples:
        return 0.0
    return (sum(sample * sample for sample in samples) / len(samples)) ** 0.5
