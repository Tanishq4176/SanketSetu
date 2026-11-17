"""Binary JPEG frame batching using the ISLF protocol.

Layout: magic b'ISLF' | uint16 little-endian frame count | uint32 lengths | JPEGs.
"""
from __future__ import annotations
import struct

MAGIC = b"ISLF"
_HEADER = struct.Struct("<4sH")


def pack_frames(jpegs: list[bytes]) -> bytes:
    if not jpegs:
        raise ValueError("No frames to pack")
    if len(jpegs) > 65535:
        raise ValueError("Too many frames")
    if any(not isinstance(frame, bytes) or not frame for frame in jpegs):
        raise ValueError("Each frame must be non-empty bytes")
    lengths = struct.pack(f"<{len(jpegs)}I", *(len(frame) for frame in jpegs))
    return _HEADER.pack(MAGIC, len(jpegs)) + lengths + b"".join(jpegs)


def unpack_frames(body: bytes, expected: int = 16, max_frame_bytes: int = 500_000) -> list[bytes]:
    if len(body) < _HEADER.size:
        raise ValueError("Payload too short")
    magic, count = _HEADER.unpack_from(body)
    if magic != MAGIC:
        raise ValueError("Bad payload header")
    if count != expected:
        raise ValueError(f"Expected {expected} frames, got {count}")
    table_end = _HEADER.size + 4 * count
    if len(body) < table_end:
        raise ValueError("Truncated length table")
    lengths = struct.unpack_from(f"<{count}I", body, _HEADER.size)
    if any(length == 0 or length > max_frame_bytes for length in lengths):
        raise ValueError("Invalid frame length")
    if sum(lengths) != len(body) - table_end:
        raise ValueError("Payload length mismatch")
    frames, offset = [], table_end
    for length in lengths:
        frames.append(body[offset:offset + length])
        offset += length
    return frames
