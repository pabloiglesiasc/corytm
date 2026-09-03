import asyncio
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

from groq import AsyncGroq

from corytm.dorian.providers.base import ToolSpec
from corytm.dorian.providers.groq import GroqProvider

_A_TOOL = ToolSpec(
    name="move_clip", description="Move a clip.", parameters={"type": "object"}
)


def _fake_response(tool_calls: list[SimpleNamespace] | None) -> Any:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=tool_calls))]
    )


def _fake_client(create: AsyncMock) -> Any:
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )


def test_a_tool_call_response_is_decoded_into_a_tool_call() -> None:
    tool_call = SimpleNamespace(
        function=SimpleNamespace(
            name="move_clip", arguments='{"track_id": "t1", "clip_id": "c1"}'
        )
    )
    create = AsyncMock(return_value=_fake_response([tool_call]))
    provider = GroqProvider(client=cast(AsyncGroq, _fake_client(create)))

    result = asyncio.run(
        provider.propose_tool_call(instruction="move it", tools=[_A_TOOL])
    )

    assert result is not None
    assert result.tool_name == "move_clip"
    assert result.arguments == {"track_id": "t1", "clip_id": "c1"}


def test_a_response_with_no_tool_call_yields_none() -> None:
    create = AsyncMock(return_value=_fake_response(None))
    provider = GroqProvider(client=cast(AsyncGroq, _fake_client(create)))

    result = asyncio.run(
        provider.propose_tool_call(instruction="do nothing relevant", tools=[_A_TOOL])
    )

    assert result is None


def test_propose_tool_call_sends_the_instruction_and_translated_tools() -> None:
    create = AsyncMock(return_value=_fake_response(None))
    provider = GroqProvider(
        client=cast(AsyncGroq, _fake_client(create)), model="a-model"
    )

    asyncio.run(provider.propose_tool_call(instruction="move it", tools=[_A_TOOL]))

    _, kwargs = create.call_args
    assert kwargs["model"] == "a-model"
    assert kwargs["messages"] == [{"role": "user", "content": "move it"}]
    assert kwargs["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "move_clip",
                "description": "Move a clip.",
                "parameters": {"type": "object"},
            },
        }
    ]
