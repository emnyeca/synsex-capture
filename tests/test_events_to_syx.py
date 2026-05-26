from pathlib import Path

import pytest

from digitone_syx_toolkit.digitone2.constants import (
    CHECKSUM_SUM_END,
    CHECKSUM_SUM_START,
    EXPLICIT_LENGTH_CODE_TO_DISPLAY,
    TRIGGER_REGION_CONTROL_START,
    TRIGGER_REGION_PAYLOAD_START,
    TRIGGER_SLOT_SIZE,
    TRIGGER_SLOT0_PAYLOAD_INDEX,
)
from digitone_syx_toolkit.digitone2.packing import trigger_payload_offset_from_index, unpack_7bit_region
from digitone_syx_toolkit.digitone2.pattern_name import (
    PATTERN_NAME_MAX_CHARS,
    PATTERN_NAME_PRIMARY_DECODED_OFFSET,
    PATTERN_NAME_SHADOW_DECODED_OFFSET,
)
from digitone_syx_toolkit.errors import SyxFileError
from digitone_syx_toolkit.events_to_syx import build_syx_from_events, default_output_file_for_events


def _decode_pattern_name_fields(data: bytes) -> tuple[bytes, bytes]:
    decoded = unpack_7bit_region(data, start=CHECKSUM_SUM_START, end_exclusive=CHECKSUM_SUM_END)
    p0 = PATTERN_NAME_PRIMARY_DECODED_OFFSET
    s0 = PATTERN_NAME_SHADOW_DECODED_OFFSET
    primary = bytes(decoded[p0 : p0 + PATTERN_NAME_MAX_CHARS])
    shadow = bytes(decoded[s0 : s0 + PATTERN_NAME_MAX_CHARS])
    return primary, shadow


def _pattern_name_packed_offsets() -> set[int]:
    offsets: set[int] = set()
    for base in (PATTERN_NAME_PRIMARY_DECODED_OFFSET, PATTERN_NAME_SHADOW_DECODED_OFFSET):
        for rel in range(PATTERN_NAME_MAX_CHARS):
            abs_idx = base + rel
            group = abs_idx // 7
            pos = abs_idx % 7
            control_offset = CHECKSUM_SUM_START + group * 8
            payload_offset = control_offset + 1 + pos
            offsets.add(control_offset)
            offsets.add(payload_offset)
    offsets.update({114113, 114114})
    return offsets


def _write_events_yaml(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def _read_trigger_slot_value(data: bytes, slot_index: int, rel: int) -> int:
    payload_index = TRIGGER_SLOT0_PAYLOAD_INDEX + slot_index * TRIGGER_SLOT_SIZE + rel
    payload_offset, control_offset, mask = trigger_payload_offset_from_index(
        payload_index,
        control_start=TRIGGER_REGION_CONTROL_START,
        payload_start=TRIGGER_REGION_PAYLOAD_START,
    )
    value = data[payload_offset] & 0x7F
    if data[control_offset] & mask:
        value |= 0x80
    return value


@pytest.mark.parametrize(
    ("events_name", "expected_name"),
    [
        ("trial.events.yaml", "trial.syx"),
        ("trial.events.yml", "trial.syx"),
        ("trial.yaml", "trial.syx"),
        ("trial.yml", "trial.syx"),
        ("trial4_multiple_track_multiple_trigger_noninherit.events.yaml", "trial4_multiple_track_multiple_trigger_noninherit.syx"),
    ],
)
def test_default_output_file_for_events(events_name: str, expected_name: str):
    result = default_output_file_for_events(events_name)
    assert result.as_posix() == f"captures/generated/{expected_name}"


def test_build_syx_from_events_encodes_trigger_record_fields(tmp_path: Path):
    events = tmp_path / "events.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 128\n"
        "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n"
        "  - step: 17\n"
        "    track: 2\n"
        "    note: D5\n"
        "    velocity: 84\n"
        "    length: '2'\n"
        "  - step: 128\n"
        "    track: 8\n"
        "    note: G4\n"
        "    velocity: inherit\n"
        "    length: 'INF'\n",
    )

    output = tmp_path / "out.syx"
    result = build_syx_from_events(events_yaml=events, output_file=output)

    built = output.read_bytes()
    assert result.written_events == 3

    # Slot 1: Track 1 / Step 1 / C5 / inherit / inherit
    assert [_read_trigger_slot_value(built, 0, rel) for rel in range(6)] == [0x00, 0x00, 0x3C, 0xFF, 0xFF, 0x00]

    # Slot 2: Track 2 / Step 17 / D5 / velocity 84 / length 2
    assert [_read_trigger_slot_value(built, 1, rel) for rel in range(6)] == [0x01, 0x10, 0x3E, 0x54, 0x1E, 0x00]

    # Slot 3: Track 8 / Step 128 / G4 / inherit / INF
    assert [_read_trigger_slot_value(built, 2, rel) for rel in range(6)] == [0x07, 0x7F, 0x37, 0xFF, 0x7F, 0x00]


