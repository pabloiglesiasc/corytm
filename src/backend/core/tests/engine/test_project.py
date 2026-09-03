import pytest
from pydantic import ValidationError

from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack


def test_constructs_with_tracks() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.5)
    track = AudioTrack(id="track-1", clips=(clip,))
    project = Project(id="project-1", tracks=(track,))

    assert project.id == "project-1"
    assert project.tracks == (track,)


def test_defaults_to_no_tracks() -> None:
    project = Project(id="project-1")

    assert project.tracks == ()


def test_with_clip_moved_returns_a_new_project_with_updated_start() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    project = Project(id="project-1", tracks=(track,))

    moved = project.with_clip_moved(
        track_id="track-1", clip_id="clip-1", new_start_seconds=5.0
    )

    assert moved is not project
    assert moved.tracks[0].clips[0].start_seconds == 5.0
    assert project.tracks[0].clips[0].start_seconds == 0.0


def test_with_clip_moved_rejects_an_unknown_track() -> None:
    project = Project(id="project-1")

    with pytest.raises(ValueError, match="track"):
        project.with_clip_moved(
            track_id="missing", clip_id="clip-1", new_start_seconds=1.0
        )


def test_with_clip_moved_rejects_a_deeply_nested_negative_start() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    project = Project(id="project-1", tracks=(track,))

    with pytest.raises(ValidationError):
        project.with_clip_moved(
            track_id="track-1", clip_id="clip-1", new_start_seconds=-1.0
        )


def test_with_track_added_appends_an_empty_track() -> None:
    project = Project(id="project-1")

    added = project.with_track_added(track_id="track-1")

    assert added is not project
    assert project.tracks == ()
    assert added.tracks == (AudioTrack(id="track-1"),)


def test_with_track_added_preserves_existing_tracks() -> None:
    existing = AudioTrack(id="track-1")
    project = Project(id="project-1", tracks=(existing,))

    added = project.with_track_added(track_id="track-2")

    assert added.tracks == (existing, AudioTrack(id="track-2"))


def test_with_clip_appended_appends_to_the_named_track() -> None:
    track = AudioTrack(id="track-1")
    project = Project(id="project-1", tracks=(track,))

    appended = project.with_clip_appended(
        track_id="track-1", clip_id="clip-1", duration_seconds=2.0
    )

    assert appended.tracks[0].clips == (
        AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0),
    )
    assert project.tracks[0].clips == ()


def test_with_clip_appended_rejects_an_unknown_track() -> None:
    project = Project(id="project-1")

    with pytest.raises(ValueError, match="track"):
        project.with_clip_appended(
            track_id="missing", clip_id="clip-1", duration_seconds=2.0
        )


def test_rejects_a_deeply_nested_clip_with_a_negative_start() -> None:
    with pytest.raises(ValidationError):
        Project.model_validate(
            {
                "id": "project-1",
                "tracks": [
                    {
                        "id": "track-1",
                        "clips": [
                            {
                                "id": "clip-1",
                                "start_seconds": -1.0,
                                "duration_seconds": 1.0,
                            }
                        ],
                    }
                ],
            }
        )
