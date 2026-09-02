"""Serves ADR-010's second, Desktop-facing loopback transport.

Implements the Python-core half of the Desktop↔Python command channel:
a second `asyncio` listener, independent of whatever port/secret this
process later uses to spawn and authenticate the Native Audio Runtime
(ADR-007), whose port and per-launch secret are handed to Rust over the
existing sidecar stdout lifecycle channel. Carries a real `MoveClipCommand`
against an in-memory fixture project, reusing `project.proto`'s message
types by reference per ADR-010 rather than a new Desktop-owned envelope.
"""

import asyncio
import secrets
import sys
import tempfile
from pathlib import Path

from corytm.engine.clip import AudioClip
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.generated.project_pb2 import MoveClipCommand

from .session import move_clip_in_session
from .transport import read_frame, write_frame

_AUTHENTICATION_TIMEOUT_SECONDS = 5
_COMMAND_TIMEOUT_SECONDS = 30


def _build_desktop_fixture_project() -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id="desktop-fixture", tracks=(track,))


async def serve_desktop_channel() -> None:
    """Run the Desktop channel server until shutdown.

    Prints `READY` followed by a `DESKTOP <port> <secret>` line over
    stdout, accepts exactly one authenticated client connection,
    applies its one `MoveClipCommand` to a hardcoded in-memory fixture
    project (Corytm Engine's `with_clip_moved` plus EP-006's live
    native session, via `move_clip_in_session`), returns the resulting
    `ClipMovedEvent`, then blocks reading stdin lines until `SHUTDOWN`
    before returning — mirroring `sidecar_proof.py`'s existing
    lifecycle protocol with one additional handshake line.

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

    try:
        reader, writer = await asyncio.wait_for(
            connection_future, timeout=_AUTHENTICATION_TIMEOUT_SECONDS
        )

        received_secret = await asyncio.wait_for(
            read_frame(reader), timeout=_AUTHENTICATION_TIMEOUT_SECONDS
        )
        if received_secret.decode("utf-8") != secret:
            raise RuntimeError("desktop channel client failed to authenticate")

        command_bytes = await asyncio.wait_for(
            read_frame(reader), timeout=_COMMAND_TIMEOUT_SECONDS
        )
        command = MoveClipCommand()
        command.ParseFromString(command_bytes)

        project = _build_desktop_fixture_project()
        with tempfile.TemporaryDirectory() as output_directory:
            _, clip_moved_event = await move_clip_in_session(
                project,
                track_id=command.track_id,
                clip_id=command.clip_id,
                new_start_seconds=command.new_start_seconds,
                output_directory=Path(output_directory),
            )

        write_frame(writer, clip_moved_event.SerializeToString())
        await writer.drain()

        writer.close()
        await writer.wait_closed()
    finally:
        server.close()
        await server.wait_closed()

    for line in sys.stdin:
        if line.strip() == "SHUTDOWN":
            break
