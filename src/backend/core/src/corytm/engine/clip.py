"""Canonical audio clip, the leaf of the Engine timing model."""

from pydantic import BaseModel, ConfigDict, Field


class AudioClip(BaseModel):
    """A single audio region placed on a track's timeline.

    Timing only — no source-audio reference, gain, or fades yet. Frozen:
    edits produce a new `AudioClip`, never in-place mutation.

    Attributes:
        id: Stable identifier, unique within its owning `AudioTrack`.
        start_seconds: Position of the clip's start on the track's
            timeline, in seconds. Must be non-negative.
        duration_seconds: Length of the clip, in seconds. Must be
            strictly positive.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    start_seconds: float = Field(ge=0)
    duration_seconds: float = Field(gt=0)
