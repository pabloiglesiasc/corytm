from dataclasses import dataclass


@dataclass(frozen=True)
class AudioClip:
    id: str
    start_seconds: float
    duration_seconds: float

    def __post_init__(self) -> None:
        if self.start_seconds < 0:
            raise ValueError("start_seconds must be non-negative")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
