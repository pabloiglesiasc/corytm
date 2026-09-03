import pytest
from pydantic import ValidationError

from corytm.engine.clip import AudioClip
from corytm.engine.track import AudioTrack


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


def test_with_clip_moved_returns_a_new_track_with_updated_start() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))

    moved = track.with_clip_moved(clip_id="clip-1", new_start_seconds=5.0)

    assert moved is not track
    assert moved.clips[0].start_seconds == 5.0
    assert track.clips[0].start_seconds == 0.0


def test_with_clip_moved_rejects_an_unknown_clip() -> None:
    track = AudioTrack(id="track-1")

    with pytest.raises(ValueError, match="clip"):
        track.with_clip_moved(clip_id="missing", new_start_seconds=1.0)


def test_with_clip_moved_rejects_a_negative_start() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))

    with pytest.raises(ValidationError):
        track.with_clip_moved(clip_id="clip-1", new_start_seconds=-1.0)


def test_with_clip_appended_places_the_first_clip_at_the_start() -> None:
    track = AudioTrack(id="track-1")

    appended = track.with_clip_appended(clip_id="clip-1", duration_seconds=2.0)

    assert appended is not track
    assert track.clips == ()
    assert appended.clips == (
        AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0),
    )


def test_with_clip_appended_places_a_later_clip_after_existing_ones() -> None:
    first = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(first,))

    appended = track.with_clip_appended(clip_id="clip-2", duration_seconds=1.5)

    assert appended.clips == (
        first,
        AudioClip(id="clip-2", start_seconds=2.0, duration_seconds=1.5),
    )
    assert track.clips == (first,)


def test_with_clip_appended_rejects_a_non_positive_duration() -> None:
    track = AudioTrack(id="track-1")

    with pytest.raises(ValidationError):
        track.with_clip_appended(clip_id="clip-1", duration_seconds=0.0)
