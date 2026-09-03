import asyncio
import tempfile
from pathlib import Path

import pytest

from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.runtime.session import ClipMove, materialize_then_move_clips

_SAMPLE_RATE = 44100.0


def _build_one_clip_project() -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=1.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id="incremental-edit-test", tracks=(track,))


@pytest.mark.transport
def test_move_clip_is_reflected_in_a_subsequent_re_render_of_the_same_session() -> None:
    project = _build_one_clip_project()

    with tempfile.TemporaryDirectory() as output_directory:
        rendered_event, clip_moved_events = asyncio.run(
            materialize_then_move_clips(
                project,
                [ClipMove(track_id="track-1", clip_id="clip-1", new_start_seconds=1.5)],
                Path(output_directory),
            )
        )

        assert rendered_event.project_id == project.id
        assert rendered_event.rendered_sample_count == pytest.approx(
            1.0 * _SAMPLE_RATE, abs=1
        )
        assert rendered_event.peak_amplitude > 0.5

        assert len(clip_moved_events) == 1
        moved_event = clip_moved_events[0]

        assert moved_event.moved is True
        assert moved_event.project_id == project.id
        assert moved_event.track_id == "track-1"
        assert moved_event.clip_id == "clip-1"
        assert moved_event.start_seconds == 1.5
        assert moved_event.rendered_sample_count == pytest.approx(
            2.5 * _SAMPLE_RATE, abs=1
        )
        assert moved_event.peak_amplitude > 0.5
        assert Path(moved_event.rendered_file_path).exists()
        assert moved_event.rendered_file_path != rendered_event.rendered_file_path


@pytest.mark.transport
def test_a_move_with_an_unknown_clip_id_fails_without_ending_the_session() -> None:
    project = _build_one_clip_project()

    with tempfile.TemporaryDirectory() as output_directory:
        _, clip_moved_events = asyncio.run(
            materialize_then_move_clips(
                project,
                [
                    ClipMove(
                        track_id="track-1",
                        clip_id="no-such-clip",
                        new_start_seconds=1.5,
                    ),
                    ClipMove(
                        track_id="track-1", clip_id="clip-1", new_start_seconds=2.0
                    ),
                ],
                Path(output_directory),
            )
        )

        assert len(clip_moved_events) == 2

        failed_event, succeeded_event = clip_moved_events

        assert failed_event.moved is False
        assert failed_event.rendered_sample_count == 0
        assert failed_event.peak_amplitude == 0.0
        assert failed_event.rendered_file_path == ""

        assert succeeded_event.moved is True
        assert succeeded_event.start_seconds == 2.0
        assert succeeded_event.rendered_sample_count == pytest.approx(
            3.0 * _SAMPLE_RATE, abs=1
        )
        assert succeeded_event.peak_amplitude > 0.5
