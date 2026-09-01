import asyncio
import struct
from typing import Protocol

TRANSPORT_MAGIC = 0x636F7274
_HEADER_FORMAT = "<II"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)


class FrameWriter(Protocol):
    def write(self, data: bytes) -> None: ...


async def read_frame(reader: asyncio.StreamReader) -> bytes:
    header = await reader.readexactly(_HEADER_SIZE)
    magic, length = struct.unpack(_HEADER_FORMAT, header)

    if magic != TRANSPORT_MAGIC:
        raise ValueError(f"unexpected magic number: {magic:#x}")

    return await reader.readexactly(length)


def write_frame(writer: FrameWriter, payload: bytes) -> None:
    writer.write(struct.pack(_HEADER_FORMAT, TRANSPORT_MAGIC, len(payload)) + payload)
