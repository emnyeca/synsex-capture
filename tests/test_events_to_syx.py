from pathlib import Path

import pytest

from digitone_syx_toolkit.errors import SyxFileError
from digitone_syx_toolkit.events_to_syx import build_syx_from_events


def test_build_syx_from_events_writes_expected_bytes(tmp_path: Path):
    template = tmp_path / "template.syx"
    template.write_bytes(Path("captures/BASE_EMPTY.syx").read_bytes())

    events = tmp_path / "events.yaml"
    events.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 126\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "tracks:\n"
        "  - track: 1\n"
        "    default_velocity: 100\n"
        "    default_length: '1'\n"
        "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: 100\n"
        "    length: '2'\n",
        encoding="utf-8",
    )

    output = tmp_path / "out.syx"
    result = build_syx_from_events(
        events_yaml=events,
        output_file=output,
        template_file=template,
    )

    built = output.read_bytes()
    assert result.written_events == 1
    assert built[101511] == 0x00
    assert built[101512] == 0x06
    assert built[1333] == 100
    assert built[1334] == 0x0E
    # Slot1 pitch/velocity/length for C5/100/2
    assert built[21723] == 60
    assert built[21724] == 100
    assert built[21725] == 0x1E

    expected_cs = sum(built[10:114113]) % 16384
    assert built[114113] == ((expected_cs >> 7) & 0x7F)
    assert built[114114] == (expected_cs & 0x7F)


def test_build_syx_from_events_rejects_duplicate_step_track(tmp_path: Path):
    template = tmp_path / "template.syx"
    template.write_bytes(Path("captures/BASE_EMPTY.syx").read_bytes())

    events = tmp_path / "events_bad.yaml"
    events.write_text(
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
        "    velocity: 100\n"
        "    length: '1'\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: D5\n"
        "    velocity: 100\n"
        "    length: '1'\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError):
        build_syx_from_events(
            events_yaml=events,
            output_file=tmp_path / "out.syx",
            template_file=template,
        )
