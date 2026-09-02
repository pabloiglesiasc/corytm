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

from corytm.engine.project import Project
from corytm.generated.project_pb2 import (
    ClipMovedEvent,
    Command,
    Event,
    ProjectRenderedEvent,
)

from .projection import to_materialize_command, to_move_clip_command
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


@asynccontextmanager
async def _connected_native_runtime(
    output_directory: Path,
) -> AsyncGenerator[tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
    """Spawn `native_runtime`, connect, and authenticate over the transport.

    Yields a `(reader, writer)` pair for the caller to drive an arbitrary
    sequence of commands/events over. On exit, closes the writer and
    waits for the child process to exit, always tearing down the process
    and listening socket, including on error.

    Args:
        output_directory: Directory the native process should write its
            rendered output into.

    Yields:
        The connected, authenticated stream reader/writer pair.

    Raises:
        FileNotFoundError: `native_runtime_executable()` doesn't exist —
            the native build hasn't been run.
        RuntimeError: The spawned process failed to authenticate, or
            exited with a non-zero return code.
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

    writer: asyncio.StreamWriter | None = None
    try:
        reader, writer = await asyncio.wait_for(
            connection_future, timeout=_CONNECT_TIMEOUT_SECONDS
        )

        received_secret = await asyncio.wait_for(
            read_frame(reader), timeout=_CONNECT_TIMEOUT_SECONDS
        )
        if received_secret.decode("utf-8") != secret:
            raise RuntimeError("native_runtime failed to authenticate")

        yield reader, writer

        writer.close()
        await writer.wait_closed()
        writer = None

        return_code = await asyncio.wait_for(
            process.wait(), timeout=_EVENT_TIMEOUT_SECONDS
        )
        if return_code != 0:
            raise RuntimeError(f"native_runtime exited with code {return_code}")
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
        RuntimeError: The spawned process failed to authenticate, or
            exited with a non-zero return code.
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
        RuntimeError: The spawned process failed to authenticate, or
            exited with a non-zero return code.
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
