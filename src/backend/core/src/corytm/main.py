"""Application entry point: the `corytm` console script.

Builds a minimal one-track/one-clip project, renders it through the
Native Audio Runtime via `corytm.runtime.session`, and reports the
result. `[project.scripts]` wires this module's `main` as the
installed `corytm` command.
"""

import asyncio
import sys
from pathlib import Path

from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.runtime.desktop import serve_desktop_channel
from corytm.runtime.session import materialize_project


def _build_first_sound_project() -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id="first-sound", tracks=(track,))


def main() -> None:
    """Render the fixture project, or serve the Desktop channel.

    With no arguments, writes the rendered WAV file into the current
    working directory. Given the single argument `serve`, instead runs
    as ADR-010's Desktop-facing sidecar until shutdown.
    """
    if sys.argv[1:] == ["serve"]:
        asyncio.run(serve_desktop_channel())
        return

    project = _build_first_sound_project()
    output_directory = Path.cwd()

    event = asyncio.run(materialize_project(project, output_directory))

    print(
        f"Rendered {event.rendered_sample_count} samples to {event.rendered_file_path}"
    )
    print(f"Peak amplitude: {event.peak_amplitude:.4f}")


if __name__ == "__main__":
    main()