def test_build_syx_from_events_writes_normalized_pattern_name(tmp_path: Path):
    events = tmp_path / "events_with_name.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        "name: Blue Moon A\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
    )

    output = tmp_path / "out_named.syx"
    build_syx_from_events(events_yaml=events, output_file=output)
    built = output.read_bytes()

    primary, shadow = _decode_pattern_name_fields(built)
    expected = b"BLUE MOON A" + b"\x00" * 5
    assert primary == expected
    assert shadow == expected


def test_build_syx_from_events_length_code_one_is_0x0E(tmp_path: Path):
    events = tmp_path / "events_length_one.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1\n"
        "  total_steps: 16\n"
        "events:\n"
        "  - step: 2\n"
        "    track: 2\n"
        "    note: D5\n"
        "    velocity: inherit\n"
        "    length: '1'\n",
    )

    output = tmp_path / "out_length_one.syx"
    build_syx_from_events(events_yaml=events, output_file=output)
    built = output.read_bytes()

    assert [_read_trigger_slot_value(built, 0, rel) for rel in range(6)] == [0x01, 0x01, 0x3E, 0xFF, 0x0E, 0x00]


def test_build_syx_from_events_checksum_recompute_is_consistent(tmp_path: Path):
    events = tmp_path / "events.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 126\n"
        "  speed: 1/8\n"
        "  total_steps: 64\n"
        "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
    )

    output = tmp_path / "out.syx"
    build_syx_from_events(events_yaml=events, output_file=output)
    built = output.read_bytes()

    expected_cs = sum(built[10:114113]) % 16384
    assert built[114113] == ((expected_cs >> 7) & 0x7F)
    assert built[114114] == (expected_cs & 0x7F)


def test_build_syx_from_events_rejects_duplicate_step_track(tmp_path: Path):
    events = tmp_path / "events_bad.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: D5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
    )

    with pytest.raises(SyxFileError, match="Chord is not supported"):
        build_syx_from_events(events_yaml=events, output_file=tmp_path / "out.syx")


def test_checksum_reference_speed_matches_capture(tmp_path: Path):
    events = tmp_path / "speed_patch.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events: []\n",
    )

    output = tmp_path / "speed_patched.syx"
    build_syx_from_events(
        events_yaml=events,
        output_file=output,
        template_file=Path("captures/CHECKSUM_BASE_EMPTY.syx"),
    )

    assert output.read_bytes() == Path("captures/CHECKSUM_REFERENCE_SPEED.syx").read_bytes()


def test_length_display_map_full_and_known_anchors():
    assert len(EXPLICIT_LENGTH_CODE_TO_DISPLAY) == 0x80
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x00] == ".125"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x02] == "1/64"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x06] == "1/32"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x0E] == "1/16"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x1E] == "1/8"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x2E] == "1/4"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x3E] == "1/2"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x4E] == "16.0"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x7E] == "128"
    assert EXPLICIT_LENGTH_CODE_TO_DISPLAY[0x7F] == "INF"


