from engine.clip import AudioClip
from engine.project import Project
from engine.track import AudioTrack


def test_constructs_with_tracks() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.5)
    track = AudioTrack(id="track-1", clips=(clip,))
    project = Project(id="project-1", tracks=(track,))

    assert project.id == "project-1"
    assert project.tracks == (track,)


def test_defaults_to_no_tracks() -> None:
    project = Project(id="project-1")

    assert project.tracks == ()
