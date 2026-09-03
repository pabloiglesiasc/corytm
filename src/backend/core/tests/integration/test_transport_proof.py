import asyncio
import platform
import secrets
from pathlib import Path

import pytest

from corytm.generated.proof_pb2 import ProofMessage
from corytm.runtime.transport import read_frame, write_frame


def _transport_proof_executable() -> Path:
    build_dir = Path(__file__).resolve().parents[4] / "backend" / "audio" / "build"

    if platform.system() == "Windows":
        return build_dir / "Release" / "transport_proof.exe"

    return build_dir / "transport_proof"


async def _round_trip() -> None:
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

    executable = _transport_proof_executable()
    assert executable.exists(), f"transport_proof executable not found at {executable}"

    process = await asyncio.create_subprocess_exec(str(executable), str(port), secret)

    try:
        reader, writer = await asyncio.wait_for(connection_future, timeout=5)

        received_secret = await asyncio.wait_for(read_frame(reader), timeout=5)
        assert received_secret.decode("utf-8") == secret

        command = ProofMessage(
            schema_version=1, payload="corytm-transport-proof-command"
        )
        write_frame(writer, command.SerializeToString())
        await writer.drain()

        event_bytes = await asyncio.wait_for(read_frame(reader), timeout=5)
        event = ProofMessage()
        event.ParseFromString(event_bytes)

        assert event.schema_version == command.schema_version
        assert event.payload == "corytm-transport-proof-event"

        writer.close()
        await writer.wait_closed()

        return_code = await asyncio.wait_for(process.wait(), timeout=5)
        assert return_code == 0
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()

        server.close()
        await server.wait_closed()


@pytest.mark.transport
def test_transport_round_trip() -> None:
    asyncio.run(_round_trip())
