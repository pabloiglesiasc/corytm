import pytest
from pydantic import ValidationError

from corytm.dorian.tools import MoveClipProposal


def test_a_valid_proposal_constructs() -> None:
    proposal = MoveClipProposal.model_validate(
        {"track_id": "track-1", "clip_id": "clip-1", "new_start_seconds": 1.5}
    )

    assert proposal.track_id == "track-1"
    assert proposal.clip_id == "clip-1"
    assert proposal.new_start_seconds == 1.5


def test_a_proposal_missing_a_required_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MoveClipProposal.model_validate({"track_id": "track-1", "clip_id": "clip-1"})


def test_a_proposal_with_a_negative_start_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MoveClipProposal.model_validate(
            {"track_id": "track-1", "clip_id": "clip-1", "new_start_seconds": -1.0}
        )


def test_a_proposal_with_an_unexpected_extra_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MoveClipProposal.model_validate(
            {
                "track_id": "track-1",
                "clip_id": "clip-1",
                "new_start_seconds": 1.5,
                "delete_project": True,
            }
        )
