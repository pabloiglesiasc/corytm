import asyncio
import sys
from pathlib import Path

import pytest

from corytm.engine.clip import AudioClip
from corytm.engine.persistence import load_project, save_project
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.generated.project_pb2 import (
    AddAudioClipCommand,
    AddAudioTrackCommand,
    Command,
    CreateProjectCommand,
    Event,
    GetPlaybackPositionCommand,
    MoveClipCommand,
    OpenProjectCommand,
    PlayCommand,
    SaveProjectCommand,
    StopCommand,
)
from corytm.generated.project_pb2 import AudioClip as AudioClipMessage
from corytm.generated.project_pb2 import AudioTrack as AudioTrackMessage
from corytm.generated.project_pb2 import Project as ProjectMessage
from corytm.runtime.desktop import serve_desktop_channel
from corytm.runtime.transport import read_frame, write_frame

_SAMPLE_RATE = 44100.0


class _CapturingStdout:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self._buffer = ""

    def write(self, data: str) -> int:
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self.lines.append(line)
        return len(data)

    def flush(self) -> None:
        pass


class _FakeStdin:
    """Yields one `SHUTDOWN` line, standing in for the real sidecar stdin.

    Lets a Python-only test drive `serve_desktop_channel()` through its
    full lifecycle — including the post-session stdin wait — without
    touching the real process stdin, which pytest's own capture
    replaces with an object that raises on read.
    """

    def __iter__(self) -> _FakeStdin:
        return self

    def __next__(self) -> str:
        if self._yielded:
            raise StopIteration
        self._yielded = True
        return "SHUTDOWN\n"

    _yielded = False


async def _read_handshake(stdout: _CapturingStdout) -> tuple[int, str]:
    while True:
        for line in stdout.lines:
            if line.startswith("DESKTOP "):
                _, port_text, secret = line.split(" ")
                return int(port_text), secret
        await asyncio.sleep(0.01)


async def _exchange(
    writer: asyncio.StreamWriter, reader: asyncio.StreamReader, command: Command
) -> Event:
    write_frame(writer, command.SerializeToString())
    await writer.drain()

    event = Event()
    event.ParseFromString(await asyncio.wait_for(read_frame(reader), timeout=15))
    return event


def _build_fixture_project(project_id: str) -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id=project_id, tracks=(track,))


def test_create_and_save_project_over_one_connection(tmp_path: Path) -> None:
    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            assert created.WhichOneof("event") == "project_created"
            assert created.project_created.project_id

            save_path = tmp_path / "saved.corytm.json"
            saved = await _exchange(
                writer,
                reader,
                Command(
                    save_project=SaveProjectCommand(
                        schema_version=1, file_path=str(save_path)
                    )
                ),
            )
            assert saved.WhichOneof("event") == "project_saved"
            assert saved.project_saved.project_id == created.project_created.project_id
            assert saved.project_saved.file_path == str(save_path)

            reloaded = load_project(save_path)
            assert reloaded.id == created.project_created.project_id
            assert reloaded.tracks == ()

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=20))


@pytest.mark.transport
def test_open_project_re_materializes_it_and_move_clip_still_applies(
    tmp_path: Path,
) -> None:
    fixture_project = _build_fixture_project("open-project-test")
    fixture_path = tmp_path / "fixture.corytm.json"
    save_project(fixture_project, fixture_path)

    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            opened = await _exchange(
                writer,
                reader,
                Command(
                    open_project=OpenProjectCommand(
                        schema_version=1, file_path=str(fixture_path)
                    )
                ),
            )
            assert opened.WhichOneof("event") == "project_opened"
            assert opened.project_opened.project_id == "open-project-test"
            assert opened.project_opened.track_count == 1
            assert opened.project_opened.rendered_sample_count == pytest.approx(
                2.0 * _SAMPLE_RATE, abs=1
            )
            assert opened.project_opened.peak_amplitude > 0.5

            moved = await _exchange(
                writer,
                reader,
                Command(
                    move_clip=MoveClipCommand(
                        schema_version=1,
                        project_id="open-project-test",
                        track_id="track-1",
                        clip_id="clip-1",
                        new_start_seconds=1.0,
                    )
                ),
            )
            assert moved.WhichOneof("event") == "clip_moved"
            assert moved.clip_moved.moved is True
            assert moved.clip_moved.start_seconds == 1.0

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))


