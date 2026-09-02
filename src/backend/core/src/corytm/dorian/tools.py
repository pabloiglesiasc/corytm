"""Dorian's semantic tools: trusted capabilities Dorian may call.

Per ADR-004, a tool's input model is the validation boundary between a
model's untrusted proposed action and Corytm Engine/the Native Audio
Runtime: a proposal that fails validation is rejected before any
Engine or native code runs. A tool's function is the only path through
which the corresponding proposal is authorized and executed — it goes
through the same Engine/Runtime capabilities a human-driven UI action
would use, never a direct native or Tracktion call.
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from corytm.engine.project import Project
from corytm.generated.project_pb2 import ClipMovedEvent
from corytm.runtime.session import ClipMove, materialize_then_move_clips


class MoveClipProposal(BaseModel):
    """A model-proposed move-clip edit, as untrusted tool-call arguments.

    Attributes:
        track_id: Id of the track owning the clip to move.
        clip_id: Id of the clip to move, within that track.
        new_start_seconds: The clip's proposed new start position, in
            seconds. Must be non-negative.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    track_id: str
    clip_id: str
    new_start_seconds: float = Field(ge=0)


async def move_clip(
    project: Project, proposal: MoveClipProposal, output_directory: Path
) -> tuple[Project, ClipMovedEvent]:
    """Authorize and execute a validated move-clip proposal.

    This is Dorian's only sanctioned path to move a clip (ADR-004):
    `proposal` must already be a validated `MoveClipProposal`, not raw
    model output. Execution goes through Corytm Engine's own
    `with_clip_moved` operation — the same canonical-state update a
    human-driven edit would produce — and then through EP-006's live
    native session, so the move's effect on the re-rendered sound is
    observable the same way a human-driven edit's would be.

    Args:
        project: The canonical project to edit.
        proposal: The validated move-clip proposal to authorize and
            apply.
        output_directory: Directory the native process should write
            its rendered output into.

    Returns:
        The new canonical `Project` with the clip moved, and the
        `ClipMovedEvent` describing the edit's effect on the
        re-rendered sound.

    Raises:
        ValueError: `proposal` names a track or clip that doesn't
            exist on `project` — raised by Engine's own
            `with_clip_moved` before any native process is spawned.
        FileNotFoundError, RuntimeError, TimeoutError: propagated
            unchanged from `materialize_then_move_clips`.
    """
    new_project = project.with_clip_moved(
        track_id=proposal.track_id,
        clip_id=proposal.clip_id,
        new_start_seconds=proposal.new_start_seconds,
    )

    _, clip_moved_events = await materialize_then_move_clips(
        project,
        [
            ClipMove(
                track_id=proposal.track_id,
                clip_id=proposal.clip_id,
                new_start_seconds=proposal.new_start_seconds,
            )
        ],
        output_directory,
    )

    return new_project, clip_moved_events[0]
