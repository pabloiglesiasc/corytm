"""Spawns and drives the Native Audio Runtime over one long-lived session.

Owns the process lifecycle and handshake for a `native_runtime` child
process: spawn it, exchange a per-launch secret over a loopback socket,
then send one or more `Command`-enveloped wire messages and read back
their `Event`-enveloped responses, all over the same connection.
"""

import asyncio
import platform
import secrets
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import NamedTuple

from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.generated.project_pb2 import (
    ClipMovedEvent,
    Command,
    Event,
    GetPlaybackPositionCommand,
    PlaybackPositionEvent,
    PlaybackStartedEvent,
    PlaybackStoppedEvent,
    PrepareDeviceCommand,
    ProjectRenderedEvent,
    StopCommand,
)

from .projection import to_materialize_command, to_move_clip_command, to_play_command
from .transport import read_frame, write_frame

_CONNECT_TIMEOUT_SECONDS = 5
_EVENT_TIMEOUT_SECONDS = 30


class ClipMove(NamedTuple):
    """One clip-move edit intention to send as a `MoveClipCommand`."""

    track_id: str
    clip_id: str
    new_start_seconds: float


def native_runtime_executable() -> Path:
    """Return the expected path to the built `native_runtime` binary.

    Returns:
        The platform-appropriate path under `src/backend/audio/build`;
        existence is not checked here.
    """
    build_dir = Path(__file__).resolve().parents[5] / "backend" / "audio" / "build"

    if platform.system() == "Windows":
        return build_dir / "Release" / "native_runtime.exe"

    return build_dir / "native_runtime"


class _NativeRuntimeProcess(NamedTuple):
    """One spawned, authenticated `native_runtime` process and its transport."""

    process: asyncio.subprocess.Process
    server: asyncio.AbstractServer
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter


async def _spawn_and_authenticate(output_directory: Path) -> _NativeRuntimeProcess:
    """Spawn `native_runtime` and complete its connection handshake.

    Shared by `_connected_native_runtime` (a one-shot session, closed by
    its caller before returning) and `PlaybackSession` (held open across
    multiple, separately-arriving Desktop-channel commands) — both need
    the identical spawn/listen/accept/authenticate sequence, only their
    teardown timing differs.

    Args:
        output_directory: Directory the native process should write its
            rendered output into.

    Returns:
        The spawned process, its listening server, and the connected,
        authenticated stream reader/writer pair.

    Raises:
        FileNotFoundError: `native_runtime_executable()` doesn't exist —
            the native build hasn't been run.
        RuntimeError: The spawned process failed to authenticate.
        TimeoutError: The connection or handshake wasn't completed
            within the configured timeout.
    """
    executable = native_runtime_executable()

    if not executable.exists():
        raise FileNotFoundError(f"native_runtime executable not found at {executable}")

    secret = secrets.token_hex(16)
    loop = asyncio.get_running_loop()
    connection_future: asyncio.Future[
        tuple[asyncio.StreamReader, asyncio.StreamWriter]
    ] = loop.create_future()

    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        connection_future.set_result((reader, writer))

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    assert server.sockets is not None
    port = server.sockets[0].getsockname()[1]

    process = await asyncio.create_subprocess_exec(
        str(executable), str(port), secret, str(output_directory)
    )

    reader, writer = await asyncio.wait_for(
        connection_future, timeout=_CONNECT_TIMEOUT_SECONDS
    )

    received_secret = await asyncio.wait_for(
        read_frame(reader), timeout=_CONNECT_TIMEOUT_SECONDS
    )
    if received_secret.decode("utf-8") != secret:
        raise RuntimeError("native_runtime failed to authenticate")

    return _NativeRuntimeProcess(process, server, reader, writer)


