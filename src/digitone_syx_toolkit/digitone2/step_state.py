"""Step-state helpers for Digitone II trigger generation."""

from __future__ import annotations

from ..errors import SyxFileError
from ..events_yaml import EventItem
from .constants import (
    STEP_STATE_ENTRY_SIZE,
    STEP_STATE_LOGICAL_BASE,
    STEP_STATE_TRACK_STRIDE,
    SUPPORTED_STEP_MAX,
    SUPPORTED_STEP_MIN,
    SUPPORTED_TRACK_MAX,
    SUPPORTED_TRACK_MIN,
)


def step_state_logical_offset(track: int, step: int) -> int:
    """Return decoded payload offset for a track/step step-state entry."""
    if track < SUPPORTED_TRACK_MIN or track > SUPPORTED_TRACK_MAX:
        raise SyxFileError(f"track out of supported range: {track}")
    if step < SUPPORTED_STEP_MIN or step > SUPPORTED_STEP_MAX:
        raise SyxFileError(f"step out of supported range: {step}")

    track_index = track - 1
    step_index = step - 1
    return STEP_STATE_LOGICAL_BASE + STEP_STATE_TRACK_STRIDE * track_index + STEP_STATE_ENTRY_SIZE * step_index


def normal_trigger_step_state(step: int) -> bytes:
    """Return decoded 2-byte step-state value for a normal trigger."""
    if step < SUPPORTED_STEP_MIN or step > SUPPORTED_STEP_MAX:
        raise SyxFileError(f"step out of supported range: {step}")
    return bytes((0x03, 0x81 if (step % 2) == 1 else 0x91))


def write_normal_trigger_step_state(decoded_payload: bytearray, track: int, step: int) -> None:
    offset = step_state_logical_offset(track, step)
    value = normal_trigger_step_state(step)
    decoded_payload[offset : offset + STEP_STATE_ENTRY_SIZE] = value


def write_events_step_state(decoded_payload: bytearray, events: tuple[EventItem, ...]) -> None:
    """Write normal trigger step-state entries for all events."""
    for event in events:
        write_normal_trigger_step_state(decoded_payload, event.track, event.step)
