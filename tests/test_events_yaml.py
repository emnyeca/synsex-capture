from pathlib import Path

import pytest

from digitone_syx_toolkit.errors import SyxFileError
from digitone_syx_toolkit.events_yaml import load_event_assignment_yaml


def test_load_event_assignment_yaml_valid(tmp_path: Path):
    yaml_path = tmp_path / "events.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "name: test\n"
        "pattern:\n"
        "  length_steps: 16\n"
        "  speed: 1/8\n"
        "  time_signature: 4/4\n"
        "steps:\n"
        "  - step: 1\n"
        "    chord: Cmaj7\n"
        "    events:\n"
        "      - track: 0\n"
        "        note: C4\n"
        "        duration: 2\n"
        "        velocity: 100\n"
        "  - step: 16\n"
        "    chord: Cmaj7\n"
        "    hold: true\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.length_steps == 16
    assert len(parsed.steps) == 2
    assert parsed.steps[0].events[0].note_midi == 60
    assert parsed.steps[0].events[0].velocity == 100
    assert parsed.steps[1].hold is True


def test_load_event_assignment_yaml_rejects_hold_and_events(tmp_path: Path):
    yaml_path = tmp_path / "events_bad.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "pattern:\n"
        "  length_steps: 16\n"
        "steps:\n"
        "  - step: 1\n"
        "    hold: true\n"
        "    events:\n"
        "      - track: 0\n"
        "        note: C4\n"
        "        duration: 1\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_duplicate_track(tmp_path: Path):
    yaml_path = tmp_path / "events_dup.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "pattern:\n"
        "  length_steps: 4\n"
        "steps:\n"
        "  - step: 1\n"
        "    events:\n"
        "      - track: 0\n"
        "        note: C4\n"
        "        duration: 1\n"
        "      - track: 0\n"
        "        note: E4\n"
        "        duration: 1\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError):
        load_event_assignment_yaml(yaml_path)
