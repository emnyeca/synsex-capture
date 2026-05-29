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
    assert parsed.name == "TEST"
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


def test_load_event_assignment_yaml_accepts_track_default_velocity_map(tmp_path: Path):
    yaml_path = tmp_path / "events_track_defaults.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "track_defaults:\n"
        "  velocity:\n"
        "    1: 50\n"
        "    3: 70\n"
        "events: []\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.track_default_velocity == {1: 50, 3: 70}


def test_load_event_assignment_yaml_rejects_track_default_velocity_out_of_range(tmp_path: Path):
    yaml_path = tmp_path / "events_track_defaults_bad.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "track_defaults:\n"
        "  velocity:\n"
        "    1: 0\n"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="1..127"):
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


def test_load_event_assignment_yaml_accepts_length_code_hex(tmp_path: Path):
    yaml_path = tmp_path / "events_length_code.yaml"
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
        "    length_code: \"0x26\"\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.events[0].length_code == 0x26


def test_load_event_assignment_yaml_accepts_length_mapping_code(tmp_path: Path):
    yaml_path = tmp_path / "events_length_mapping.yaml"
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
        "    length:\n"
        "      code: \"0x7F\"\n"
        "      display: \"INF\"\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.events[0].length_code == 0x7F


def test_load_event_assignment_yaml_rejects_length_code_over_0x7f(tmp_path: Path):
    yaml_path = tmp_path / "events_length_code_bad.yaml"
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
        "    length_code: \"0x80\"\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="out of range"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_accepts_all_explicit_length_codes(tmp_path: Path):
    events = "".join(
        (
            "  - step: 1\n"
            "    track: 1\n"
            "    note: C5\n"
            "    velocity: inherit\n"
            f"    length_code: \"0x{code:02X}\"\n"
        )
        for code in range(0x80)
    )
    # only one event per file due duplicate-step-track constraint
    for code in range(0x80):
        yaml_path = tmp_path / f"events_code_{code:02X}.yaml"
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
            f"    length_code: \"0x{code:02X}\"\n",
            encoding="utf-8",
        )
        parsed = load_event_assignment_yaml(yaml_path)
        assert parsed.events[0].length_code == code


def test_load_event_assignment_yaml_normalizes_pattern_name_ascii_case(tmp_path: Path):
    yaml_path = tmp_path / "events_name_normalized.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "name: Blue Moon A\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events: []\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.name == "BLUE MOON A"


def test_load_event_assignment_yaml_keeps_beta_sharp_character(tmp_path: Path):
    yaml_path = tmp_path / "events_name_beta.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "name: ß\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events: []\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.name == "ß"


def test_load_event_assignment_yaml_truncates_pattern_name_over_16_chars(tmp_path: Path):
    yaml_path = tmp_path / "events_name_too_long.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "name: BLUE MOON SOLO FORM\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events: []\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.name == "BLUE MOON SOLO F"


def test_load_event_assignment_yaml_rejects_unsupported_char_after_16th(tmp_path: Path):
    yaml_path = tmp_path / "events_name_bad_after_16.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "name: ABCDEFGHIJKLMNOP/\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="Unsupported pattern name character"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_pattern_name_unsupported_char(tmp_path: Path):
    yaml_path = tmp_path / "events_name_bad_char.yaml"
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "name: THEME/A\n"
        "pattern:\n"
        "  mode: pattern-wide\n"
        "  tempo: 120\n"
        "  speed: 1/8\n"
        "  total_steps: 16\n"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="Unsupported pattern name character"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_accepts_per_track_mode(tmp_path: Path):
    yaml_path = tmp_path / "events_per_track.yaml"
    track_scale = "".join(
        f"  {track}: {{length: 32, speed: '1/8'}}\n" for track in range(1, 17)
    )
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: OFF\n"
        "  reset: INF\n"
        "track_scale:\n"
        f"{track_scale}"
        "events:\n"
        "  - step: 1\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.pattern.mode == "per-track"
    assert parsed.pattern.change == "OFF"
    assert parsed.pattern.reset == "INF"
    assert len(parsed.track_scale) == 16
    assert parsed.track_scale[16].length == 32
    assert parsed.track_scale[16].speed == "1/8"


