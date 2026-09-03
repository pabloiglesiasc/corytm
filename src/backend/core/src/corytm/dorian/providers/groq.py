"""Groq-hosted model adapter for Dorian's `ModelProvider` boundary (ADR-013).

This is the only module in `corytm.dorian` permitted to depend on the
`groq` SDK or its request/response shapes — everything else depends
only on `providers.base`.
"""

import json
from collections.abc import Sequence

from groq import AsyncGroq
from groq.types.chat import ChatCompletionToolParam
from groq.types.shared_params import FunctionDefinition

from corytm.dorian.providers.base import ToolCall, ToolSpec

DEFAULT_MODEL = "openai/gpt-oss-20b"


class GroqProvider:
    """Dorian's `ModelProvider` boundary implemented against Groq.

    Per ADR-013, this is Alpha's only concrete `ModelProvider`: it
    calls Groq's OpenAI-compatible chat-completions tool-calling API
    and translates its response into a provider-neutral `ToolCall`.

    Attributes:
        model: The Groq-hosted model id to call (default
            `openai/gpt-oss-20b`; `openai/gpt-oss-120b` is ADR-013's
            approved fallback).
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        client: AsyncGroq | None = None,
    ) -> None:
        """Construct a provider bound to one Groq-hosted model.

        Args:
            api_key: Groq API key. When omitted, the `groq` SDK
                resolves it from the `GROQ_API_KEY` environment
                variable — never hardcoded or committed.
            model: The Groq-hosted model id to call.
            client: An already-constructed client to use instead of
                building one — the seam tests inject a fake client
                through, so no real network call is ever made in
                automated tests.
        """
        self._client = client if client is not None else AsyncGroq(api_key=api_key)
        self.model = model

    async def propose_tool_call(
        self, *, instruction: str, tools: Sequence[ToolSpec]
    ) -> ToolCall | None:
        """See `ModelProvider.propose_tool_call`."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": instruction}],
            tools=[_as_groq_tool(tool) for tool in tools],
            tool_choice="auto",
            temperature=0,
        )
        message = response.choices[0].message
        if not message.tool_calls:
            return None
        call = message.tool_calls[0]
        return ToolCall(
            tool_name=call.function.name,
            arguments=json.loads(call.function.arguments),
        )


def _as_groq_tool(tool: ToolSpec) -> ChatCompletionToolParam:
    function: FunctionDefinition = {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
    }
    return {"type": "function", "function": function}
