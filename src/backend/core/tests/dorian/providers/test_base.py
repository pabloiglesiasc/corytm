import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from corytm.dorian.providers.base import ToolCall, ToolSpec, tool_spec_from_model


class _ExampleProposal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    thing_id: str
    amount: float = Field(ge=0)


def test_tool_spec_from_model_carries_the_given_name_and_description() -> None:
    spec = tool_spec_from_model(
        name="do_thing", description="Do the thing.", model_cls=_ExampleProposal
    )

    assert spec.name == "do_thing"
    assert spec.description == "Do the thing."


def test_tool_spec_from_model_parameters_match_the_models_own_json_schema() -> None:
    spec = tool_spec_from_model(
        name="do_thing", description="Do the thing.", model_cls=_ExampleProposal
    )

    assert spec.parameters == _ExampleProposal.model_json_schema()


def test_a_tool_spec_is_frozen() -> None:
    spec = ToolSpec(name="do_thing", description="Do the thing.", parameters={})

    with pytest.raises(ValidationError):
        spec.name = "other"


def test_a_tool_call_carries_its_tool_name_and_raw_arguments() -> None:
    call = ToolCall(tool_name="do_thing", arguments={"thing_id": "t1", "amount": 2.0})

    assert call.tool_name == "do_thing"
    assert call.arguments == {"thing_id": "t1", "amount": 2.0}
