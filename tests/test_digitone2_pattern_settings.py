from pathlib import Path

import pytest

from digitone_syx_toolkit.digitone2.constants import (
    CHECKSUM_HI_OFFSET,
    CHECKSUM_LO_OFFSET,
    PATTERN_CHANGE_EXTENDED_MASK,
    PATTERN_CHANGE_EXTENDED_OFFSET,
    PATTERN_CHANGE_LOW_OFFSET,
    PATTERN_CHANGE_OFF_LOW_VALUE,
    PATTERN_MODE_OFFSET,
    PATTERN_MODE_PER_TRACK,
    PATTERN_SPEED_OFFSET,
    PATTERN_RESET_EXTENDED_MASK,
    PATTERN_RESET_EXTENDED_OFFSET,
    PATTERN_RESET_INF_LOW_VALUE,
    PATTERN_RESET_LOW_OFFSET,
    PATTERN_TEMPO_CONTROL_OFFSET,
    PATTERN_TEMPO_HI_MSB_MASK,
    PATTERN_TEMPO_HI_OFFSET,
    PATTERN_TEMPO_LO_MSB_MASK,
    PATTERN_TEMPO_LO_OFFSET,
    PATTERN_TOTAL_STEPS_CONTROL_OFFSET,
    PATTERN_TOTAL_STEPS_MSB_MASK,
    PATTERN_TOTAL_STEPS_PAYLOAD_OFFSET,
    SPEED_CODE_MAP,
    TRACK_LENGTH_TARGETS,
    TRACK_SPEED_OFFSETS,
    TRACK_TOTAL_STEPS_TARGETS,
)
from digitone_syx_toolkit.events_to_syx import build_syx_from_events


def _build_with_pattern(tmp_path: Path, *, tempo: float, speed: str, total_steps: int) -> bytes:
    events = tmp_path / "pattern.yaml"
    events.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        f"  tempo: {tempo}\n"
        f"  speed: {speed}\n"
        f"  total_steps: {total_steps}\n"
        "events: []\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.syx"
    build_syx_from_events(events_yaml=events, output_file=output, template_file=Path("captures/BASE/BASE_EMPTY.syx"))
    return output.read_bytes()


def _build_with_per_track(tmp_path: Path) -> bytes:
    events = tmp_path / "per_track.yaml"
    track_scale_lines = []
    for track in range(1, 17):
        length = 128 if track == 16 else 15 + track
        speed = "1/2" if track % 2 == 0 else "1"
        track_scale_lines.append(f"  {track}: {{length: {length}, speed: '{speed}'}}\n")
    events.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "name: per track signature\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: OFF\n"
        "  reset: INF\n"
        "track_scale:\n"
        + "".join(track_scale_lines)
        + "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n"
        "  - step: 2\n"
        "    track: 2\n"
        "    note: D5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
        encoding="utf-8",
    )
    output = tmp_path / "per_track.syx"
    build_syx_from_events(events_yaml=events, output_file=output, template_file=Path("captures/BASE/BASE_EMPTY.syx"))
    return output.read_bytes()


def _decode_tempo(data: bytes) -> int:
    hi = data[PATTERN_TEMPO_HI_OFFSET] & 0x7F
    lo = data[PATTERN_TEMPO_LO_OFFSET] & 0x7F
    if data[PATTERN_TEMPO_CONTROL_OFFSET] & PATTERN_TEMPO_HI_MSB_MASK:
        hi |= 0x80
    if data[PATTERN_TEMPO_CONTROL_OFFSET] & PATTERN_TEMPO_LO_MSB_MASK:
        lo |= 0x80
    return (hi << 8) | lo


def _decode_total_steps_payload_value(data: bytes, *, control_offset: int, payload_offset: int, msb_mask: int) -> int:
    value = data[payload_offset] & 0x7F
    if data[control_offset] & msb_mask:
        value |= 0x80
    return value


def _decode_checksum(data: bytes) -> int:
    return ((data[CHECKSUM_HI_OFFSET] & 0x7F) << 7) | (data[CHECKSUM_LO_OFFSET] & 0x7F)


@pytest.mark.parametrize("tempo", [120.0, 130.0, 300.0])
def test_pattern_tempo_encoding(tmp_path: Path, tempo: float):
    built = _build_with_pattern(tmp_path, tempo=tempo, speed="1", total_steps=16)
    assert _decode_tempo(built) == round(tempo * 120)


def test_pattern_speed_encoding(tmp_path: Path):
    built = _build_with_pattern(tmp_path, tempo=120.0, speed="1/8", total_steps=16)
    assert built[PATTERN_SPEED_OFFSET] == SPEED_CODE_MAP["1/8"]


@pytest.mark.parametrize("total_steps", [16, 64, 128])
def test_pattern_total_steps_and_track_mirrors(tmp_path: Path, total_steps: int):
    built = _build_with_pattern(tmp_path, tempo=120.0, speed="1", total_steps=total_steps)

    assert built[PATTERN_MODE_OFFSET] == 0x00
    assert _decode_total_steps_payload_value(
        built,
        control_offset=PATTERN_TOTAL_STEPS_CONTROL_OFFSET,
        payload_offset=PATTERN_TOTAL_STEPS_PAYLOAD_OFFSET,
        msb_mask=PATTERN_TOTAL_STEPS_MSB_MASK,
    ) == total_steps

    for _track, control_offset, payload_offset, msb_mask in TRACK_TOTAL_STEPS_TARGETS:
        assert _decode_total_steps_payload_value(
            built,
            control_offset=control_offset,
            payload_offset=payload_offset,
            msb_mask=msb_mask,
        ) == total_steps


def test_per_track_mode_writes_track_lengths_speeds_change_reset_and_checksum(tmp_path: Path):
    built = _build_with_per_track(tmp_path)

    assert built[PATTERN_MODE_OFFSET] == PATTERN_MODE_PER_TRACK
    assert built[PATTERN_CHANGE_EXTENDED_OFFSET] & PATTERN_CHANGE_EXTENDED_MASK == 0
    assert built[PATTERN_CHANGE_LOW_OFFSET] == PATTERN_CHANGE_OFF_LOW_VALUE
    assert built[PATTERN_RESET_EXTENDED_OFFSET] & PATTERN_RESET_EXTENDED_MASK == 0
    assert built[PATTERN_RESET_LOW_OFFSET] == PATTERN_RESET_INF_LOW_VALUE

    for track, control_offset, payload_offset, msb_mask in TRACK_LENGTH_TARGETS:
        expected_length = 128 if track == 16 else 15 + track
        assert _decode_total_steps_payload_value(
            built,
            control_offset=control_offset,
            payload_offset=payload_offset,
            msb_mask=msb_mask,
        ) == expected_length

        expected_speed = "1/2" if track % 2 == 0 else "1"
        assert built[TRACK_SPEED_OFFSETS[track]] == SPEED_CODE_MAP[expected_speed]

    control_offset, payload_offset, msb_mask = TRACK_LENGTH_TARGETS[-1][1:]
    assert built[control_offset] & msb_mask == msb_mask
    assert built[payload_offset] == 0x00
    assert built[PATTERN_TOTAL_STEPS_PAYLOAD_OFFSET] == PATTERN_RESET_INF_LOW_VALUE

    expected_checksum = sum(built[10:114113]) % 16384
    assert _decode_checksum(built) == expected_checksum
