"""Serves ADR-010's second, Desktop-facing loopback transport.

Implements the Python-core half of the Desktop↔Python command channel:
a second `asyncio` listener, independent of whatever port/secret this
process later uses to spawn and authenticate the Native Audio Runtime
(ADR-007), whose port and per-launch secret are handed to Rust over the
existing sidecar stdout lifecycle channel. Accepts one authenticated
client connection and dispatches a sequence of `project.proto`
`Command`-enveloped commands against one in-memory "current project"
slot — `CreateProjectCommand`/`SaveProjectCommand`/`OpenProjectCommand`
(backed by ADR-011's `corytm.engine.persistence` module) and the
pre-existing `MoveClipCommand` — mirroring the multi-command session
loop `native_runtime.cpp` already implements (FT-017/TK-018), reusing
`project.proto`'s message types by reference per ADR-010 rather than a
new Desktop-owned envelope.
"""

import asyncio
import secrets
import sys
import tempfile
import uuid
from pathlib import Path

from corytm.engine.clip import AudioClip
from corytm.engine.persistence import load_project, save_project
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.generated.project_pb2 import (
    Command,
    Event,
    ProjectCreatedEvent,
    ProjectOpenedEvent,
    ProjectSavedEvent,
)

from .session import materialize_project, move_clip_in_session
from .transport import read_frame, write_frame

_AUTHENTICATION_TIMEOUT_SECONDS = 5
_COMMAND_TIMEOUT_SECONDS = 30
_SCHEMA_VERSION = 1


def _build_desktop_fixture_project() -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id="desktop-fixture", tracks=(track,))


async def _dispatch_command(
    command: Command, current_project: Project, output_directory: Path
) -> tuple[Event, Project]:
    """Apply one `Command` against `current_project` and return its `Event`.

    Args:
        command: The received, already-decoded command.
        current_project: The session's project so far — `_run_session`
            always seeds this with the hardcoded fixture, so a
            connection that only ever sends `MoveClipCommand` behaves
            exactly as before this dispatcher existed.
        output_directory: Directory the native process should write
            its rendered output into, for any command that renders.

    Returns:
        The resulting `Event`, and the project to carry forward as
        `current_project` for the next command in this session.

    Raises:
        ValueError: `command` names an unknown track/clip, or carries
            no recognized command.
        FileNotFoundError, RuntimeError, TimeoutError: propagated
            unchanged from the Runtime/native calls a command makes.
    """
    which = command.WhichOneof("command")

    if which == "create_project":
        new_project = Project(id=str(uuid.uuid4()), tracks=())
        return (
            Event(
                project_created=ProjectCreatedEvent(
                    schema_version=_SCHEMA_VERSION, project_id=new_project.id
                )
            ),
            new_project,
        )

    if which == "save_project":
        file_path = command.save_project.file_path
        save_project(current_project, Path(file_path))
        return (
            Event(
                project_saved=ProjectSavedEvent(
                    schema_version=_SCHEMA_VERSION,
                    project_id=current_project.id,
                    file_path=file_path,
                )
            ),
            current_project,
        )

    if which == "open_project":
        file_path = command.open_project.file_path
        loaded_project = load_project(Path(file_path))
        rendered_event = await materialize_project(loaded_project, output_directory)
        return (
            Event(
                project_opened=ProjectOpenedEvent(
                    schema_version=_SCHEMA_VERSION,
                    project_id=loaded_project.id,
                    file_path=file_path,
                    track_count=len(loaded_project.tracks),
                    rendered_sample_count=rendered_event.rendered_sample_count,
                    peak_amplitude=rendered_event.peak_amplitude,
                )
            ),
            loaded_project,
        )

    if which == "move_clip":
        move = command.move_clip
        new_project, clip_moved_event = await move_clip_in_session(
            current_project,
            track_id=move.track_id,
            clip_id=move.clip_id,
            new_start_seconds=move.new_start_seconds,
            output_directory=output_directory,
        )
        return Event(clip_moved=clip_moved_event), new_project

    raise ValueError(f"unsupported Desktop channel command: {which!r}")


async def _run_session(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    """Dispatch `Command` frames from `reader` until the client disconnects.

    Holds one in-memory "current project" slot across the whole
    connection, seeded with the existing hardcoded fixture so a
    connection that only ever sends `MoveClipCommand` behaves exactly
    as before this session loop existed.

    Args:
        reader: The authenticated client connection to read commands
            from.
        writer: The same connection, to write each command's `Event`
            back to.
    """
    current_project: Project = _build_desktop_fixture_project()

    while True:
        try:
            command_bytes = await asyncio.wait_for(
                read_frame(reader), timeout=_COMMAND_TIMEOUT_SECONDS
            )
        except asyncio.IncompleteReadError:
            return

        command = Command()
        command.ParseFromString(command_bytes)

        with tempfile.TemporaryDirectory() as output_directory:
            event, current_project = await _dispatch_command(
                command, current_project, Path(output_directory)
            )

        write_frame(writer, event.SerializeToString())
        await writer.drain()


async def serve_desktop_channel() -> None:
    """Run the Desktop channel server until shutdown.

    Prints `READY` followed by a `DESKTOP <port> <secret>` line over
    stdout, accepts exactly one authenticated client connection, then
    dispatches its sequence of `Command`-enveloped commands (see
    `_run_session`) until that connection closes, then blocks reading
    stdin lines until `SHUTDOWN` before returning — mirroring
    `sidecar_proof.py`'s existing lifecycle protocol with one
    additional handshake line.

    Raises:
        RuntimeError: The connecting client's first frame didn't match
            the printed secret.
    """
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

    print("READY", flush=True)
    print(f"DESKTOP {port} {secret}", flush=True)

    writer: asyncio.StreamWriter | None = None
    try:
        reader, writer = await asyncio.wait_for(
            connection_future, timeout=_AUTHENTICATION_TIMEOUT_SECONDS
        )

        received_secret = await asyncio.wait_for(
            read_frame(reader), timeout=_AUTHENTICATION_TIMEOUT_SECONDS
        )
        if received_secret.decode("utf-8") != secret:
            raise RuntimeError("desktop channel client failed to authenticate")

        await _run_session(reader, writer)

        writer.close()
        await writer.wait_closed()
        writer = None
    finally:
        # `Server.wait_closed()` (Python 3.12.1+) waits for the listening
        # socket to close *and* for the one accepted connection to drop.
        # Closing our own end here first, on every exit path, is what
        # actually lets that second condition become true — without it,
        # a command-handler failure between accepting the connection and
        # the success path's own `writer.close()` leaves this writer
        # open, and `wait_closed()` blocks forever on a connection the
        # client is itself only ever waiting to read a response from.
        if writer is not None:
            writer.close()
            await writer.wait_closed()

        server.close()
        await server.wait_closed()

    for line in sys.stdin:
        if line.strip() == "SHUTDOWN":
            break
