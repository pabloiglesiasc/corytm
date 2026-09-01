"""Wire framing for the Python↔Native Audio Runtime transport.

Implements ADR-007's length-prefixed frame format over the loopback
socket: a `TRANSPORT_MAGIC`/payload-length header followed by the raw
payload bytes. Framing only — callers own message encoding/decoding.
"""

import asyncio
import struct
from typing import Protocol

TRANSPORT_MAGIC = 0x636F7274
_HEADER_FORMAT = "<II"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)


class FrameWriter(Protocol):
    """The minimal write surface `write_frame` needs from its writer."""

    def write(self, data: bytes) -> None: ...


async def read_frame(reader: asyncio.StreamReader) -> bytes:
    """Read one length-prefixed frame's payload from `reader`.

    Blocks until a full header and payload have arrived, or the stream
    ends early.

    Args:
        reader: The stream to read a single frame from.

    Returns:
        The frame's raw payload bytes, header stripped.

    Raises:
        ValueError: The header's magic number doesn't match
            `TRANSPORT_MAGIC`.
        asyncio.IncompleteReadError: The stream ended before a full
            header or payload arrived.
    """
    header = await reader.readexactly(_HEADER_SIZE)
    magic, length = struct.unpack(_HEADER_FORMAT, header)

    if magic != TRANSPORT_MAGIC:
        raise ValueError(f"unexpected magic number: {magic:#x}")

    return await reader.readexactly(length)


def write_frame(writer: FrameWriter, payload: bytes) -> None:
    """Write `payload` to `writer` as one length-prefixed frame.

    Args:
        writer: The destination to write the framed bytes to.
        payload: The raw message bytes to frame and write.
    """
    writer.write(struct.pack(_HEADER_FORMAT, TRANSPORT_MAGIC, len(payload)) + payload)
