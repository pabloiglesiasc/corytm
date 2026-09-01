"""Pure projection from Engine state to the wire command it materializes.

No I/O: converts an in-memory `Project` into the Protobuf message the
Native Audio Runtime consumes, per ADR-007's schema/transport split.
"""

from corytm.engine.project import Project
from corytm.generated.project_pb2 import AudioClip as AudioClipMessage
from corytm.generated.project_pb2 import AudioTrack as AudioTrackMessage
from corytm.generated.project_pb2 import MaterializeProjectCommand
from corytm.generated.project_pb2 import Project as ProjectMessage

SCHEMA_VERSION = 1


def to_materialize_command(project: Project) -> MaterializeProjectCommand:
    """Project a canonical `Project` into a `MaterializeProjectCommand`.

    Recursively converts the project and its tracks/clips into their
    wire-message equivalents, stamping every level with the current
    `SCHEMA_VERSION`.

    Args:
        project: The canonical Engine project to project.

    Returns:
        The equivalent `MaterializeProjectCommand`, ready to send over
        the ADR-007 transport.
    """
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
