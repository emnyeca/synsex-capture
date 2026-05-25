from pathlib import Path

from digitone_syx_toolkit.digitone2.constants import CHECKSUM_SUM_END, CHECKSUM_SUM_START
from digitone_syx_toolkit.digitone2.packing import repack_7bit_region, unpack_7bit_region
from digitone_syx_toolkit.digitone2.step_state import (
    normal_trigger_step_state,
    step_state_logical_offset,
    write_normal_trigger_step_state,
)


def _changed_offsets(before: bytes, after: bytes) -> set[int]:
    return {idx for idx, (b1, b2) in enumerate(zip(before, after)) if b1 != b2}


def test_step_state_logical_offset_formula():
    assert step_state_logical_offset(1, 1) == 4
    assert step_state_logical_offset(2, 17) == 1223
    assert step_state_logical_offset(8, 128) == 8567


def test_normal_trigger_step_state_odd_even():
    assert normal_trigger_step_state(17) == bytes([0x03, 0x81])
    assert normal_trigger_step_state(128) == bytes([0x03, 0x91])


def test_pack_unpack_round_trip_for_base_empty():
    raw = bytearray(Path("captures/BASE_EMPTY.syx").read_bytes())
    original = bytes(raw)
    decoded = unpack_7bit_region(raw, start=CHECKSUM_SUM_START, end_exclusive=CHECKSUM_SUM_END)
    repack_7bit_region(
        raw,
        start=CHECKSUM_SUM_START,
        end_exclusive=CHECKSUM_SUM_END,
        decoded_payload=decoded,
    )
    assert bytes(raw) == original


def test_write_step_state_sets_expected_decoded_values_for_boundaries():
    raw = bytearray(Path("captures/BASE_EMPTY_STEPS128.syx").read_bytes())
    decoded = unpack_7bit_region(raw, start=CHECKSUM_SUM_START, end_exclusive=CHECKSUM_SUM_END)

    for step in (16, 17, 127, 128):
        write_normal_trigger_step_state(decoded, 2, step)

    assert decoded[step_state_logical_offset(2, 16) : step_state_logical_offset(2, 16) + 2] == bytes([0x03, 0x91])
    assert decoded[step_state_logical_offset(2, 17) : step_state_logical_offset(2, 17) + 2] == bytes([0x03, 0x81])
    assert decoded[step_state_logical_offset(2, 127) : step_state_logical_offset(2, 127) + 2] == bytes([0x03, 0x81])
    assert decoded[step_state_logical_offset(2, 128) : step_state_logical_offset(2, 128) + 2] == bytes([0x03, 0x91])


def test_step_state_boundary_changes_include_expected_control_offsets(tmp_path: Path):
    from digitone_syx_toolkit.events_to_syx import build_syx_from_events

    def build_for_step(step: int) -> bytes:
        events_yaml = tmp_path / f"step_{step}.yaml"
        events_yaml.write_text(
            "version: 1\n"
            "device: digitone2\n"
            "pattern:\n"
            "  mode: pattern-wide\n"
            "  tempo: 120\n"
            "  speed: 1\n"
            "  total_steps: 128\n"
            "events:\n"
            f"  - track: 2\n"
            f"    step: {step}\n"
            "    note: C5\n"
            "    velocity: inherit\n"
            "    length: inherit\n",
            encoding="utf-8",
        )
        out = tmp_path / f"step_{step}.syx"
        build_syx_from_events(events_yaml=events_yaml, output_file=out, template_file=Path("captures/BASE_EMPTY_STEPS128.syx"))
        return out.read_bytes()

    base = Path("captures/BASE_EMPTY_STEPS128.syx").read_bytes()

    changed_16 = _changed_offsets(base, build_for_step(16))
    changed_17 = _changed_offsets(base, build_for_step(17))
    changed_127 = _changed_offsets(base, build_for_step(127))
    changed_128 = _changed_offsets(base, build_for_step(128))

    assert {1402, 1406, 1407}.issubset(changed_16)
    assert {1402, 1408, 1409}.issubset(changed_17)
    assert {1658, 1660, 1661}.issubset(changed_127)
    assert {1658, 1662, 1663}.issubset(changed_128)
