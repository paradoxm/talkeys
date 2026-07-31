import pytest

from talkeys.audio import rms


def _pcm_from_samples(samples):
    return b"".join(sample.to_bytes(2, "little", signed=True) for sample in samples)


def test_returns_zero_for_empty_input():
    assert rms(b"") == 0.0


def test_returns_zero_for_all_zero_samples():
    silent_pcm = _pcm_from_samples([0] * 100)

    assert rms(silent_pcm) == 0.0


def test_returns_the_constant_amplitude_when_every_sample_is_equal():
    constant_amplitude = 1000
    constant_pcm = _pcm_from_samples([constant_amplitude] * 50)

    assert rms(constant_pcm) == pytest.approx(float(constant_amplitude))


def test_treats_positive_and_negative_amplitude_the_same():
    amplitude = 1000
    alternating_pcm = _pcm_from_samples([amplitude, -amplitude] * 25)

    assert rms(alternating_pcm) == pytest.approx(float(amplitude))


def test_matches_a_manual_rms_calculation_for_mixed_amplitude_samples():
    samples = [100, -200, 300, -400]
    pcm = _pcm_from_samples(samples)
    expected_rms = (sum(sample * sample for sample in samples) / len(samples)) ** 0.5

    assert rms(pcm) == pytest.approx(expected_rms)


def test_ignores_a_trailing_odd_byte_instead_of_raising():
    single_sample = (500).to_bytes(2, "little", signed=True)
    pcm_with_truncated_trailing_sample = single_sample + b"\x01"

    assert rms(pcm_with_truncated_trailing_sample) == pytest.approx(500.0)


def test_a_single_odd_byte_with_no_full_sample_returns_zero():
    assert rms(b"\x01") == 0.0
