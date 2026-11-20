#!/usr/bin/env python3
"""Validate the pre-rendered FreeBSD splash assets without third-party modules."""

from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent
BMP = ROOT / "customfiles/boot/fluidos-splash.bmp"
PNG = ROOT / "customfiles/boot/fluidos-splash.png"
EXPECTED = (320, 200)


def check_bmp(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise SystemExit(f"Invalid BMP header: {path}")
    file_size, _reserved1, _reserved2, pixel_offset = struct.unpack_from("<IHHI", data, 2)
    header_size, width, height, planes, bits, compression, image_size, _x, _y, colors, _important = (
        struct.unpack_from("<IiiHHIIiiII", data, 14)
    )
    if (header_size < 40 or (width, height) != EXPECTED or planes != 1
            or bits != 8 or compression != 0 or file_size != len(data)
            or pixel_offset < 54 or pixel_offset > len(data)):
        raise SystemExit(f"BMP must be a valid uncompressed 320x200 8-bit image: {path}")
    palette_entries = colors or (pixel_offset - 54) // 4
    if palette_entries != 256:
        raise SystemExit(f"BMP must contain a 256-colour palette: {path}")
    row_size = ((width * bits + 31) // 32) * 4
    if image_size not in (0, row_size * height) or pixel_offset + row_size * height > len(data):
        raise SystemExit(f"BMP pixel data is incomplete: {path}")
    print(f"OK BMP {width}x{height}, 8-bit palette: {path.relative_to(ROOT)}")


def check_png(path: Path) -> None:
    data = path.read_bytes()
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        raise SystemExit(f"Invalid PNG signature: {path}")
    pos = len(signature)
    chunks = []
    idat = bytearray()
    saw_iend = False
    while pos + 12 <= len(data):
        length = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 8 + length
        if end + 4 > len(data):
            raise SystemExit(f"Truncated PNG chunk: {path}")
        payload = data[pos + 8:end]
        stored_crc = struct.unpack_from(">I", data, end)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != stored_crc:
            raise SystemExit(f"PNG CRC mismatch in {kind!r}: {path}")
        chunks.append(kind)
        if kind == b"IHDR":
            if len(payload) != 13:
                raise SystemExit(f"Invalid PNG IHDR: {path}")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if ((width, height) != EXPECTED or bit_depth != 8 or color_type != 6
                    or compression != 0 or filtering != 0 or interlace != 0):
                raise SystemExit(f"PNG must be non-interlaced 320x200 RGBA 8-bit: {path}")
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            saw_iend = True
            pos = end + 4
            break
        pos = end + 4
    if not saw_iend or pos != len(data) or not chunks or chunks[0] != b"IHDR" or b"IDAT" not in chunks:
        raise SystemExit(f"Incomplete PNG structure: {path}")
    raw = zlib.decompress(bytes(idat))
    expected_bytes = EXPECTED[1] * (1 + EXPECTED[0] * 4)
    if len(raw) != expected_bytes:
        raise SystemExit(f"PNG decoded data length is incorrect: {path}")
    if any(raw[row * (1 + EXPECTED[0] * 4)] > 4 for row in range(EXPECTED[1])):
        raise SystemExit(f"PNG contains an unsupported row filter: {path}")
    print(f"OK PNG {width}x{height}, RGBA 8-bit: {path.relative_to(ROOT)}")


check_bmp(BMP)
check_png(PNG)
