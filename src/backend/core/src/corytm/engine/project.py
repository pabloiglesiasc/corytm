"""Canonical project: the Engine's root aggregate."""

from pydantic import BaseModel, ConfigDict

from .track import AudioTrack


class Project(BaseModel):
    """A complete Corytm project: an ordered collection of tracks.

    The Engine's source-of-truth root — everything the Native Audio
    Runtime renders is a projection of a `Project`, never the reverse.
    Frozen: edits produce a new `Project`, never in-place mutation.

    Attributes:
        id: Stable identifier for this project.
        tracks: The project's `AudioTrack`s, in the order they render.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    tracks: tuple[AudioTrack, ...] = ()
