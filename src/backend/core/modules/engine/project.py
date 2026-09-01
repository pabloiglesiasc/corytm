from dataclasses import dataclass

from engine.track import AudioTrack


@dataclass(frozen=True)
class Project:
    id: str
    tracks: tuple[AudioTrack, ...] = ()
