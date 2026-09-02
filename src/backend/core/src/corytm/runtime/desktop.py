"""Serves ADR-010's second, Desktop-facing loopback transport.

Implements the Python-core half of the Desktop↔Python command channel:
a second `asyncio` listener, independent of whatever port/secret this
process later uses to spawn and authenticate the Native Audio Runtime
(ADR-007), whose port and per-launch secret are handed to Rust over the
existing sidecar stdout lifecycle channel.
"""

import asyncio
import secrets
import sys

from corytm.generated.desktop_pb2 import DesktopProofMessage

from .transport import read_frame, write_frame

_AUTHENTICATION_TIMEOUT_SECONDS = 5
_COMMAND_TIMEOUT_SECONDS = 30


async def serve_desktop_channel() -> None:
    """Run the Desktop channel proof-of-mechanism server until shutdown.

    Prints `READY` followed by a `DESKTOP <port> <secret>` line over
    stdout, accepts exactly one authenticated client connection,
    exchanges one `DesktopProofMessage` command/event round trip, then
    blocks reading stdin lines until `SHUTDOWN` before returning —
    mirroring `sidecar_proof.py`'s existing lifecycle protocol with one
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
        command = DesktopProofMessage()
        command.ParseFromString(command_bytes)

        event = DesktopProofMessage(
            schema_version=command.schema_version,
            payload="corytm-desktop-transport-proof-event",
        )
        write_frame(writer, event.SerializeToString())
        await writer.drain()

        writer.close()
        await writer.wait_closed()
    finally:
        server.close()
        await server.wait_closed()

    for line in sys.stdin:
        if line.strip() == "SHUTDOWN":
            break
