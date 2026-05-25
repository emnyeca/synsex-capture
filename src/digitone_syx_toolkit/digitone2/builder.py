"""Digitone II pattern builder from normalized event assignment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..errors import SyxFileError
from ..events_yaml import EventAssignment
from .checksum import recompute_checksum
from .constants import (
    LENGTH_CODE_MAP,
    PATTERN_MODE_OFFSET,
    PATTERN_MODE_PATTERN_WIDE,
    PATTERN_SPEED_OFFSET,
    PATTERN_TEMPO_CONTROL_OFFSET,
    PATTERN_TEMPO_HI_MSB_MASK,
    PATTERN_TEMPO_HI_OFFSET,
    PATTERN_TEMPO_LO_MSB_MASK,
    PATTERN_TEMPO_LO_OFFSET,
    PATTERN_TOTAL_STEPS_CONTROL_OFFSET,
    PATTERN_TOTAL_STEPS_MSB_MASK,
    PATTERN_TOTAL_STEPS_PAYLOAD_OFFSET,
    SPEED_CODE_MAP,
    STEP_STATE_TRACK1_OFFSETS,
    TRACK_TOTAL_STEPS_TARGETS,
    TRACK1_DEFAULT_LENGTH_OFFSET,
    TRACK1_DEFAULT_VELOCITY_OFFSET,
    TRIGGER_MAX_SLOTS,
    TRIGGER_REGION_CONTROL_START,
    TRIGGER_REGION_PAYLOAD_START,
    TRIGGER_SLOT_SIZE,
    TRIGGER_SLOT0_PAYLOAD_INDEX,
)
from .packing import set_packed_byte, set_trigger_packed_byte
from .template import load_base_empty_template


@dataclass(frozen=True)
class BuildResult:
    output_file: Path
    written_events: int
    warnings: tuple[str, ...]


def _length_to_code(length: str) -> int:
    key = length.upper()
    if key == "INHERIT":
        return 0xFF
    if key not in LENGTH_CODE_MAP:
        raise SyxFileError(f"Unsupported length: {length}")
    return LENGTH_CODE_MAP[key]


def _set_pattern_fields(data: bytearray, assignment: EventAssignment) -> None:
    data[PATTERN_MODE_OFFSET] = PATTERN_MODE_PATTERN_WIDE

    speed = assignment.pattern.speed
    if speed not in SPEED_CODE_MAP:
        raise SyxFileError(f"Unsupported pattern.speed: {speed}")
    data[PATTERN_SPEED_OFFSET] = SPEED_CODE_MAP[speed]

    scaled_tempo = round(assignment.pattern.tempo * 120)
    tempo_hi = (scaled_tempo >> 8) & 0xFF
    tempo_lo = scaled_tempo & 0xFF
    set_packed_byte(
        data,
        payload_offset=PATTERN_TEMPO_HI_OFFSET,
        control_offset=PATTERN_TEMPO_CONTROL_OFFSET,
        msb_mask=PATTERN_TEMPO_HI_MSB_MASK,
        value=tempo_hi,
    )
    set_packed_byte(
        data,
        payload_offset=PATTERN_TEMPO_LO_OFFSET,
        control_offset=PATTERN_TEMPO_CONTROL_OFFSET,
        msb_mask=PATTERN_TEMPO_LO_MSB_MASK,
        value=tempo_lo,
    )

    total_steps = assignment.pattern.total_steps
    set_packed_byte(
        data,
        payload_offset=PATTERN_TOTAL_STEPS_PAYLOAD_OFFSET,
        control_offset=PATTERN_TOTAL_STEPS_CONTROL_OFFSET,
        msb_mask=PATTERN_TOTAL_STEPS_MSB_MASK,
        value=total_steps,
    )
    for _track, control_offset, payload_offset, msb_mask in TRACK_TOTAL_STEPS_TARGETS:
        set_packed_byte(
            data,
            payload_offset=payload_offset,
            control_offset=control_offset,
            msb_mask=msb_mask,
            value=total_steps,
        )


def _set_track_defaults(data: bytearray, assignment: EventAssignment, warnings: list[str]) -> None:
    for track in assignment.tracks:
        if track.track != 1:
            warnings.append(
                f"track default for track={track.track} is not mapped yet; only track=1 defaults are applied"
            )
            continue
        data[TRACK1_DEFAULT_VELOCITY_OFFSET] = track.default_velocity
        data[TRACK1_DEFAULT_LENGTH_OFFSET] = _length_to_code(track.default_length)


def _set_step_state_table(data: bytearray, assignment: EventAssignment, warnings: list[str]) -> None:
    present_steps = {event.step for event in assignment.events}
    for step in range(1, assignment.pattern.total_steps + 1):
        offset = STEP_STATE_TRACK1_OFFSETS.get(step)
        if offset is None:
            if step in present_steps:
                warnings.append(f"step state mapping for step={step} is unknown; trigger may be hidden on device")
            continue
        data[offset] = 0x01 if step in present_steps else 0x00


def _clear_trigger_slots(data: bytearray) -> None:
    for slot_index in range(TRIGGER_MAX_SLOTS):
        base = TRIGGER_SLOT0_PAYLOAD_INDEX + (slot_index * TRIGGER_SLOT_SIZE)
        # Empty slot model observed in captures: all attributes set to decoded 0xFF.
        for rel in range(TRIGGER_SLOT_SIZE):
            set_trigger_packed_byte(
                data,
                payload_index=base + rel,
                control_start=TRIGGER_REGION_CONTROL_START,
                payload_start=TRIGGER_REGION_PAYLOAD_START,
                value=0xFF,
            )


def _write_trigger_slots(data: bytearray, assignment: EventAssignment) -> int:
    if len(assignment.events) > TRIGGER_MAX_SLOTS:
        raise SyxFileError(
            f"events count exceeds supported trigger slots: {len(assignment.events)} > {TRIGGER_MAX_SLOTS}"
        )

    written = 0
    for slot_index, event in enumerate(assignment.events):
        base = TRIGGER_SLOT0_PAYLOAD_INDEX + (slot_index * TRIGGER_SLOT_SIZE)

        field0_track = event.track - 1
        step_index = event.step - 1
        pitch = event.note_midi
        velocity = 0xFF if event.velocity == "inherit" else int(event.velocity)
        length = _length_to_code(event.length)

        values = (field0_track, step_index, pitch, velocity, length, 0x00)
        for rel, value in enumerate(values):
            set_trigger_packed_byte(
                data,
                payload_index=base + rel,
                control_start=TRIGGER_REGION_CONTROL_START,
                payload_start=TRIGGER_REGION_PAYLOAD_START,
                value=value,
            )
        written += 1
    return written


def build_digitone2_syx(
    *,
    assignment: EventAssignment,
    output_file: str | Path,
    template_override: str | Path | None = None,
) -> BuildResult:
    template_bytes = (
        Path(template_override).read_bytes() if template_override else load_base_empty_template()
    )
    data = bytearray(template_bytes)

    warnings: list[str] = []
    _set_pattern_fields(data, assignment)
    _set_track_defaults(data, assignment, warnings)
    _clear_trigger_slots(data)
    written_events = _write_trigger_slots(data, assignment)
    _set_step_state_table(data, assignment, warnings)
    recompute_checksum(data)

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(bytes(data))

    return BuildResult(
        output_file=out_path,
        written_events=written_events,
        warnings=tuple(warnings),
    )
