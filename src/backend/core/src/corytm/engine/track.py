from pydantic import BaseModel, ConfigDict

from .clip import AudioClip


class AudioTrack(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    clips: tuple[AudioClip, ...] = ()
