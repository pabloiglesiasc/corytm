import pytest
from pydantic import ValidationError

from .clip import AudioClip
from .project import Project
from .track import AudioTrack


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
