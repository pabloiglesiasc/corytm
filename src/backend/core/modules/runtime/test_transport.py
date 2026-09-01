import asyncio

import pytest

from runtime.transport import TRANSPORT_MAGIC, read_frame, write_frame


class _RecordingWriter:
    def __init__(self) -> None:
        self.written = b""

    def write(self, data: bytes) -> None:
        self.written += data


def test_write_frame_prefixes_magic_and_length() -> None:
    writer = _RecordingWriter()

    write_frame(writer, b"payload")

    magic = int.from_bytes(writer.written[0:4], "little")
    length = int.from_bytes(writer.written[4:8], "little")

    assert magic == TRANSPORT_MAGIC
    assert length == len(b"payload")
    assert writer.written[8:] == b"payload"


def test_read_frame_round_trips_a_written_frame() -> None:
    writer = _RecordingWriter()
    write_frame(writer, b"corytm-runtime-transport-test")

    async def _read() -> bytes:
        reader = asyncio.StreamReader()
        reader.feed_data(writer.written)
        reader.feed_eof()
        return await read_frame(reader)

    assert asyncio.run(_read()) == b"corytm-runtime-transport-test"


def test_read_frame_rejects_wrong_magic() -> None:
    async def _read_bad_frame() -> bytes:
        reader = asyncio.StreamReader()
        reader.feed_data((0).to_bytes(4, "little") + (0).to_bytes(4, "little"))
        reader.feed_eof()
        return await read_frame(reader)

    with pytest.raises(ValueError):
        asyncio.run(_read_bad_frame())
