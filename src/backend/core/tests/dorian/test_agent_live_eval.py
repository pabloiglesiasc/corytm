"""Live acceptance evaluation for Dorian's Groq-hosted GPT-OSS proof (ADR-013).

Per this project's established pattern for evidence automation cannot
produce itself (for example EP-005's audible smoke test, EP-011/
EP-012's real-UI confirmation), this module requires a real
`GROQ_API_KEY` and live network access — automatically skipped
otherwise. Running it for real, with a real key, is FT-026's human
acceptance step: if GPT-OSS 20B (`DEFAULT_MODEL`) does not pass
reliably, ADR-013's approved fallback is to re-run against
`openai/gpt-oss-120b` instead, not to keep 20B by default regardless.
"""

import asyncio
import os

import pytest

from corytm.dorian.agent import propose_move_clip
from corytm.dorian.providers.groq import GroqProvider

pytestmark = pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="requires a real GROQ_API_KEY to call the live Groq API",
)


@pytest.mark.live_llm
def test_a_simple_move_instruction_produces_a_valid_proposal() -> None:
    provider = GroqProvider()

    proposal = asyncio.run(
        propose_move_clip(
            "Move the clip with id 'clip-1' on track 'track-1' so it starts at"
            " 4.5 seconds.",
            provider,
        )
    )

    assert proposal is not None
    assert proposal.track_id == "track-1"
    assert proposal.clip_id == "clip-1"
    assert proposal.new_start_seconds == pytest.approx(4.5)


@pytest.mark.live_llm
def test_a_differently_phrased_instruction_still_produces_a_valid_proposal() -> None:
    provider = GroqProvider()

    proposal = asyncio.run(
        propose_move_clip(
            "Please reposition clip clip-2 (it's on track track-9) to begin at"
            " 12 seconds.",
            provider,
        )
    )

    assert proposal is not None
    assert proposal.track_id == "track-9"
    assert proposal.clip_id == "clip-2"
    assert proposal.new_start_seconds == pytest.approx(12.0)
