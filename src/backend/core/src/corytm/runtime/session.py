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
    build_dir = Path(__file__).resolve().parents[5] / "backend" / "audio" / "build"

    if platform.system() == "Windows":
        return build_dir / "Release" / "native_runtime.exe"

    return build_dir / "native_runtime"


async def materialize_project(
    project: Project, output_directory: Path
) -> ProjectRenderedEvent:
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
