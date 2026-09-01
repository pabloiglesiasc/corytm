import asyncio
from pathlib import Path

from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.runtime.session import materialize_project


def _build_first_sound_project() -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id="first-sound", tracks=(track,))


def main() -> None:
    project = _build_first_sound_project()
    output_directory = Path.cwd()

    event = asyncio.run(materialize_project(project, output_directory))

    print(
        f"Rendered {event.rendered_sample_count} samples to {event.rendered_file_path}"
    )
    print(f"Peak amplitude: {event.peak_amplitude:.4f}")


if __name__ == "__main__":
    main()
