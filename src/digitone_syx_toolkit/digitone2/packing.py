"""7-bit packed byte helpers."""

from __future__ import annotations


def set_packed_byte(data: bytearray, *, payload_offset: int, control_offset: int, msb_mask: int, value: int) -> None:
    if value < 0 or value > 0xFF:
        raise ValueError(f"value out of range: {value}")
    data[payload_offset] = value & 0x7F
    if value & 0x80:
        data[control_offset] |= msb_mask
    else:
        data[control_offset] &= (~msb_mask) & 0x7F


def trigger_payload_offset_from_index(payload_index: int, *, control_start: int, payload_start: int) -> tuple[int, int, int]:
    group = payload_index // 7
    pos_in_group = payload_index % 7  # 0..6
    control_offset = control_start + (group * 8)
    payload_offset = payload_start + payload_index + group
    mask = 0x40 >> pos_in_group
    return payload_offset, control_offset, mask


def set_trigger_packed_byte(
    data: bytearray,
    *,
    payload_index: int,
    control_start: int,
    payload_start: int,
    value: int,
) -> None:
    payload_offset, control_offset, mask = trigger_payload_offset_from_index(
        payload_index,
        control_start=control_start,
        payload_start=payload_start,
    )
    set_packed_byte(
        data,
        payload_offset=payload_offset,
        control_offset=control_offset,
        msb_mask=mask,
        value=value,
    )
