from pydantic import BaseModel, ConfigDict, Field


class AudioClip(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    start_seconds: float = Field(ge=0)
    duration_seconds: float = Field(gt=0)