@pytest.mark.transport
def test_open_project_after_relaunch_with_no_tracks_succeeds(tmp_path: Path) -> None:
    """Reproduces the real New -> Save -> quit -> relaunch -> Open path.

    `test_create_and_save_project_over_one_connection` already proves
    create+save alone; this proves the specific combination it doesn't
    cover — opening a file that was saved from a `create_project`
    result (genuinely zero tracks) in a second, independent session,
    mirroring a real quit-and-relaunch rather than reusing one
    connection throughout.
    """
    save_path = tmp_path / "empty.corytm.json"

    async def _create_and_save() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            assert created.WhichOneof("event") == "project_created"

            saved = await _exchange(
                writer,
                reader,
                Command(
                    save_project=SaveProjectCommand(
                        schema_version=1, file_path=str(save_path)
                    )
                ),
            )
            assert saved.WhichOneof("event") == "project_saved"

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    async def _relaunch_and_open() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            opened = await _exchange(
                writer,
                reader,
                Command(
                    open_project=OpenProjectCommand(
                        schema_version=1, file_path=str(save_path)
                    )
                ),
            )
            assert opened.WhichOneof("event") == "project_opened"
            assert opened.project_opened.track_count == 0
            assert opened.project_opened.rendered_sample_count == 0
            assert opened.project_opened.peak_amplitude == 0.0

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_create_and_save(), timeout=20))
    asyncio.run(asyncio.wait_for(_relaunch_and_open(), timeout=20))


@pytest.mark.transport
def test_add_track_and_add_clip_author_real_content_and_render_it() -> None:
    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            assert created.WhichOneof("event") == "project_created"

            track_added = await _exchange(
                writer,
                reader,
                Command(add_track=AddAudioTrackCommand(schema_version=1)),
            )
            assert track_added.WhichOneof("event") == "track_added"
            assert track_added.track_added.track_count == 1
            track_id = track_added.track_added.track_id

            first_clip = await _exchange(
                writer,
                reader,
                Command(
                    add_clip=AddAudioClipCommand(
                        schema_version=1, track_id=track_id, duration_seconds=2.0
                    )
                ),
            )
            assert first_clip.WhichOneof("event") == "clip_added"
            assert first_clip.clip_added.start_seconds == 0.0
            assert first_clip.clip_added.rendered_sample_count == pytest.approx(
                2.0 * _SAMPLE_RATE, abs=1
            )
            assert first_clip.clip_added.peak_amplitude > 0.5

            second_clip = await _exchange(
                writer,
                reader,
                Command(
                    add_clip=AddAudioClipCommand(
                        schema_version=1, track_id=track_id, duration_seconds=1.0
                    )
                ),
            )
            assert second_clip.WhichOneof("event") == "clip_added"
            assert second_clip.clip_added.start_seconds == 2.0
            assert second_clip.clip_added.rendered_sample_count == pytest.approx(
                3.0 * _SAMPLE_RATE, abs=1
            )
            assert second_clip.clip_added.peak_amplitude > 0.5

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))


@pytest.mark.transport
def test_repeated_commands_with_idle_gaps_stay_reliable_over_one_connection() -> None:
    """Stress-tests the persistent session against lifecycle races.

    Repeats a real command many times, each separated by a short idle
    gap, over one held connection — the shape of a real interactive
    session (pauses between clicks), not a tight loop. Catches a
    resource leak or state-corruption race across many iterations that
    a single-command test could not, and — combined with a real,
    if modest, idle gap each time — guards against any reintroduced
    per-command read timeout as directly as the dedicated idle-gap
    test above, from a different angle (many small gaps, not one).

    Each `move_clip` re-spawns a whole `native_runtime` process
    (`materialize_then_move_clips`'s existing per-command shape, not
    changed by this test), so ten iterations pay ten real process
    spawns/device-manager inits/renders/teardowns, not ten cheap
    round trips. The outer bound accounts for that against real,
    measured cost (~25s locally) plus this project's own established
    margin for CI running slower than local hardware for
    native-adjacent work, not merely local dev timing — a real
    macOS Actions run once exceeded a tighter 60s bound here.
    """

    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            for iteration in range(10):
                await asyncio.sleep(0.1)
                moved = await _exchange(
                    writer,
                    reader,
                    Command(
                        move_clip=MoveClipCommand(
                            schema_version=1,
                            project_id="desktop-fixture",
                            track_id="track-1",
                            clip_id="clip-1",
                            new_start_seconds=float(iteration),
                        )
                    ),
                )
                assert moved.WhichOneof("event") == "clip_moved"
                assert moved.clip_moved.moved is True
                assert moved.clip_moved.start_seconds == float(iteration)
                assert moved.clip_moved.rendered_sample_count > 0
                assert moved.clip_moved.peak_amplitude > 0.0

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=180))


