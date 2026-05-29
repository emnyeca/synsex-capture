"""Micro-timing helpers for Digitone II trigger records."""

from __future__ import annotations

from ..errors import SyxFileError


def encode_micro_timing(value: int) -> int:
    if value < -23 or value > 23:
        raise SyxFileError(f"micro_timing must be in -23..23: {value}")
    return value & 0xFF