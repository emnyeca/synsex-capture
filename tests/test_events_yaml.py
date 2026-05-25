from pathlib import Path

import pytest

from digitone_syx_toolkit.errors import SyxFileError
from digitone_syx_toolkit.events_yaml import load_event_assignment_yaml


def test_load_event_assignment_yaml_valid(tmp_path: Path):
    yaml_path = tmp_path / "events.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "name: test\n"
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
        "    velocity: inherit\n"
        "    length: inherit\n"
        "  - step: 2\n"
        "    track: 2\n"
        "    note: D5\n"
        "    velocity: 88\n"
        "    length: '2'\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.pattern.total_steps == 16
    assert len(parsed.events) == 2
    assert parsed.events[0].note_midi == 60
    assert parsed.events[0].velocity == "inherit"
    assert parsed.events[0].length == "inherit"


def test_load_event_assignment_yaml_rejects_duplicate_step_track(tmp_path: Path):
    yaml_path = tmp_path / "events_bad.yaml"
    yaml_path.write_text(
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
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_duplicate_track(tmp_path: Path):
    yaml_path = tmp_path / "events_dup.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 4\n"
        "tracks:\n"
        "  - track: 1\n"
        "    default_velocity: 100\n"
        "    default_length: '1'\n"
        "  - track: 1\n"
        "    default_velocity: 110\n"
        "    default_length: '2'\n"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError):
        load_event_assignment_yaml(yaml_path)