def test_inherit_and_explicit_inf_are_distinct_decoded_values(tmp_path: Path):
    events = tmp_path / "events_inf_vs_inherit.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n"
        "  - step: 2\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length:\n"
        "      code: \"0x7F\"\n"
        "      display: \"INF\"\n",
    )

    output = tmp_path / "inf_vs_inherit.syx"
    build_syx_from_events(events_yaml=events, output_file=output)
    built = output.read_bytes()

    slot1 = _read_trigger_slot_value(built, 0, 4)
    slot2 = _read_trigger_slot_value(built, 1, 4)
    assert slot1 == 0xFF
    assert slot2 == 0x7F


def test_explicit_length_code_input_writes_expected_decoded_value(tmp_path: Path):
    events = tmp_path / "events_length_code_26.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length_code: \"0x26\"\n",
    )

    output = tmp_path / "length_code_26.syx"
    build_syx_from_events(events_yaml=events, output_file=output)
    built = output.read_bytes()
    assert _read_trigger_slot_value(built, 0, 4) == 0x26


def test_hardware_validated_trials_1_to_4_regression(tmp_path: Path):
    fixtures = [
        (
            Path("captures/generated/events/trial1_minimal_trigger.events.yaml"),
            Path("captures/generated/trial1_minimal_trigger.syx"),
            Path("captures/BASE_EMPTY.syx"),
        ),
        (
            Path("captures/generated/events/trial2_page_track_cross.events.yaml"),
            Path("captures/generated/trial2_page_track_cross.syx"),
            Path("captures/BASE_EMPTY_STEPS128.syx"),
        ),
        (
            Path("captures/generated/events/trial3_same_track_multiple_trigger.events.yaml"),
            Path("captures/generated/trial3_same_track_multiple_trigger.syx"),
            Path("captures/BASE_EMPTY_STEPS128.syx"),
        ),
        (
            Path("captures/generated/events/trial4_multiple_track_multiple_trigger_noninherit.events.yaml"),
            Path("captures/generated/trial4_multiple_track_multiple_trigger_noninherit.syx"),
            Path("captures/BASE_EMPTY_STEPS128.syx"),
        ),
    ]

    for idx, (events_yaml, expected_syx, template_syx) in enumerate(fixtures, start=1):
        out = tmp_path / f"trial_{idx}.syx"
        build_syx_from_events(events_yaml=events_yaml, output_file=out, template_file=template_syx)
        assert out.read_bytes() == expected_syx.read_bytes()


@pytest.mark.parametrize(
    ("name", "template_syx", "reference_syx"),
    [
        (
            "BAAAAAAAAAAAAAAA",
            Path("captures/Pattern_Name_History/01_BASE_16A.syx"),
            Path("captures/Pattern_Name_History/02_POS01_B.syx"),
        ),
        (
            "INTRO",
            Path("captures/Pattern_Name_Length_Padding_Practical/001_CASE_001.syx"),
            Path("captures/Pattern_Name_Length_Padding_Practical/011_CASE_011.syx"),
        ),
        (
            "BLUE MOON A",
            Path("captures/Pattern_Name_Length_Padding_Practical/001_CASE_001.syx"),
            Path("captures/Pattern_Name_Length_Padding_Practical/020_CASE_020.syx"),
        ),
        (
            "\u00c5NGSTR\u00d6M",
            Path("captures/Pattern_Name_Length_Padding_Practical/001_CASE_001.syx"),
            Path("captures/Pattern_Name_Length_Padding_Practical/025_CASE_025.syx"),
        ),
    ],
)
def test_pattern_name_capture_region_regression(
    tmp_path: Path,
    name: str,
    template_syx: Path,
    reference_syx: Path,
):
    events = tmp_path / "events_name_regression.yaml"
    _write_events_yaml(
        events,
        "version: 1\n"
        "device: digitone2\n"
        f"name: {name}\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1\n"
        "  total_steps: 16\n"
        "events: []\n",
    )

    output = tmp_path / "name_regression.syx"
    build_syx_from_events(events_yaml=events, output_file=output, template_file=template_syx)

    built = output.read_bytes()
    reference = reference_syx.read_bytes()

    built_primary, built_shadow = _decode_pattern_name_fields(built)
    ref_primary, ref_shadow = _decode_pattern_name_fields(reference)
    assert built_primary == ref_primary
    assert built_shadow == ref_shadow

    for offset in sorted(_pattern_name_packed_offsets()):
        assert built[offset] == reference[offset]
