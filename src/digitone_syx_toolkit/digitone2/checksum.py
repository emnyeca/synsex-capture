"""Checksum helper for current Digitone II implementation."""

from __future__ import annotations

from .constants import (
    CHECKSUM_HI_OFFSET,
    CHECKSUM_LO_OFFSET,
    CHECKSUM_SUM_END,
    CHECKSUM_SUM_START,
)


def recompute_checksum(data: bytearray) -> None:
    checksum = sum(data[CHECKSUM_SUM_START:CHECKSUM_SUM_END]) % 16384
    data[CHECKSUM_HI_OFFSET] = (checksum >> 7) & 0x7F
    data[CHECKSUM_LO_OFFSET] = checksum & 0x7F
