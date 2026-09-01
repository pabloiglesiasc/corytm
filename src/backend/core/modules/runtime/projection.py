from engine.project import Project
from project_pb2 import AudioClip as AudioClipMessage
from project_pb2 import AudioTrack as AudioTrackMessage
from project_pb2 import MaterializeProjectCommand
from project_pb2 import Project as ProjectMessage

SCHEMA_VERSION = 1


def to_materialize_command(project: Project) -> MaterializeProjectCommand:
    return MaterializeProjectCommand(
        schema_version=SCHEMA_VERSION,
        project=ProjectMessage(
            schema_version=SCHEMA_VERSION,
            id=project.id,
            tracks=[
                AudioTrackMessage(
                    schema_version=SCHEMA_VERSION,
                    id=track.id,
                    clips=[
                        AudioClipMessage(
                            schema_version=SCHEMA_VERSION,
                            id=clip.id,
                            start_seconds=clip.start_seconds,
                            duration_seconds=clip.duration_seconds,
                        )
                        for clip in track.clips
                    ],
                )
                for track in project.tracks
            ],
        ),
    )
