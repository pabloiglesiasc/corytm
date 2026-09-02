import asyncio
import tempfile
from pathlib import Path

import pytest

from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.runtime.session import materialize_project


@pytest.mark.transport
def test_first_sound_round_trip() -> None:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    project = Project(id="first-sound-test", tracks=(track,))

    with tempfile.TemporaryDirectory() as output_directory:
        event = asyncio.run(materialize_project(project, Path(output_directory)))

        assert event.project_id == project.id
        assert event.rendered_sample_count == pytest.approx(2.0 * 44100, abs=1)
        assert event.peak_amplitude > 0.5
        assert Path(event.rendered_file_path).exists()


@pytest.mark.transport
def test_materialize_project_with_no_tracks_returns_a_zero_render_event() -> None:
    project = Project(id="empty-project-test", tracks=())

    with tempfile.TemporaryDirectory() as output_directory:
        event = asyncio.run(materialize_project(project, Path(output_directory)))

        assert event.project_id == project.id
        assert event.rendered_sample_count == 0
        assert event.peak_amplitude == 0.0
