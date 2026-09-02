import asyncio
import sys

import pytest

from corytm.generated.project_pb2 import MoveClipCommand
from corytm.runtime.desktop import serve_desktop_channel
from corytm.runtime.transport import write_frame


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


async def _read_handshake(stdout: _CapturingStdout) -> tuple[int, str]:
    while True:
        for line in stdout.lines:
            if line.startswith("DESKTOP "):
                _, port_text, secret = line.split(" ")
                return int(port_text), secret
        await asyncio.sleep(0.01)


async def _scenario() -> None:
    stdout = _CapturingStdout()
    original_stdout = sys.stdout
    sys.stdout = stdout
    try:
        server_task = asyncio.create_task(serve_desktop_channel())

        port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

        _reader, writer = await asyncio.open_connection("127.0.0.1", port)
        write_frame(writer, secret.encode("utf-8"))
        await writer.drain()

        command = MoveClipCommand(
            schema_version=1,
            project_id="desktop-fixture",
            track_id="track-1",
            clip_id="no-such-clip",
            new_start_seconds=1.0,
        )
        write_frame(writer, command.SerializeToString())
        await writer.drain()

        with pytest.raises(ValueError, match="no clip"):
            await server_task

        writer.close()
        await writer.wait_closed()
    finally:
        sys.stdout = original_stdout


def test_a_command_handler_failure_does_not_deadlock_teardown() -> None:
    asyncio.run(asyncio.wait_for(_scenario(), timeout=15))
