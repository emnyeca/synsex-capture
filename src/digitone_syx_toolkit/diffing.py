"""Binary diff support for .syx files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ByteDifference:
    """A byte-level difference at an offset."""

    offset: int
    before: int | None
    after: int | None


@dataclass
class DiffResult:
    """Summary of two-file byte comparison."""

    len1: int
    len2: int
    differences: list[ByteDifference]


def diff_bytes(data1: bytes, data2: bytes) -> DiffResult:
    """Compare two byte buffers and return all differing offsets."""
    max_len = max(len(data1), len(data2))
    differences: list[ByteDifference] = []

    for offset in range(max_len):
        b1 = data1[offset] if offset < len(data1) else None
        b2 = data2[offset] if offset < len(data2) else None
        if b1 != b2:
            differences.append(ByteDifference(offset=offset, before=b1, after=b2))

    return DiffResult(len1=len(data1), len2=len(data2), differences=differences)


def diff_syx_files(file1: str | Path, file2: str | Path) -> DiffResult:
    """Compare two files as raw bytes."""
    data1 = Path(file1).read_bytes()
    data2 = Path(file2).read_bytes()
    return diff_bytes(data1, data2)


def format_diff(result: DiffResult, limit: int | None = None) -> str:
    """Render diff result as human-readable text with hex values."""
    lines = [
        f"Length file1: {result.len1} bytes",
        f"Length file2: {result.len2} bytes",
        f"Differences : {len(result.differences)}",
    ]

    if not result.differences:
        return "\n".join(lines + ["No differences detected."])

    lines.append("offset    before  after")
    lines.append("--------  ------  -----")

    rows = result.differences if limit is None else result.differences[:limit]
    for d in rows:
        before_hex = "--" if d.before is None else f"{d.before:02X}"
        after_hex = "--" if d.after is None else f"{d.after:02X}"
        lines.append(f"0x{d.offset:06X}  {before_hex:>6}  {after_hex:>5}")

    if limit is not None and len(result.differences) > limit:
        lines.append(f"... truncated to first {limit} differences")

    return "\n".join(lines)
