from dataclasses import dataclass

from engine.clip import AudioClip


@dataclass(frozen=True)
class AudioTrack:
    id: str
    clips: tuple[AudioClip, ...] = ()
