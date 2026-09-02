"""Canonical audio track: an ordered container of clips."""

from pydantic import BaseModel, ConfigDict

from .clip import AudioClip


class AudioTrack(BaseModel):
    """A single timeline lane holding zero or more audio clips.

    Frozen: edits produce a new `AudioTrack`, never in-place mutation.
    Clip overlap and ordering are not validated on construction or on
    `with_clip_moved` — only `with_clip_appended` guarantees its own
    new clip doesn't overlap this track's existing ones.

    Attributes:
        id: Stable identifier, unique within its owning `Project`.
        clips: The track's `AudioClip`s, in the order they render.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    clips: tuple[AudioClip, ...] = ()

    def with_clip_moved(self, *, clip_id: str, new_start_seconds: float) -> AudioTrack:
        """Return a new track with one clip's start time changed.

        The targeted clip is rebuilt through full construction (not a
        raw field copy) so `AudioClip`'s own validation — a start time
        must be non-negative — applies to the new value exactly as it
        would to any other construction.

        Args:
            clip_id: Id of the clip to move, within this track.
            new_start_seconds: The clip's new start position, in
                seconds.

        Returns:
            A new `AudioTrack` with the targeted clip moved; all other
            clips are unchanged.

        Raises:
            ValueError: No clip with `clip_id` exists on this track.
            pydantic.ValidationError: `new_start_seconds` is invalid.
        """
        updated_clips: list[AudioClip] = []
        found = False

        for clip in self.clips:
            if clip.id != clip_id:
                updated_clips.append(clip)
                continue

            updated_clips.append(
                AudioClip(
                    id=clip.id,
                    start_seconds=new_start_seconds,
                    duration_seconds=clip.duration_seconds,
                )
            )
            found = True

        if not found:
            raise ValueError(f"no clip with id {clip_id!r} in track {self.id!r}")

        return self.model_copy(update={"clips": tuple(updated_clips)})

    def with_clip_appended(
        self, *, clip_id: str, duration_seconds: float
    ) -> AudioTrack:
        """Return a new track with a clip appended after its existing clips.

        The new clip's start position is computed, not caller-supplied:
        immediately after the last existing clip ends, or at the
        timeline start if this track has none — placing authored
        clips without overlap by construction.

        Args:
            clip_id: Id for the new clip. Uniqueness is not validated
                here — the caller controls id generation.
            duration_seconds: Length of the new clip, in seconds.

        Returns:
            A new `AudioTrack` with the appended clip; existing clips
            are unchanged.

        Raises:
            pydantic.ValidationError: `duration_seconds` is invalid.
        """
        start_seconds = (
            0.0
            if not self.clips
            else max(clip.start_seconds + clip.duration_seconds for clip in self.clips)
        )
        new_clip = AudioClip(
            id=clip_id, start_seconds=start_seconds, duration_seconds=duration_seconds
        )
        return self.model_copy(update={"clips": (*self.clips, new_clip)})