def test_session_survives_a_long_idle_gap_between_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproduces the real "leave the app open for a while" bug.

    `_run_session`'s command-read used to wrap `read_frame` in
    `asyncio.wait_for(..., timeout=_COMMAND_TIMEOUT_SECONDS)`, whose
    `TimeoutError` was never caught (only `IncompleteReadError` was) —
    it propagated uncaught through `serve_desktop_channel()`/`main()`,
    silently killing the whole `corytm serve` process on any real idle
    gap longer than that timeout, while the Rust side kept believing
    its connection was still live. The Desktop channel is designed to
    be genuinely persistent for the app's whole session (ADR-010), so
    an idle gap of any length must never end the session on its own —
    only the client actually disconnecting should.

    `raising=False` lets this same monkeypatch line keep exercising a
    real, fast reproduction of the exact bug before the fix (shrinking
    the real timeout from 30s to a fraction of a second) without
    erroring once the fix removes `_COMMAND_TIMEOUT_SECONDS` entirely
    — at that point the patch simply targets nothing.
    """
    monkeypatch.setattr(
        "corytm.runtime.desktop._COMMAND_TIMEOUT_SECONDS", 0.2, raising=False
    )

    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            await asyncio.sleep(0.5)
            assert not server_task.done(), (
                "the session must not exit merely from an idle gap"
            )

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            assert created.WhichOneof("event") == "project_created"

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=15))


@pytest.mark.transport
def test_move_clip_still_works_without_any_prior_command() -> None:
    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            moved = await _exchange(
                writer,
                reader,
                Command(
                    move_clip=MoveClipCommand(
                        schema_version=1,
                        project_id="desktop-fixture",
                        track_id="track-1",
                        clip_id="clip-1",
                        new_start_seconds=1.0,
                    )
                ),
            )
            assert moved.WhichOneof("event") == "clip_moved"
            assert moved.clip_moved.moved is True
            assert moved.clip_moved.start_seconds == 1.0
            assert moved.clip_moved.rendered_sample_count > 0
            assert moved.clip_moved.peak_amplitude > 0.0

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))


@pytest.mark.transport
def test_play_reports_advancing_position_and_stop_halts_it() -> None:
    """Drives the real Play -> GetPlaybackPosition -> Stop path.

    Unlike every other command this file exercises, Play spawns and
    holds its own dedicated `native_runtime` process across this whole
    sequence (`PlaybackSession`) rather than the one-shot
    spawn-per-command shape `move_clip`/`add_clip` use — this is the
    test proving that lifecycle actually works end to end, not just in
    isolation (TK-039's own native-level finding).

    Tolerates, rather than fails on, a test environment with no real
    audio output device (`device_opened=False`): CI runners commonly
    expose none (confirmed directly for Windows in TK-039/RSK-018), in
    which case position genuinely cannot advance and this test reports
    that rather than asserting on a codepath that never ran — mirroring
    `playback_proof`'s own soft-skip precedent.
    """

    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            project_id = created.project_created.project_id

            track_added = await _exchange(
                writer,
                reader,
                Command(add_track=AddAudioTrackCommand(schema_version=1)),
            )
            track_id = track_added.track_added.track_id

            clip_added = await _exchange(
                writer,
                reader,
                Command(
                    add_clip=AddAudioClipCommand(
                        schema_version=1, track_id=track_id, duration_seconds=3.0
                    )
                ),
            )

            project = ProjectMessage(
                schema_version=1,
                id=project_id,
                tracks=[
                    AudioTrackMessage(
                        schema_version=1,
                        id=track_id,
                        clips=[
                            AudioClipMessage(
                                schema_version=1,
                                id=clip_added.clip_added.clip_id,
                                start_seconds=clip_added.clip_added.start_seconds,
                                duration_seconds=clip_added.clip_added.duration_seconds,
                            )
                        ],
                    )
                ],
            )

            started = await _exchange(
                writer,
                reader,
                Command(play=PlayCommand(schema_version=1, project=project)),
            )
            assert started.WhichOneof("event") == "playback_started"

            if not started.playback_started.device_opened:
                writer.close()
                await writer.wait_closed()
                await asyncio.wait_for(server_task, timeout=5)
                pytest.skip("no real audio output device available in this environment")

            first_position = await _exchange(
                writer,
                reader,
                Command(
                    get_playback_position=GetPlaybackPositionCommand(schema_version=1)
                ),
            )
            assert first_position.WhichOneof("event") == "playback_position"
            assert first_position.playback_position.is_playing is True

            await asyncio.sleep(0.3)

            second_position = await _exchange(
                writer,
                reader,
                Command(
                    get_playback_position=GetPlaybackPositionCommand(schema_version=1)
                ),
            )
            assert second_position.playback_position.is_playing is True
            assert (
                second_position.playback_position.position_seconds
                > first_position.playback_position.position_seconds
            ), "expected playback position to genuinely advance"

            stopped = await _exchange(
                writer, reader, Command(stop=StopCommand(schema_version=1))
            )
            assert stopped.WhichOneof("event") == "playback_stopped"

            after_stop = await _exchange(
                writer,
                reader,
                Command(
                    get_playback_position=GetPlaybackPositionCommand(schema_version=1)
                ),
            )
            assert after_stop.playback_position.is_playing is False

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))


@pytest.mark.transport
def test_play_is_fast_once_the_device_is_warm() -> None:
    """Regression test for FT-030's human-validation latency defect.

    Human validation found click-to-audible/playhead latency of
    ~3-4s — diagnosed to a real, several-second macOS CoreMIDI cold-
    start cost inside `openRealtimeOutputDevice`, paid on every single
    Play because each one used to spawn a brand new `native_runtime`
    process. Fixed by spawning one playback process per Desktop-channel
    connection and eagerly warming its device (`PlaybackSession.open`,
    called by `_run_session` before the first command is even read)
    instead of on Play itself.

    This test sleeps well past that real warm-up cost (confirmed
    empirically to be under ~5.5s locally) before timing Play itself,
    mirroring real usage: a human takes several seconds clicking
    through New Project -> Add Track -> Add Clip before ever reaching
    Play, which is plenty of time for the background warm-up to finish
    invisibly. The bound asserted (1.5s) is deliberately looser than
    FT-030's own <500ms Alpha ceiling to absorb real CI/test-harness
    overhead (process scheduling, protobuf (de)serialization, socket
    round trips) while still failing hard against a real regression
    back to multi-second latency.
    """

    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            project_id = created.project_created.project_id

            track_added = await _exchange(
                writer,
                reader,
                Command(add_track=AddAudioTrackCommand(schema_version=1)),
            )
            track_id = track_added.track_added.track_id

            clip_added = await _exchange(
                writer,
                reader,
                Command(
                    add_clip=AddAudioClipCommand(
                        schema_version=1, track_id=track_id, duration_seconds=3.0
                    )
                ),
            )

            # Give the background device warm-up plenty of real time to
            # finish before timing Play itself — this is the whole point
            # of the fix: real usage always has this much slack.
            await asyncio.sleep(6.0)

            project = ProjectMessage(
                schema_version=1,
                id=project_id,
                tracks=[
                    AudioTrackMessage(
                        schema_version=1,
                        id=track_id,
                        clips=[
                            AudioClipMessage(
                                schema_version=1,
                                id=clip_added.clip_added.clip_id,
                                start_seconds=clip_added.clip_added.start_seconds,
                                duration_seconds=clip_added.clip_added.duration_seconds,
                            )
                        ],
                    )
                ],
            )

            play_start = asyncio.get_event_loop().time()
            started = await _exchange(
                writer,
                reader,
                Command(play=PlayCommand(schema_version=1, project=project)),
            )
            play_latency_seconds = asyncio.get_event_loop().time() - play_start

            await _exchange(writer, reader, Command(stop=StopCommand(schema_version=1)))

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)

            if not started.playback_started.device_opened:
                pytest.skip("no real audio output device available in this environment")

            assert play_latency_seconds < 1.5, (
                f"expected a warm Play to complete in well under 1.5s, took "
                f"{play_latency_seconds:.3f}s — the device-open cost may not "
                f"be getting paid ahead of Play any more"
            )
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))


@pytest.mark.transport
def test_playback_stops_automatically_at_the_effective_end() -> None:
    """Regression test for FT-030's human-validation auto-stop defect.

    Human validation found the playhead advancing indefinitely past the
    end of the project's content until the user manually pressed Stop.
    Confirmed empirically that Tracktion's own transport does not stop
    itself once an Edit's content ends (it keeps running, producing
    silence) — Corytm's Native Audio Runtime is the authoritative layer
    that now enforces this instead (`waitForNextCommand`'s poll loop,
    `native_runtime.cpp`), so `is_playing` itself becomes authoritative
    for every caller, including this test's own `GetPlaybackPosition`
    poll — no separate frontend timer is involved or needed.
    """

    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            project_id = created.project_created.project_id

            track_added = await _exchange(
                writer,
                reader,
                Command(add_track=AddAudioTrackCommand(schema_version=1)),
            )
            track_id = track_added.track_added.track_id

            clip_added = await _exchange(
                writer,
                reader,
                Command(
                    add_clip=AddAudioClipCommand(
                        schema_version=1, track_id=track_id, duration_seconds=0.5
                    )
                ),
            )

            project = ProjectMessage(
                schema_version=1,
                id=project_id,
                tracks=[
                    AudioTrackMessage(
                        schema_version=1,
                        id=track_id,
                        clips=[
                            AudioClipMessage(
                                schema_version=1,
                                id=clip_added.clip_added.clip_id,
                                start_seconds=clip_added.clip_added.start_seconds,
                                duration_seconds=clip_added.clip_added.duration_seconds,
                            )
                        ],
                    )
                ],
            )

            started = await _exchange(
                writer,
                reader,
                Command(play=PlayCommand(schema_version=1, project=project)),
            )

            if not started.playback_started.device_opened:
                writer.close()
                await writer.wait_closed()
                await asyncio.wait_for(server_task, timeout=5)
                pytest.skip("no real audio output device available in this environment")

            # Never send an explicit Stop -- only the effective-end
            # auto-stop should end this, well past the 0.5s clip.
            await asyncio.sleep(1.2)

            position = await _exchange(
                writer,
                reader,
                Command(
                    get_playback_position=GetPlaybackPositionCommand(schema_version=1)
                ),
            )
            assert position.playback_position.is_playing is False, (
                "expected playback to have auto-stopped at the effective end "
                "of the 0.5s clip without any explicit Stop"
            )

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))


@pytest.mark.transport
def test_stop_then_play_resumes_from_the_stopped_position() -> None:
    """Regression test for FT-030's human-validation stop/resume defect.

    Human validation found Stop followed by Play again restarting from
    0 rather than resuming from the stopped position. Confirmed
    empirically that Tracktion's own `stop()`/`freePlaybackContext()`
    never reset transport position at all — the real cause was that
    every Play used to spawn a brand new process and a brand new `Edit`
    (starting at 0 by construction). The fix keeps one process/session
    alive for the whole connection and has `native_runtime.cpp`'s own
    `Play` handling explicitly seek the freshly-rebuilt Edit back to the
    position the matching `Stop` captured.
    """

    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            project_id = created.project_created.project_id

            track_added = await _exchange(
                writer,
                reader,
                Command(add_track=AddAudioTrackCommand(schema_version=1)),
            )
            track_id = track_added.track_added.track_id

            clip_added = await _exchange(
                writer,
                reader,
                Command(
                    add_clip=AddAudioClipCommand(
                        schema_version=1, track_id=track_id, duration_seconds=3.0
                    )
                ),
            )

            project = ProjectMessage(
                schema_version=1,
                id=project_id,
                tracks=[
                    AudioTrackMessage(
                        schema_version=1,
                        id=track_id,
                        clips=[
                            AudioClipMessage(
                                schema_version=1,
                                id=clip_added.clip_added.clip_id,
                                start_seconds=clip_added.clip_added.start_seconds,
                                duration_seconds=clip_added.clip_added.duration_seconds,
                            )
                        ],
                    )
                ],
            )
            play_command = Command(play=PlayCommand(schema_version=1, project=project))

            first_started = await _exchange(writer, reader, play_command)

            if not first_started.playback_started.device_opened:
                writer.close()
                await writer.wait_closed()
                await asyncio.wait_for(server_task, timeout=5)
                pytest.skip("no real audio output device available in this environment")

            await asyncio.sleep(0.6)

            stopped = await _exchange(
                writer, reader, Command(stop=StopCommand(schema_version=1))
            )
            stopped_position = stopped.playback_stopped.final_position_seconds
            assert 0.3 < stopped_position < 2.5, (
                f"expected to stop somewhere mid-clip, got {stopped_position}"
            )

            resumed = await _exchange(writer, reader, play_command)
            assert resumed.playback_started.device_opened is True

            position_after_resume = await _exchange(
                writer,
                reader,
                Command(
                    get_playback_position=GetPlaybackPositionCommand(schema_version=1)
                ),
            )
            assert (
                position_after_resume.playback_position.position_seconds
                >= stopped_position - 0.1
            ), (
                f"expected resume near {stopped_position:.3f}s, got "
                f"{position_after_resume.playback_position.position_seconds:.3f}s "
                f"-- looks reset to 0 instead of resumed"
            )

            await _exchange(writer, reader, Command(stop=StopCommand(schema_version=1)))

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))
