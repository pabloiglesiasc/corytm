"""Pure projection from Engine state to the wire command it materializes.

No I/O: converts an in-memory `Project` into the Protobuf message the
Native Audio Runtime consumes, per ADR-007's schema/transport split.
"""

from corytm.engine.project import Project
from corytm.generated.project_pb2 import AudioClip as AudioClipMessage
from corytm.generated.project_pb2 import AudioTrack as AudioTrackMessage
from corytm.generated.project_pb2 import (
    MaterializeProjectCommand,
    MoveClipCommand,
    PlayCommand,
)
from corytm.generated.project_pb2 import Project as ProjectMessage

SCHEMA_VERSION = 1


def _to_project_message(project: Project) -> ProjectMessage:
    """Recursively convert a canonical `Project` into its wire message.

    Args:
        project: The canonical Engine project to convert.

    Returns:
        The equivalent `ProjectMessage`, with every level stamped with
        the current `SCHEMA_VERSION`.
    """
    return ProjectMessage(
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
    )


def to_materialize_command(project: Project) -> MaterializeProjectCommand:
    """Project a canonical `Project` into a `MaterializeProjectCommand`.

    Args:
        project: The canonical Engine project to project.

    Returns:
        The equivalent `MaterializeProjectCommand`, ready to send over
        the ADR-007 transport.
    """
    return MaterializeProjectCommand(
        schema_version=SCHEMA_VERSION, project=_to_project_message(project)
    )


def to_play_command(project: Project) -> PlayCommand:
    """Project a canonical `Project` into a `PlayCommand`.

    Unlike `to_materialize_command`, the resulting Edit is built for
    real-time device playback rather than offline rendering — see
    `native_runtime.cpp`'s `PlaySpec` handling.

    Args:
        project: The canonical Engine project to play.

    Returns:
        The equivalent `PlayCommand`, ready to send over the ADR-007
        transport.
    """
    return PlayCommand(
        schema_version=SCHEMA_VERSION, project=_to_project_message(project)
    )


def to_move_clip_command(
    *, project_id: str, track_id: str, clip_id: str, new_start_seconds: float
) -> MoveClipCommand:
    """Project a clip-move edit intention into a `MoveClipCommand`.

    Pure: describes the edit's intention as a wire command, independent
    of whether the Native Audio Runtime already has this project loaded
    — it is not a projection of a `Project`'s full state.

    Args:
        project_id: Id of the project owning the clip.
        track_id: Id of the track owning the clip, within that
            project.
        clip_id: Id of the clip to move, within that track.
        new_start_seconds: The clip's new start position, in seconds.

    Returns:
        The equivalent `MoveClipCommand`, ready to send over the
        ADR-007 transport.
    """
    return MoveClipCommand(
        schema_version=SCHEMA_VERSION,
        project_id=project_id,
        track_id=track_id,
        clip_id=clip_id,
        new_start_seconds=new_start_seconds,
    )
