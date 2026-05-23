"""Build a .syx file from validated events YAML and an offset mapping profile.

This path is intentionally explicit: all writable offsets are provided by profile YAML.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import SyxFileError
from .events_yaml import EventAssignment, load_event_assignment_yaml


DEFAULT_DIGITONE2_PROFILE = (
    Path(__file__).resolve().parents[2] / "profiles" / "digitone2.default.yaml"
)
_DIGITONE2_CHECKSUM_HI_OFFSET = 114113
_DIGITONE2_CHECKSUM_LO_OFFSET = 114114
_DIGITONE2_CHECKSUM_SUM_START = 10
_DIGITONE2_CHECKSUM_SUM_END = 114113


@dataclass(frozen=True)
class SlotOffset:
    step: int
    track: int
    offset_step: int
    offset_track: int
    offset_note: int
    offset_velocity: int
    offset_length: int


@dataclass(frozen=True)
class PatternLengthMapping:
    offset: int | None
    encoding: str


@dataclass(frozen=True)
class EventsToSyxProfile:
    version: int
    default_velocity: int
    track_base: str
    length_codes: dict[int, int]
    slots: tuple[SlotOffset, ...]
    pattern_length: PatternLengthMapping


@dataclass(frozen=True)
class BuildResult:
    output_file: Path
    written_events: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ProfileCoverage:
    required_pairs: tuple[tuple[int, int], ...]
    mapped_pairs: tuple[tuple[int, int], ...]
    missing_pairs: tuple[tuple[int, int], ...]


def _to_int(value: object, field: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        try:
            return int(text, 16) if text.lower().startswith("0x") else int(text)
        except ValueError as exc:
            raise SyxFileError(f"{field} must be int or int-like string: {value}") from exc
    raise SyxFileError(f"{field} must be int or string, got {type(value)}")


def _set_byte(mutable: bytearray, offset: int, value: int, field: str) -> None:
    if offset < 0 or offset >= len(mutable):
        raise SyxFileError(f"{field} offset out of range: {offset} (file length={len(mutable)})")
    if value < 0 or value > 0xFF:
        raise SyxFileError(f"{field} value out of byte range: {value}")
    mutable[offset] = value


def _load_profile(path: str | Path) -> EventsToSyxProfile:
    src = Path(path)
    if not src.exists():
        raise SyxFileError(f"Profile YAML not found: {src}")

    payload = yaml.safe_load(src.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SyxFileError("Profile YAML must be a mapping.")

    version = _to_int(payload.get("version", 1), "profile.version")
    if version != 1:
        raise SyxFileError(f"Unsupported profile version: {version}")

    defaults = payload.get("defaults")
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        raise SyxFileError("profile.defaults must be a mapping")
    default_velocity = _to_int(defaults.get("velocity", 100), "profile.defaults.velocity")
    if default_velocity < 1 or default_velocity > 127:
        raise SyxFileError("profile.defaults.velocity must be 1..127")

    track_base = str(payload.get("track_base", "zero_based")).strip().lower()
    if track_base not in {"zero_based", "one_based"}:
        raise SyxFileError("profile.track_base must be zero_based or one_based")

    raw_length_codes = payload.get("length_codes")
    if not isinstance(raw_length_codes, dict):
        raise SyxFileError("profile.length_codes must be a mapping")
    length_codes: dict[int, int] = {}
    for key, val in raw_length_codes.items():
        dur = _to_int(key, "profile.length_codes key")
        code = _to_int(val, f"profile.length_codes[{key}]")
        if dur < 1:
            raise SyxFileError("profile.length_codes duration key must be >=1")
        if code < 0 or code > 0xFF:
            raise SyxFileError("profile.length_codes value must be 0..255")
        length_codes[dur] = code

    raw_slots = payload.get("slots")
    if not isinstance(raw_slots, list) or not raw_slots:
        raise SyxFileError("profile.slots must be a non-empty list")

    slots: list[SlotOffset] = []
    seen: set[tuple[int, int]] = set()
    for item in raw_slots:
        if not isinstance(item, dict):
            raise SyxFileError("profile.slots entries must be mappings")

        slot = SlotOffset(
            step=_to_int(item.get("step"), "slot.step"),
            track=_to_int(item.get("track"), "slot.track"),
            offset_step=_to_int(item.get("offset_step"), "slot.offset_step"),
            offset_track=_to_int(item.get("offset_track"), "slot.offset_track"),
            offset_note=_to_int(item.get("offset_note"), "slot.offset_note"),
            offset_velocity=_to_int(item.get("offset_velocity"), "slot.offset_velocity"),
            offset_length=_to_int(item.get("offset_length"), "slot.offset_length"),
        )

        if slot.track < 0 or slot.track > 6:
            raise SyxFileError(f"slot track out of range: {slot.track}")

        key = (slot.step, slot.track)
        if key in seen:
            raise SyxFileError(f"duplicate slot mapping for step={slot.step} track={slot.track}")
        seen.add(key)
        slots.append(slot)

    pattern = payload.get("pattern_length") or {}
    if not isinstance(pattern, dict):
        raise SyxFileError("profile.pattern_length must be a mapping")

    pl_offset = pattern.get("offset")
    pattern_length = PatternLengthMapping(
        offset=_to_int(pl_offset, "profile.pattern_length.offset") if pl_offset is not None else None,
        encoding=str(pattern.get("encoding", "raw")).strip().lower(),
    )
    if pattern_length.encoding not in {"raw", "wrap128"}:
        raise SyxFileError("profile.pattern_length.encoding must be raw or wrap128")

    return EventsToSyxProfile(
        version=version,
        default_velocity=default_velocity,
        track_base=track_base,
        length_codes=length_codes,
        slots=tuple(slots),
        pattern_length=pattern_length,
    )


def resolve_profile_path(profile_yaml: str | Path | None = None) -> Path:
    """Resolve profile path, defaulting to bundled Digitone II profile."""
    candidate = Path(profile_yaml) if profile_yaml else DEFAULT_DIGITONE2_PROFILE
    if not candidate.exists():
        raise SyxFileError(
            f"Profile YAML not found: {candidate}. "
            "Provide --profile or create the default profile file."
        )
    return candidate


def _length_code(duration: int, length_codes: dict[int, int]) -> tuple[int, str | None]:
    if duration in length_codes:
        return length_codes[duration], None

    known = sorted(length_codes)
    if not known:
        raise SyxFileError("profile.length_codes is empty")

    fallback = max((d for d in known if d <= duration), default=known[0])
    warning = f"duration={duration} not mapped; fallback to nearest lower duration={fallback}"
    return length_codes[fallback], warning


def _pattern_length_code(length_steps: int, encoding: str) -> int:
    if encoding == "wrap128":
        return length_steps % 128
    return length_steps


def _recompute_digitone2_checksum(data: bytearray) -> None:
    if len(data) <= _DIGITONE2_CHECKSUM_LO_OFFSET:
        raise SyxFileError(
            "File is too short to contain Digitone II checksum bytes "
            f"({_DIGITONE2_CHECKSUM_HI_OFFSET}, {_DIGITONE2_CHECKSUM_LO_OFFSET})."
        )
    checksum = sum(data[_DIGITONE2_CHECKSUM_SUM_START:_DIGITONE2_CHECKSUM_SUM_END]) % 16384
    data[_DIGITONE2_CHECKSUM_HI_OFFSET] = (checksum >> 7) & 0x7F
    data[_DIGITONE2_CHECKSUM_LO_OFFSET] = checksum & 0x7F


def check_profile_coverage(
    *,
    events_yaml: str | Path,
    profile_yaml: str | Path | None = None,
) -> ProfileCoverage:
    """Check whether profile has slot mappings for all non-hold event pairs."""
    assignment: EventAssignment = load_event_assignment_yaml(events_yaml)
    profile = _load_profile(resolve_profile_path(profile_yaml))

    required: set[tuple[int, int]] = set()
    for step in assignment.steps:
        if step.hold:
            continue
        for event in step.events:
            required.add((step.step, event.track))

    mapped = {(slot.step, slot.track) for slot in profile.slots}
    missing = sorted(required - mapped)
    used = sorted(required & mapped)

    return ProfileCoverage(
        required_pairs=tuple(sorted(required)),
        mapped_pairs=tuple(used),
        missing_pairs=tuple(missing),
    )


def export_missing_slots_template(
    *,
    events_yaml: str | Path,
    profile_yaml: str | Path | None = None,
    output_yaml: str | Path,
) -> Path:
    """Export missing (step,track) pairs as a profile-fill template YAML."""
    resolved_profile = resolve_profile_path(profile_yaml)
    coverage = check_profile_coverage(events_yaml=events_yaml, profile_yaml=resolved_profile)

    payload = {
        "version": 1,
        "source_events": str(Path(events_yaml)),
        "source_profile": str(resolved_profile),
        "missing_count": len(coverage.missing_pairs),
        "missing_slots": [
            {
                "step": step,
                "track": track,
                "offset_step": None,
                "offset_track": None,
                "offset_note": None,
                "offset_velocity": None,
                "offset_length": None,
            }
            for step, track in coverage.missing_pairs
        ],
        "notes": [
            "Fill offsets for each missing slot and copy into profiles/digitone2.default.yaml slots.",
            "Use existing capture/diff workflow to identify offsets per step/track.",
        ],
    }

    out = Path(output_yaml)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return out


def build_syx_from_events(
    *,
    template_file: str | Path,
    events_yaml: str | Path,
    profile_yaml: str | Path | None = None,
    output_file: str | Path,
) -> BuildResult:
    """Build output .syx by writing event bytes using profile-defined offsets."""
    template_path = Path(template_file)
    if not template_path.exists():
        raise SyxFileError(f"Template .syx not found: {template_path}")

    assignment: EventAssignment = load_event_assignment_yaml(events_yaml)
    resolved_profile = resolve_profile_path(profile_yaml)
    profile = _load_profile(resolved_profile)

    coverage = check_profile_coverage(events_yaml=events_yaml, profile_yaml=resolved_profile)
    if coverage.missing_pairs:
        preview = ", ".join(f"({s},{t})" for s, t in coverage.missing_pairs[:12])
        more = "" if len(coverage.missing_pairs) <= 12 else f" ... +{len(coverage.missing_pairs) - 12} more"
        raise SyxFileError(
            "Missing slot mappings in profile.slots. "
            f"Missing pairs: {preview}{more}."
        )

    data = bytearray(template_path.read_bytes())
    slot_map = {(slot.step, slot.track): slot for slot in profile.slots}
    warnings: list[str] = []
    written = 0

    if profile.pattern_length.offset is not None:
        pl_code = _pattern_length_code(assignment.length_steps, profile.pattern_length.encoding)
        _set_byte(data, profile.pattern_length.offset, pl_code, "pattern_length")

    for step in assignment.steps:
        if step.hold:
            continue

        for event in step.events:
            key = (step.step, event.track)
            slot = slot_map.get(key)
            if slot is None:
                raise SyxFileError(
                    f"No slot mapping for step={step.step}, track={event.track}. "
                    "Add this pair to profile.slots."
                )

            track_value = event.track if profile.track_base == "zero_based" else event.track + 1
            velocity = event.velocity if event.velocity is not None else profile.default_velocity

            length_code, length_warning = _length_code(event.duration, profile.length_codes)
            if length_warning:
                warnings.append(f"step={step.step} track={event.track}: {length_warning}")

            _set_byte(data, slot.offset_step, step.step - 1, "slot.offset_step")
            _set_byte(data, slot.offset_track, track_value, "slot.offset_track")
            _set_byte(data, slot.offset_note, event.note_midi, "slot.offset_note")
            _set_byte(data, slot.offset_velocity, velocity, "slot.offset_velocity")
            _set_byte(data, slot.offset_length, length_code, "slot.offset_length")
            written += 1

    _recompute_digitone2_checksum(data)

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(bytes(data))

    return BuildResult(
        output_file=out_path,
        written_events=written,
        warnings=tuple(warnings),
    )