@asynccontextmanager
async def _connected_native_runtime(
    output_directory: Path,
) -> AsyncGenerator[tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
    """Spawn `native_runtime`, connect, and authenticate over the transport.

    Yields a `(reader, writer)` pair for the caller to drive an arbitrary
    sequence of commands/events over. On exit, closes the writer and
    waits for the child process to exit, always tearing down the process
    and listening socket, including on error.

    `native_runtime`'s own process exit code reflects whether every
    command in the session rendered non-silent output, not merely
    whether it ran correctly — a project with no tracks legitimately
    renders nothing and exits non-zero, even though the `Event` already
    sent for that command faithfully reports it (zero sample count,
    zero peak amplitude). That is real, already-delivered information,
    not a process failure, so this context manager never raises on
    exit code alone: a caller that successfully read every `Event` it
    expected already knows the outcome; only a genuine transport
    failure (the process never authenticating, an event never
    arriving) is reported as an error here.

    Args:
        output_directory: Directory the native process should write its
            rendered output into.

    Yields:
        The connected, authenticated stream reader/writer pair.

    Raises:
        FileNotFoundError: `native_runtime_executable()` doesn't exist —
            the native build hasn't been run.
        RuntimeError: The spawned process failed to authenticate.
        TimeoutError: The connection or handshake wasn't completed
            within the configured timeout, or the process didn't exit
            promptly once its connection closed.
    """
    process, server, reader, writer_ = await _spawn_and_authenticate(output_directory)

    writer: asyncio.StreamWriter | None = writer_
    try:
        yield reader, writer_

        writer_.close()
        await writer_.wait_closed()
        writer = None

        await asyncio.wait_for(process.wait(), timeout=_EVENT_TIMEOUT_SECONDS)
    finally:
        # `Server.wait_closed()` (Python 3.12.1+) waits for the listening
        # socket to close *and* for every accepted connection to drop.
        # Closing our own end here first, on every exit path, is what
        # actually lets that second condition become true — without it,
        # a caller-side failure between `yield` and the success path's
        # own `writer.close()` leaves this writer open and `wait_closed()`
        # blocks forever on a connection nothing will ever close.
        if writer is not None:
            writer.close()
            await writer.wait_closed()

        if process.returncode is None:
            process.kill()
            await process.wait()

        server.close()
        await server.wait_closed()


class PlaybackSession:
    """Holds one live `native_runtime` playback process for a whole
    Desktop-channel connection, across many Play/Stop cycles.

    Unlike every other Desktop-channel command — each spawns a fresh
    `native_runtime` process for exactly one command/response, via
    `_connected_native_runtime` — real-time playback needs the same
    open audio device to persist across Play, any number of position
    polls, and Stop, and across repeated Play/Stop pairs, so that:
    (1) the real audio-device open/settle cost (measured empirically at
    several real seconds, dominated by the host OS's own first-touch
    MIDI-client cold start rather than anything Corytm controls) is
    paid once per connection via `open()`, ideally well before the user
    ever clicks Play, rather than on every single click; and (2) Stop
    followed by Play again resumes from the stopped position rather
    than restarting, since `native_runtime`'s own resume logic (see
    `native_runtime.cpp`'s `PlaySpec` handling) only has a stopped
    position to resume from when it is the same long-lived process
    that was told to stop. This class is the owner of that
    connection-lifetime process.
    """

    def __init__(self, native_process: _NativeRuntimeProcess) -> None:
        self._native_process = native_process

    @staticmethod
    async def spawn(output_directory: Path) -> PlaybackSession:
        """Spawn `native_runtime` and authenticate — fast, no device-open.

        Deliberately split from `prepare_device()` (the slow part): a
        caller needs this to complete quickly and unconditionally so it
        always has a real process handle to `kill()` if the Desktop-
        channel connection closes before `prepare_device()`'s own,
        much longer, device-open/settle wait finishes.

        Args:
            output_directory: Directory passed to the spawned process;
                unused by the playback command path itself (it never
                renders to a file), so its lifetime need not outlive
                this call.

        Returns:
            The live session, with its device not yet opened.

        Raises:
            FileNotFoundError, RuntimeError, TimeoutError: propagated
                unchanged from `_spawn_and_authenticate`.
        """
        native_process = await _spawn_and_authenticate(output_directory)
        return PlaybackSession(native_process)

    async def prepare_device(self) -> bool:
        """Eagerly open the real audio device, before any Play arrives.

        This is the slow part — measured empirically at several real
        seconds, dominated by the host OS's own first-touch MIDI-client
        cold start rather than anything Corytm controls — so callers
        run it as a backgrounded task right after `spawn()`, ideally
        finishing well before the user ever clicks Play, rather than
        blocking on it directly.

        Returns:
            Whether a real audio device was genuinely opened (a real
            "no device in this environment" condition is not an error
            — `play()` retries opening it regardless).
        """
        await _send_command(
            self._native_process.writer,
            Command(prepare_device=PrepareDeviceCommand(schema_version=1)),
        )
        event = await _read_event(self._native_process.reader)
        return event.device_prepared.device_opened

    async def play(self, project: Project) -> PlaybackStartedEvent:
        """Start real-time playback of `project` on this live session.

        Args:
            project: The canonical project to play.

        Returns:
            The `PlaybackStartedEvent` describing whether a real audio
            device is open.
        """
        await _send_command(
            self._native_process.writer, Command(play=to_play_command(project))
        )
        event = await _read_event(self._native_process.reader)
        return event.playback_started

    async def get_position(self) -> PlaybackPositionEvent:
        """Query this session's current live playback position.

        Returns:
            The `PlaybackPositionEvent` describing whether playback is
            still active and its current position.
        """
        await _send_command(
            self._native_process.writer,
            Command(get_playback_position=GetPlaybackPositionCommand(schema_version=1)),
        )
        event = await _read_event(self._native_process.reader)
        return event.playback_position

    async def stop(self) -> PlaybackStoppedEvent:
        """Stop this session's live playback, keeping the process alive.

        Unlike an earlier design, this does not tear the process down —
        a live device stays open and ready so the next `play()` call is
        cheap, and so a `play()` for the same project resumes from the
        position this call captures rather than restarting at 0.

        Returns:
            The `PlaybackStoppedEvent` describing the final position
            playback stopped at.
        """
        await _send_command(
            self._native_process.writer, Command(stop=StopCommand(schema_version=1))
        )
        event = await _read_event(self._native_process.reader)
        return event.playback_stopped

    async def kill(self) -> None:
        """Forcibly tear down this session's process.

        Used when the owning Desktop-channel connection itself closes —
        this session lives for the connection's whole lifetime, so this
        is its only teardown path (there is no per-Play spawn/close
        cycle to piggyback on any more).
        """
        if self._native_process.process.returncode is None:
            self._native_process.process.kill()

        self._native_process.writer.close()
        await self._native_process.writer.wait_closed()

        if self._native_process.process.returncode is None:
            await asyncio.wait_for(
                self._native_process.process.wait(), timeout=_EVENT_TIMEOUT_SECONDS
            )

        self._native_process.server.close()
        await self._native_process.server.wait_closed()


async def _send_command(writer: asyncio.StreamWriter, command: Command) -> None:
    write_frame(writer, command.SerializeToString())
    await writer.drain()


async def _read_event(reader: asyncio.StreamReader) -> Event:
    event_bytes = await asyncio.wait_for(
        read_frame(reader), timeout=_EVENT_TIMEOUT_SECONDS
    )
    event = Event()
    event.ParseFromString(event_bytes)
    return event


async def materialize_project(
    project: Project, output_directory: Path
) -> ProjectRenderedEvent:
    """Render `project` by spawning and driving the Native Audio Runtime.

    Sends `project` as a `MaterializeProjectCommand` over one connection
    and returns the `ProjectRenderedEvent` it renders and sends back.

    Args:
        project: The canonical project to materialize.
        output_directory: Directory the native process should write its
            rendered output into.

    Returns:
        The `ProjectRenderedEvent` describing the render outcome.

    Raises:
        FileNotFoundError: `native_runtime_executable()` doesn't exist —
            the native build hasn't been run.
        RuntimeError: The spawned process failed to authenticate.
        TimeoutError: The connection, handshake, or event wasn't
            received within the configured timeout.
    """
    async with _connected_native_runtime(output_directory) as (reader, writer):
        await _send_command(
            writer, Command(materialize=to_materialize_command(project))
        )
        event = await _read_event(reader)

    return event.project_rendered


async def move_clip_in_session(
    project: Project,
    *,
    track_id: str,
    clip_id: str,
    new_start_seconds: float,
    output_directory: Path,
) -> tuple[Project, ClipMovedEvent]:
    """Apply one clip move to `project`'s canonical state and live session.

    Combines Corytm Engine's own `with_clip_moved` canonical-state
    update with a materialize-then-move round trip against the Native
    Audio Runtime, so both halves of an edit happen together. This is
    the one shared execution path behind both `corytm.dorian.tools`'
    `move_clip` (ADR-004) and the Desktop channel's move-clip command
    (ADR-010) — `corytm.runtime` never depends on `corytm.dorian`, so
    this lives here rather than being called through Dorian's module.

    Args:
        project: The canonical project to edit.
        track_id: Id of the track owning the clip to move.
        clip_id: Id of the clip to move, within that track.
        new_start_seconds: The clip's new start position, in seconds.
        output_directory: Directory the native process should write
            its rendered output into.

    Returns:
        The new canonical `Project` with the clip moved, and the
        `ClipMovedEvent` describing the edit's effect on the
        re-rendered sound.

    Raises:
        ValueError: `track_id`/`clip_id` don't exist on `project` —
            raised by Engine's own `with_clip_moved` before any native
            process is spawned.
        FileNotFoundError, RuntimeError, TimeoutError: propagated
            unchanged from `materialize_then_move_clips`.
    """
    new_project = project.with_clip_moved(
        track_id=track_id, clip_id=clip_id, new_start_seconds=new_start_seconds
    )

    _, clip_moved_events = await materialize_then_move_clips(
        project,
        [
            ClipMove(
                track_id=track_id, clip_id=clip_id, new_start_seconds=new_start_seconds
            )
        ],
        output_directory,
    )

    return new_project, clip_moved_events[0]


async def add_clip_in_session(
    project: Project,
    *,
    track_id: str,
    clip_id: str,
    duration_seconds: float,
    output_directory: Path,
) -> tuple[Project, AudioClip, ProjectRenderedEvent]:
    """Append a new clip to a track and re-render the resulting project.

    Combines Corytm Engine's own `with_clip_appended` canonical-state
    update with a full re-materialize of the resulting project — a new
    clip has no live-session incremental counterpart the way moving an
    existing one does (`move_clip_in_session`), so the whole project is
    simply re-sent, exactly as `open_project` already does.

    Args:
        project: The canonical project to edit.
        track_id: Id of the track to append the clip to.
        clip_id: Id for the new clip. Uniqueness is not validated here
            — the caller controls id generation.
        duration_seconds: Length of the new clip, in seconds.
        output_directory: Directory the native process should write
            its rendered output into.

    Returns:
        The new canonical `Project` with the clip appended, that same
        clip (to read back its computed start position), and the
        `ProjectRenderedEvent` describing the re-rendered sound.

    Raises:
        ValueError: `track_id` doesn't exist on `project` — raised by
            Engine's own `with_clip_appended` before any native
            process is spawned.
        FileNotFoundError, RuntimeError, TimeoutError: propagated
            unchanged from `materialize_project`.
    """
    new_project = project.with_clip_appended(
        track_id=track_id, clip_id=clip_id, duration_seconds=duration_seconds
    )
    new_track = next(track for track in new_project.tracks if track.id == track_id)
    new_clip = new_track.clips[-1]

    rendered_event = await materialize_project(new_project, output_directory)

    return new_project, new_clip, rendered_event


async def materialize_then_move_clips(
    project: Project, moves: Sequence[ClipMove], output_directory: Path
) -> tuple[ProjectRenderedEvent, list[ClipMovedEvent]]:
    """Materialize `project`, then apply `moves` to that same live session.

    Sends one `MaterializeProjectCommand` followed by one
    `MoveClipCommand` per entry in `moves`, in order, all over the same
    `native_runtime` connection — proving each move is applied to the
    still-live `Edit` the materialize command built, not a fresh
    rebuild. A move with an unknown track/clip id comes back with
    `moved = False` rather than ending the session, so later entries in
    `moves` can still succeed.

    Args:
        project: The canonical project to materialize.
        moves: Clip moves to apply, in order, to the materialized
            project's live session.
        output_directory: Directory the native process should write its
            rendered output into.

    Returns:
        The baseline `ProjectRenderedEvent`, and one `ClipMovedEvent`
        per entry in `moves`, in the same order.

    Raises:
        FileNotFoundError: `native_runtime_executable()` doesn't exist —
            the native build hasn't been run.
        RuntimeError: The spawned process failed to authenticate.
        TimeoutError: The connection, handshake, or an event wasn't
            received within the configured timeout.
    """
    async with _connected_native_runtime(output_directory) as (reader, writer):
        await _send_command(
            writer, Command(materialize=to_materialize_command(project))
        )
        rendered_event = (await _read_event(reader)).project_rendered

        clip_moved_events: list[ClipMovedEvent] = []

        for move in moves:
            await _send_command(
                writer,
                Command(
                    move_clip=to_move_clip_command(
                        project_id=project.id,
                        track_id=move.track_id,
                        clip_id=move.clip_id,
                        new_start_seconds=move.new_start_seconds,
                    )
                ),
            )
            clip_moved_events.append((await _read_event(reader)).clip_moved)

    return rendered_event, clip_moved_events
