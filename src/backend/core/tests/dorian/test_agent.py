import asyncio
from collections.abc import Sequence

import pytest
from pydantic import ValidationError

from corytm.dorian.agent import propose_move_clip
from corytm.dorian.providers.base import ToolCall, ToolSpec
from corytm.dorian.tools import MoveClipProposal


class _FakeProvider:
    def __init__(self, result: ToolCall | None) -> None:
        self._result = result
        self.last_tools: Sequence[ToolSpec] | None = None

    async def propose_tool_call(
        self, *, instruction: str, tools: Sequence[ToolSpec]
    ) -> ToolCall | None:
        self.last_tools = tools
        return self._result


def _propose(provider: _FakeProvider) -> MoveClipProposal | None:
    return asyncio.run(propose_move_clip("move it", provider))


def test_a_valid_move_clip_call_is_validated_into_a_proposal() -> None:
    provider = _FakeProvider(
        ToolCall(
            tool_name="move_clip",
            arguments={"track_id": "t1", "clip_id": "c1", "new_start_seconds": 4.5},
        )
    )

    proposal = _propose(provider)

    assert proposal is not None
    assert proposal.track_id == "t1"
    assert proposal.clip_id == "c1"
    assert proposal.new_start_seconds == 4.5
    assert provider.last_tools is not None
    assert [tool.name for tool in provider.last_tools] == ["move_clip"]


def test_no_tool_call_yields_none() -> None:
    provider = _FakeProvider(None)

    assert _propose(provider) is None


def test_a_call_naming_a_different_tool_yields_none() -> None:
    provider = _FakeProvider(ToolCall(tool_name="delete_project", arguments={}))

    assert _propose(provider) is None


def test_invalid_arguments_raise_validation_error() -> None:
    provider = _FakeProvider(
        ToolCall(tool_name="move_clip", arguments={"track_id": "t1"})
    )

    with pytest.raises(ValidationError):
        _propose(provider)
