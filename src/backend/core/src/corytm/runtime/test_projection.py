from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack

from .projection import SCHEMA_VERSION, to_materialize_command


def test_projects_an_empty_project() -> None:
    project = Project(id="project-1")

    command = to_materialize_command(project)

    assert command.schema_version == SCHEMA_VERSION
    assert command.project.schema_version == SCHEMA_VERSION
    assert command.project.id == "project-1"
    assert list(command.project.tracks) == []


def test_projects_tracks_and_clips_in_order() -> None:
    clip_a = AudioClip(id="clip-a", start_seconds=0.0, duration_seconds=1.5)
    clip_b = AudioClip(id="clip-b", start_seconds=1.5, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip_a, clip_b))
    project = Project(id="project-1", tracks=(track,))

    command = to_materialize_command(project)

    assert len(command.project.tracks) == 1
    track_message = command.project.tracks[0]
    assert track_message.schema_version == SCHEMA_VERSION
    assert track_message.id == "track-1"
    assert len(track_message.clips) == 2

    first_clip_message = track_message.clips[0]
    assert first_clip_message.schema_version == SCHEMA_VERSION
    assert first_clip_message.id == "clip-a"
    assert first_clip_message.start_seconds == 0.0
    assert first_clip_message.duration_seconds == 1.5

    second_clip_message = track_message.clips[1]
    assert second_clip_message.id == "clip-b"
    assert second_clip_message.start_seconds == 1.5
    assert second_clip_message.duration_seconds == 2.0
