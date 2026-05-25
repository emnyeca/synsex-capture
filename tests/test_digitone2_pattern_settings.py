from pathlib import Path

import pytest

from digitone_syx_toolkit.digitone2.constants import (
    PATTERN_MODE_OFFSET,
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
    build_syx_from_events(events_yaml=events, output_file=output, template_file=Path("captures/BASE_EMPTY.syx"))
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
