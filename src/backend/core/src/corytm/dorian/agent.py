"""Orchestrates a live model call through Dorian's move_clip tool (ADR-013).

Builds `move_clip`'s tool schema from its own existing
`corytm.dorian.tools.MoveClipProposal`, calls a configured
`ModelProvider`, and validates the raw response through that same
model — reusing ADR-004's validate-then-execute boundary unchanged.
This module never authorizes or executes an edit itself; a validated
proposal it returns must still be passed to
`corytm.dorian.tools.move_clip`, exactly as a hand-constructed one
would be.
"""

from corytm.dorian.providers.base import ModelProvider, ToolSpec, tool_spec_from_model
from corytm.dorian.tools import MoveClipProposal

MOVE_CLIP_TOOL_SPEC: ToolSpec = tool_spec_from_model(
    name="move_clip",
    description="Move an existing clip on a track to a new start position, in seconds.",
    model_cls=MoveClipProposal,
)


async def propose_move_clip(
    instruction: str, provider: ModelProvider
) -> MoveClipProposal | None:
    """Ask a model to propose a move-clip edit from a natural-language instruction.

    Args:
        instruction: The natural-language edit request to interpret.
        provider: The `ModelProvider` to ask.

    Returns:
        A validated `MoveClipProposal`, or `None` if the model chose
        not to invoke `move_clip` (no tool call, or a different tool
        name).

    Raises:
        pydantic.ValidationError: The model invoked `move_clip` but
            its arguments don't satisfy `MoveClipProposal` — rejected
            before reaching Corytm Engine or the Native Audio Runtime,
            per ADR-004.
    """
    call = await provider.propose_tool_call(
        instruction=instruction, tools=[MOVE_CLIP_TOOL_SPEC]
    )
    if call is None or call.tool_name != MOVE_CLIP_TOOL_SPEC.name:
        return None
    return MoveClipProposal.model_validate(call.arguments)
