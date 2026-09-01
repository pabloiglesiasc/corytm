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

    def with_clip_moved(
        self, *, track_id: str, clip_id: str, new_start_seconds: float
    ) -> Project:
        """Return a new project with one clip's start time changed.

        Delegates the actual clip update to the targeted `AudioTrack`,
        which enforces `AudioClip`'s own validation on the new value.

        Args:
            track_id: Id of the track owning the clip, within this
                project.
            clip_id: Id of the clip to move, within that track.
            new_start_seconds: The clip's new start position, in
                seconds.

        Returns:
            A new `Project` with the targeted clip moved; all other
            tracks and clips are unchanged.

        Raises:
            ValueError: No track with `track_id` exists on this
                project, or no clip with `clip_id` exists on that
                track.
            pydantic.ValidationError: `new_start_seconds` is invalid.
        """
        updated_tracks: list[AudioTrack] = []
        found = False

        for track in self.tracks:
            if track.id != track_id:
                updated_tracks.append(track)
                continue

            updated_tracks.append(
                track.with_clip_moved(
                    clip_id=clip_id, new_start_seconds=new_start_seconds
                )
            )
            found = True

        if not found:
            raise ValueError(f"no track with id {track_id!r} in project {self.id!r}")

        return self.model_copy(update={"tracks": tuple(updated_tracks)})
