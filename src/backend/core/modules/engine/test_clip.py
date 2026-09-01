import pytest

from engine.clip import AudioClip


def test_constructs_with_valid_fields() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.5)

    assert clip.id == "clip-1"
    assert clip.start_seconds == 0.0
    assert clip.duration_seconds == 2.5


def test_rejects_negative_start() -> None:
    with pytest.raises(ValueError):
        AudioClip(id="clip-1", start_seconds=-1.0, duration_seconds=1.0)


def test_rejects_non_positive_duration() -> None:
    with pytest.raises(ValueError):
        AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=0.0)
