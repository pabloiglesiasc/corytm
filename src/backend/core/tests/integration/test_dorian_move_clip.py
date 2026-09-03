import asyncio
import tempfile
from pathlib import Path

import pytest

from corytm.dorian.tools import MoveClipProposal, move_clip
from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack

_SAMPLE_RATE = 44100.0


def _build_one_clip_project() -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=1.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id="dorian-move-clip-test", tracks=(track,))


@pytest.mark.transport
def test_a_valid_proposal_moves_the_clip_and_renders_the_effect() -> None:
    project = _build_one_clip_project()
    proposal = MoveClipProposal(
        track_id="track-1", clip_id="clip-1", new_start_seconds=1.5
    )

    with tempfile.TemporaryDirectory() as output_directory:
        new_project, clip_moved_event = asyncio.run(
            move_clip(project, proposal, Path(output_directory))
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


def test_an_unknown_clip_id_is_rejected_before_any_native_process_is_spawned() -> None:
    project = _build_one_clip_project()
    proposal = MoveClipProposal(
        track_id="track-1", clip_id="no-such-clip", new_start_seconds=1.5
    )

    with pytest.raises(ValueError, match="no clip"):
        asyncio.run(move_clip(project, proposal, Path("/nonexistent-output-dir")))
