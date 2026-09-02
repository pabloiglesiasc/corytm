import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.runtime.session import materialize_project, move_clip_in_session

_SAMPLE_RATE = 44100.0


def _build_one_clip_project() -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=1.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id="move-clip-in-session-test", tracks=(track,))


@pytest.mark.transport
def test_moves_the_clip_and_renders_the_effect() -> None:
    project = _build_one_clip_project()

    with tempfile.TemporaryDirectory() as output_directory:
        new_project, clip_moved_event = asyncio.run(
            move_clip_in_session(
                project,
                track_id="track-1",
                clip_id="clip-1",
                new_start_seconds=1.5,
                output_directory=Path(output_directory),
            )
        )

        assert project.tracks[0].clips[0].start_seconds == 0.0

        assert new_project.tracks[0].clips[0].start_seconds == 1.5

        assert clip_moved_event.moved is True
        assert clip_moved_event.track_id == "track-1"
        assert clip_moved_event.clip_id == "clip-1"
        assert clip_moved_event.start_seconds == 1.5
        assert clip_moved_event.rendered_sample_count == pytest.approx(
            2.5 * _SAMPLE_RATE, abs=1
        )
        assert clip_moved_event.peak_amplitude > 0.5


@pytest.mark.transport
def test_a_caller_error_mid_session_does_not_deadlock_teardown() -> None:
    project = _build_one_clip_project()

    async def _scenario() -> None:
        with (
            tempfile.TemporaryDirectory() as output_directory,
            patch(
                "corytm.runtime.session.to_materialize_command",
                side_effect=RuntimeError("simulated caller failure"),
            ),
            pytest.raises(RuntimeError, match="simulated caller failure"),
        ):
            await materialize_project(project, Path(output_directory))

    asyncio.run(asyncio.wait_for(_scenario(), timeout=15))


def test_an_unknown_clip_id_is_rejected_before_any_native_process_is_spawned() -> None:
    project = _build_one_clip_project()

    with pytest.raises(ValueError, match="no clip"):
        asyncio.run(
            move_clip_in_session(
                project,
                track_id="track-1",
                clip_id="no-such-clip",
                new_start_seconds=1.5,
                output_directory=Path("/nonexistent-output-dir"),
            )
        )
