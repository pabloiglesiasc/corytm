import pytest
from pydantic import ValidationError

from .clip import AudioClip
from .track import AudioTrack


def test_constructs_with_clips() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.5)
    track = AudioTrack(id="track-1", clips=(clip,))

    assert track.id == "track-1"
    assert track.clips == (clip,)


def test_defaults_to_no_clips() -> None:
    track = AudioTrack(id="track-1")

    assert track.clips == ()


def test_rejects_a_nested_clip_with_an_invalid_duration() -> None:
    with pytest.raises(ValidationError):
        AudioTrack.model_validate(
            {
                "id": "track-1",
                "clips": [
                    {"id": "clip-1", "start_seconds": 0.0, "duration_seconds": 0.0}
                ],
            }
        )
