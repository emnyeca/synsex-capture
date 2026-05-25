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


def test_load_event_assignment_yaml_rejects_track_defaults_section(tmp_path: Path):
    yaml_path = tmp_path / "events_tracks.yaml"
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
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="tracks"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_track_9(tmp_path: Path):
    yaml_path = tmp_path / "events_track9.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 64\n"
        "events:\n"
        "  - step: 1\n"
        "    track: 9\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="track must be 1..8"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_step_129(tmp_path: Path):
    yaml_path = tmp_path / "events_step129.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 128\n"
        "events:\n"
        "  - step: 129\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="out of range"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_step_over_total_steps(tmp_path: Path):
    yaml_path = tmp_path / "events_over_total.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events:\n"
        "  - step: 17\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="1..16"):
        load_event_assignment_yaml(yaml_path)
