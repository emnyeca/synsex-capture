from pathlib import Path

import pytest

from digitone_syx_toolkit.errors import SyxFileError
from digitone_syx_toolkit.events_to_syx import build_syx_from_events, export_missing_slots_template


def test_build_syx_from_events_writes_expected_bytes(tmp_path: Path):
    template = tmp_path / "template.syx"
    template.write_bytes(bytes([0xF0] + [0x00] * 114114 + [0xF7]))

    events = tmp_path / "events.yaml"
    events.write_text(
        "version: 1\n"
        "pattern:\n"
        "  length_steps: 16\n"
        "steps:\n"
        "  - step: 1\n"
        "    events:\n"
        "      - track: 0\n"
        "        note: C4\n"
        "        duration: 2\n",
        encoding="utf-8",
    )

    profile = tmp_path / "profile.yaml"
    profile.write_text(
        "version: 1\n"
        "defaults:\n"
        "  velocity: 100\n"
        "track_base: zero_based\n"
        "length_codes:\n"
        "  \"1\": 0x7F\n"
        "  \"2\": 0x1E\n"
        "pattern_length:\n"
        "  offset: 20\n"
        "  encoding: wrap128\n"
        "slots:\n"
        "  - step: 1\n"
        "    track: 0\n"
        "    offset_step: 10\n"
        "    offset_track: 11\n"
        "    offset_note: 12\n"
        "    offset_velocity: 13\n"
        "    offset_length: 14\n",
        encoding="utf-8",
    )

    output = tmp_path / "out.syx"
    result = build_syx_from_events(
        template_file=template,
        events_yaml=events,
        profile_yaml=profile,
        output_file=output,
    )

    built = output.read_bytes()
    assert result.written_events == 1
    assert built[10] == 0  # step-1
    assert built[11] == 0  # track 0
    assert built[12] == 60  # C4
    assert built[13] == 100
    assert built[14] == 0x1E
    assert built[20] == 16
    # Checksum is auto-recomputed for Digitone II offsets.
    expected_cs = sum(built[10:114113]) % 16384
    assert built[114113] == ((expected_cs >> 7) & 0x7F)
    assert built[114114] == (expected_cs & 0x7F)


def test_build_syx_from_events_missing_slot_raises(tmp_path: Path):
    template = tmp_path / "template.syx"
    template.write_bytes(bytes([0xF0] + [0x00] * 30 + [0xF7]))

    events = tmp_path / "events.yaml"
    events.write_text(
        "version: 1\n"
        "pattern:\n"
        "  length_steps: 16\n"
        "steps:\n"
        "  - step: 1\n"
        "    events:\n"
        "      - track: 2\n"
        "        note: C4\n"
        "        duration: 1\n",
        encoding="utf-8",
    )

    profile = tmp_path / "profile.yaml"
    profile.write_text(
        "version: 1\n"
        "defaults:\n"
        "  velocity: 100\n"
        "track_base: zero_based\n"
        "length_codes:\n"
        "  \"1\": 0x7F\n"
        "pattern_length:\n"
        "  encoding: raw\n"
        "slots:\n"
        "  - step: 1\n"
        "    track: 0\n"
        "    offset_step: 10\n"
        "    offset_track: 11\n"
        "    offset_note: 12\n"
        "    offset_velocity: 13\n"
        "    offset_length: 14\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError):
        build_syx_from_events(
            template_file=template,
            events_yaml=events,
            profile_yaml=profile,
            output_file=tmp_path / "out.syx",
        )


def test_export_missing_slots_template(tmp_path: Path):
    events = tmp_path / "events.yaml"
    events.write_text(
        "version: 1\n"
        "pattern:\n"
        "  length_steps: 16\n"
        "steps:\n"
        "  - step: 1\n"
        "    events:\n"
        "      - track: 0\n"
        "        note: C4\n"
        "        duration: 1\n"
        "      - track: 2\n"
        "        note: E4\n"
        "        duration: 1\n",
        encoding="utf-8",
    )

    profile = tmp_path / "profile.yaml"
    profile.write_text(
        "version: 1\n"
        "defaults:\n"
        "  velocity: 100\n"
        "track_base: zero_based\n"
        "length_codes:\n"
        "  \"1\": 0x7F\n"
        "pattern_length:\n"
        "  encoding: raw\n"
        "slots:\n"
        "  - step: 1\n"
        "    track: 0\n"
        "    offset_step: 10\n"
        "    offset_track: 11\n"
        "    offset_note: 12\n"
        "    offset_velocity: 13\n"
        "    offset_length: 14\n",
        encoding="utf-8",
    )

    out = tmp_path / "missing.yaml"
    export_missing_slots_template(events_yaml=events, profile_yaml=profile, output_yaml=out)

    text = out.read_text(encoding="utf-8")
    assert "missing_count: 1" in text
    assert "step: 1" in text
    assert "track: 2" in text