def test_load_event_assignment_yaml_rejects_per_track_missing_track16(tmp_path: Path):
    yaml_path = tmp_path / "events_per_track_missing.yaml"
    track_scale = "".join(
        f"  {track}: {{length: 32, speed: '1/8'}}\n" for track in range(1, 16)
    )
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: OFF\n"
        "  reset: INF\n"
        "track_scale:\n"
        f"{track_scale}"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="exactly tracks 1..16"):
        load_event_assignment_yaml(yaml_path)


@pytest.mark.parametrize("length", [1, 129])
def test_load_event_assignment_yaml_rejects_per_track_length_out_of_range(tmp_path: Path, length: int):
    yaml_path = tmp_path / "events_per_track_length_bad.yaml"
    track_scale = "".join(
        f"  {track}: {{length: {length if track == 16 else 32}, speed: '1/8'}}\n" for track in range(1, 17)
    )
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: OFF\n"
        "  reset: INF\n"
        "track_scale:\n"
        f"{track_scale}"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="track_scale\[16\].length must be in 2..128"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_per_track_invalid_speed(tmp_path: Path):
    yaml_path = tmp_path / "events_per_track_speed_bad.yaml"
    track_scale = "".join(
        f"  {track}: {{length: 32, speed: {'3' if track == 16 else "'1/8'"}}}\n" for track in range(1, 17)
    )
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: OFF\n"
        "  reset: INF\n"
        "track_scale:\n"
        f"{track_scale}"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="track_scale\[16\].speed"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_per_track_change_other_than_off(tmp_path: Path):
    yaml_path = tmp_path / "events_per_track_change_bad.yaml"
    track_scale = "".join(
        f"  {track}: {{length: 32, speed: '1/8'}}\n" for track in range(1, 17)
    )
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: 2\n"
        "  reset: INF\n"
        "track_scale:\n"
        f"{track_scale}"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="pattern.change must be OFF"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_per_track_reset_other_than_inf(tmp_path: Path):
    yaml_path = tmp_path / "events_per_track_reset_bad.yaml"
    track_scale = "".join(
        f"  {track}: {{length: 32, speed: '1/8'}}\n" for track in range(1, 17)
    )
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: OFF\n"
        "  reset: 16\n"
        "track_scale:\n"
        f"{track_scale}"
        "events: []\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="pattern.reset must be INF"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_rejects_per_track_event_past_own_track_length(tmp_path: Path):
    yaml_path = tmp_path / "events_per_track_step_bad.yaml"
    track_scale = "".join(
        f"  {track}: {{length: {4 if track == 1 else 32}, speed: '1/8'}}\n" for track in range(1, 17)
    )
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: OFF\n"
        "  reset: INF\n"
        "track_scale:\n"
        f"{track_scale}"
        "events:\n"
        "  - step: 5\n"
        "    track: 1\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
        encoding="utf-8",
    )

    with pytest.raises(SyxFileError, match="1..4"):
        load_event_assignment_yaml(yaml_path)


def test_load_event_assignment_yaml_accepts_per_track_entries_for_tracks_9_to_16(tmp_path: Path):
    yaml_path = tmp_path / "events_per_track_upper_tracks.yaml"
    track_scale = "".join(
        f"  {track}: {{length: {48 if track == 16 else 32}, speed: {'"1/2"' if track >= 9 else '"1/8"'}}}\n"
        for track in range(1, 17)
    )
    yaml_path.write_text(
        "version: 1\n"
        "device: digitone2\n"
        "pattern:\n"
        "  mode: per-track\n"
        "  tempo: 120\n"
        "  change: OFF\n"
        "  reset: INF\n"
        "track_scale:\n"
        f"{track_scale}"
        "events:\n"
        "  - step: 32\n"
        "    track: 8\n"
        "    note: C5\n"
        "    velocity: inherit\n"
        "    length: inherit\n",
        encoding="utf-8",
    )

    parsed = load_event_assignment_yaml(yaml_path)
    assert parsed.track_scale[9].speed == "1/2"
    assert parsed.track_scale[16].length == 48
