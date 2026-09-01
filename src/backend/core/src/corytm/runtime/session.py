"""Spawns and drives the Native Audio Runtime for one materialization.

Owns the process lifecycle and handshake for a single request/response
round trip: spawn `native_runtime`, exchange a per-launch secret over a
loopback socket, send a `MaterializeProjectCommand`, and return the
`ProjectRenderedEvent` it responds with.
"""

import asyncio
import platform
import secrets
from pathlib import Path

from corytm.engine.project import Project
from corytm.generated.project_pb2 import ProjectRenderedEvent

from .projection import to_materialize_command
from .transport import read_frame, write_frame

_CONNECT_TIMEOUT_SECONDS = 5
_EVENT_TIMEOUT_SECONDS = 30


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


async def materialize_project(
    project: Project, output_directory: Path
) -> ProjectRenderedEvent:
    """Render `project` by spawning and driving the Native Audio Runtime.

    Spawns `native_runtime` as a child process, listens on an ephemeral
    loopback port, authenticates it with a per-call secret, sends
    `project` as a `MaterializeProjectCommand`, and waits for the
    `ProjectRenderedEvent` it renders and sends back. The child process
    and its listening socket are always torn down before returning,
    including on error.

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

    try:
        reader, writer = await asyncio.wait_for(
            connection_future, timeout=_CONNECT_TIMEOUT_SECONDS
        )

        received_secret = await asyncio.wait_for(
            read_frame(reader), timeout=_CONNECT_TIMEOUT_SECONDS
        )
        if received_secret.decode("utf-8") != secret:
            raise RuntimeError("native_runtime failed to authenticate")

        command = to_materialize_command(project)
        write_frame(writer, command.SerializeToString())
        await writer.drain()

        event_bytes = await asyncio.wait_for(
            read_frame(reader), timeout=_EVENT_TIMEOUT_SECONDS
        )
        event = ProjectRenderedEvent()
        event.ParseFromString(event_bytes)

        writer.close()
        await writer.wait_closed()

        return_code = await asyncio.wait_for(
            process.wait(), timeout=_EVENT_TIMEOUT_SECONDS
        )
        if return_code != 0:
            raise RuntimeError(f"native_runtime exited with code {return_code}")

        return event
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()

        server.close()
        await server.wait_closed()
