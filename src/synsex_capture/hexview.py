"""Hex dump rendering for binary SysEx files."""

from __future__ import annotations

from pathlib import Path


def hex_dump(data: bytes, width: int = 16) -> str:
    """Render bytes in a classic offset/hex/ascii table."""
    lines: list[str] = []
    for offset in range(0, len(data), width):
        chunk = data[offset : offset + width]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        hex_part = hex_part.ljust(width * 3 - 1)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{offset:08X}  {hex_part}  |{ascii_part}|")
    return "\n".join(lines)


def hex_dump_file(path: str | Path, width: int = 16) -> str:
    """Load a binary file and return hex dump text."""
    data = Path(path).read_bytes()
    return hex_dump(data, width=width)
