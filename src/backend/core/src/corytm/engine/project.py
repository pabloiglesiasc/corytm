from pydantic import BaseModel, ConfigDict

from .track import AudioTrack


class Project(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    tracks: tuple[AudioTrack, ...] = ()
