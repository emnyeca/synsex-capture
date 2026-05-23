"""Utilities for reading/writing SysEx (.syx) files."""

from __future__ import annotations

from pathlib import Path

from .errors import SyxFileError


def extract_sysex_messages(raw: bytes) -> list[bytes]:
    """Extract one or more SysEx packets from a byte stream."""
    messages: list[bytes] = []
    start: int | None = None

    for idx, value in enumerate(raw):
        if value == 0xF0 and start is None:
            start = idx
        elif value == 0xF7 and start is not None:
            messages.append(raw[start : idx + 1])
            start = None

    return messages


def save_syx_file(messages: list[bytes], path: str | Path) -> Path:
    """Write SysEx message list to a .syx file."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    for msg in messages:
        if not msg or msg[0] != 0xF0 or msg[-1] != 0xF7:
            raise SyxFileError("Invalid SysEx packet. A packet must start with F0 and end with F7.")

    file_path.write_bytes(b"".join(messages))
    return file_path


def load_syx_file(path: str | Path) -> list[bytes]:
    """Read a .syx file and return all SysEx packets inside it."""
    file_path = Path(path)
    if not file_path.exists():
        raise SyxFileError(f".syx file not found: {file_path}")

    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        raise SyxFileError(f"Failed to read .syx file: {file_path}") from exc

    packets = extract_sysex_messages(raw)
    if not packets and raw:
        raise SyxFileError(
            f"No valid SysEx packets found in file: {file_path}. "
            "Expected one or more F0...F7 packets."
        )
    return packets
