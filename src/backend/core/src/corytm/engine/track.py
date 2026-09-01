"""Canonical audio track: an ordered container of clips."""

from pydantic import BaseModel, ConfigDict

from .clip import AudioClip


class AudioTrack(BaseModel):
    """A single timeline lane holding zero or more audio clips.

    Frozen: edits produce a new `AudioTrack`, never in-place mutation.
    Clip overlap and ordering are not validated here — the Engine has no
    editing behavior yet beyond construction.

    Attributes:
        id: Stable identifier, unique within its owning `Project`.
        clips: The track's `AudioClip`s, in the order they render.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    clips: tuple[AudioClip, ...] = ()
