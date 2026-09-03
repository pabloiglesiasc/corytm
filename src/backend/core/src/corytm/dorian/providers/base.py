"""Dorian's provider-neutral tool-call boundary (ADR-013).

`ToolSpec`/`ToolCall` describe a tool call in terms no specific
provider's SDK defines, and `ModelProvider` is the interface every
concrete adapter implements. `corytm.dorian.agent` depends only on
these — never on a provider's own request/response shape.
"""

from collections.abc import Sequence
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict


class ToolSpec(BaseModel):
    """A tool's provider-neutral definition, offered to a model.

    Attributes:
        name: The tool's identifier, matching the `ToolCall.tool_name`
            a provider returns when it invokes this tool.
        description: Guides a model's decision to invoke this tool.
        parameters: The tool's arguments, as a JSON Schema object —
            typically a tool's own Pydantic model's
            `model_json_schema()`, so a tool's provider-facing shape
            can never drift from its trusted validation model.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    parameters: dict[str, Any]


class ToolCall(BaseModel):
    """A model's provider-neutral proposed tool invocation.

    Attributes:
        tool_name: Which offered `ToolSpec.name` the model selected.
        arguments: The model's raw, untrusted proposed arguments —
            not yet validated against the tool's own input model.
    """

    model_config = ConfigDict(frozen=True)

    tool_name: str
    arguments: dict[str, Any]


class ModelProvider(Protocol):
    """Dorian's boundary to any concrete model/provider adapter.

    Per ADR-013, `corytm.dorian.agent` depends only on this protocol,
    never on a specific provider's SDK or response shape — a second
    provider is a second implementation of this one method, nothing
    else changes.
    """

    async def propose_tool_call(
        self, *, instruction: str, tools: Sequence[ToolSpec]
    ) -> ToolCall | None:
        """Ask the model to select and fill in at most one offered tool.

        Args:
            instruction: The natural-language edit request to
                interpret.
            tools: The tools the model may choose to invoke.

        Returns:
            A `ToolCall` naming the tool the model selected and its
            raw, untrusted arguments, or `None` if the model chose not
            to invoke any tool.
        """
        ...


def tool_spec_from_model(
    *, name: str, description: str, model_cls: type[BaseModel]
) -> ToolSpec:
    """Build a `ToolSpec` from an existing tool's own proposal model.

    Reuses a tool's own Pydantic input model (for example
    `corytm.dorian.tools.MoveClipProposal`) as the offered schema, so
    a tool's provider-facing shape and its trusted validation boundary
    (ADR-004) can never drift apart.

    Args:
        name: The tool's identifier.
        description: Guides a model's decision to invoke this tool.
        model_cls: The tool's own proposal model, whose
            `model_json_schema()` becomes `ToolSpec.parameters`.

    Returns:
        The resulting `ToolSpec`.
    """
    return ToolSpec(
        name=name, description=description, parameters=model_cls.model_json_schema()
    )
