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
