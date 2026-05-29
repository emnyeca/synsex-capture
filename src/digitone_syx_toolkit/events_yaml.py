"""Validation and parsing for Digitone II focused events YAML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .digitone2.constants import DISPLAY_TO_EXPLICIT_LENGTH_CODE, LENGTH_CODE_MAP
from .digitone2.length_codes import parse_length_code
from .digitone2.micro_timing import encode_micro_timing
from .digitone2.pattern_name import PATTERN_NAME_MAX_CHARS, normalize_pattern_name, validate_pattern_name
from .errors import SyxFileError


_NOTE_BASE = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


@dataclass(frozen=True)
class EventItem:
    step: int
    track: int
    note: str
    note_midi: int
    velocity: int | str
    length: str
    length_code: int | None = None
    time: int = 0


@dataclass(frozen=True)
class PatternSettings:
    mode: str
    tempo: float
    speed: str | None = None
    total_steps: int | None = None
    change: str | None = None
    reset: str | None = None


@dataclass(frozen=True)
class TrackScaleSettings:
    length: int
    speed: str


@dataclass(frozen=True)
class EventAssignment:
    version: int
    device: str
    name: str | None
    pattern: PatternSettings
    track_default_velocity: dict[int, int]
    track_scale: dict[int, TrackScaleSettings]
    events: tuple[EventItem, ...]


def _parse_note_name(note_name: str) -> int:
    text = note_name.strip()
    if len(text) < 2:
        raise SyxFileError(f"Invalid note format: {note_name}")

    root = text[0].upper()
    if root not in _NOTE_BASE:
        raise SyxFileError(f"Invalid note root: {note_name}")

    idx = 1
    accidental = 0
    if idx < len(text) and text[idx] in ("#", "b"):
        accidental = 1 if text[idx] == "#" else -1
        idx += 1

    octave_text = text[idx:]
    if not octave_text or octave_text == "+" or octave_text == "-":
        raise SyxFileError(f"Invalid note octave: {note_name}")

    try:
        octave = int(octave_text)
    except ValueError as exc:
        raise SyxFileError(f"Invalid note octave: {note_name}") from exc

    # Digitone display naming stores C5 as 60 in tested captures.
    midi = (octave + 1) * 12 + _NOTE_BASE[root] + accidental - 12
    if midi < 0 or midi > 127:
        raise SyxFileError(f"MIDI note out of range for {note_name}: {midi}")
    return midi


def _as_int(value: object, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SyxFileError(f"{field} must be an integer: {value}") from exc


def _parse_length_code_or_error(raw: object, field: str) -> int:
    try:
        return parse_length_code(raw)  # type: ignore[arg-type]
    except ValueError as exc:
        raise SyxFileError(f"{field}: {exc}") from exc


def _parse_speed(raw: object, field: str) -> str:
    speed = str(raw).strip()
    if speed not in {"2", "3/2", "1", "3/4", "1/2", "1/4", "1/8"}:
        raise SyxFileError(f"{field} must be one of: 2, 3/2, 1, 3/4, 1/2, 1/4, 1/8")
    return speed


def _parse_symbolic_text(raw: object, field: str) -> str:
    if isinstance(raw, bool):
        value = "ON" if raw else "OFF"
    else:
        value = str(raw).strip()
    if not value:
        raise SyxFileError(f"{field} is required")
    return value.upper()


def _parse_micro_timing(raw: object, field: str) -> int:
    value = _as_int(raw, field)
    encode_micro_timing(value)
    return value


def _load_yaml(path: str | Path) -> dict:
    src = Path(path)
    if not src.exists():
        raise SyxFileError(f"Events YAML not found: {src}")

    payload = yaml.safe_load(src.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SyxFileError("Events YAML must be a mapping.")
    return payload


def load_event_assignment_yaml(path: str | Path) -> EventAssignment:
    """Load and validate events YAML against the Digitone II v1 schema."""
    payload = _load_yaml(path)

    version = _as_int(payload.get("version", 1), "version")
    if version != 1:
        raise SyxFileError(f"Unsupported events schema version: {version}")

    name = payload.get("name")
    if name is not None:
        name = normalize_pattern_name(str(name))
        try:
            validate_pattern_name(name)
        except ValueError as exc:
            raise SyxFileError(str(exc)) from exc
        if len(name) > PATTERN_NAME_MAX_CHARS:
            name = name[:PATTERN_NAME_MAX_CHARS]

    device = str(payload.get("device", "digitone2")).strip().lower()
    if device != "digitone2":
        raise SyxFileError(f"Unsupported device: {device}. Expected digitone2")

    pattern = payload.get("pattern")
    if not isinstance(pattern, dict):
        raise SyxFileError("'pattern' must be a mapping.")

    mode = str(pattern.get("mode", "pattern-wide")).strip().lower()
    if mode in {"pattern-wide", "pattern_wide"}:
        canonical_mode = "pattern-wide"
    elif mode in {"per-track", "per_track"}:
        canonical_mode = "per-track"
    else:
        raise SyxFileError("pattern.mode must be 'pattern-wide' or 'per-track'")

    tempo = float(pattern.get("tempo", 120.0))
    if tempo < 30.0 or tempo > 300.0:
        raise SyxFileError("pattern.tempo must be in 30.0..300.0")

    speed: str | None = None
    total_steps: int | None = None
    change: str | None = None
    reset: str | None = None
    track_scale: dict[int, TrackScaleSettings] = {}

    if canonical_mode == "pattern-wide":
        speed = _parse_speed(pattern.get("speed", "1/8"), "pattern.speed")
        total_steps = _as_int(pattern.get("total_steps"), "pattern.total_steps")
        if total_steps < 2 or total_steps > 128:
            raise SyxFileError("pattern.total_steps must be in 2..128")
    else:
        change = _parse_symbolic_text(pattern.get("change", ""), "pattern.change")
        if change != "OFF":
            raise SyxFileError("pattern.change must be OFF in per-track mode")
        reset = _parse_symbolic_text(pattern.get("reset", ""), "pattern.reset")
        if reset != "INF":
            raise SyxFileError("pattern.reset must be INF in per-track mode")

        raw_track_scale = payload.get("track_scale")
        if not isinstance(raw_track_scale, dict):
            raise SyxFileError("'track_scale' must be a mapping in per-track mode")

        for raw_track, raw_settings in raw_track_scale.items():
            track = _as_int(raw_track, "track_scale track")
            if track < 1 or track > 16:
                raise SyxFileError(f"track_scale track must be 1..16: {track}")
            if not isinstance(raw_settings, dict):
                raise SyxFileError(f"track_scale[{track}] must be a mapping")
            length = _as_int(raw_settings.get("length"), f"track_scale[{track}].length")
            if length < 2 or length > 128:
                raise SyxFileError(f"track_scale[{track}].length must be in 2..128")
            track_speed = _parse_speed(raw_settings.get("speed"), f"track_scale[{track}].speed")
            track_scale[track] = TrackScaleSettings(length=length, speed=track_speed)

        expected_tracks = set(range(1, 17))
        actual_tracks = set(track_scale)
        if actual_tracks != expected_tracks:
            missing = sorted(expected_tracks - actual_tracks)
            extra = sorted(actual_tracks - expected_tracks)
            details: list[str] = []
            if missing:
                details.append(f"missing tracks {missing}")
            if extra:
                details.append(f"unexpected tracks {extra}")
            raise SyxFileError("track_scale must contain exactly tracks 1..16: " + ", ".join(details))

    raw_tracks = payload.get("tracks")
    if raw_tracks not in (None, []):
        raise SyxFileError(
            "'tracks' defaults rewrite is not supported in the current Digitone II encoder scope"
        )

    track_default_velocity: dict[int, int] = {}
    raw_track_defaults = payload.get("track_defaults")
    if raw_track_defaults is not None:
        if not isinstance(raw_track_defaults, dict):
            raise SyxFileError("'track_defaults' must be a mapping")
        raw_velocity_map = raw_track_defaults.get("velocity")
        if raw_velocity_map is None:
            raise SyxFileError("'track_defaults.velocity' is required when track_defaults is provided")
        if not isinstance(raw_velocity_map, dict):
            raise SyxFileError("'track_defaults.velocity' must be a mapping")

        for raw_track, raw_velocity in raw_velocity_map.items():
            track = _as_int(raw_track, "track_defaults.velocity track")
            if track < 1 or track > 8:
                raise SyxFileError(f"track_defaults.velocity track must be 1..8: {track}")
            velocity = _as_int(raw_velocity, f"track_defaults.velocity[{track}]")
            if velocity < 1 or velocity > 127:
                raise SyxFileError(f"track_defaults.velocity[{track}] must be 1..127")
            track_default_velocity[track] = velocity

    raw_events = payload.get("events")
    if not isinstance(raw_events, list):
        raise SyxFileError("'events' must be a list")

    parsed_events: list[EventItem] = []
    seen_pairs: dict[tuple[int, int], set[int]] = {}
    for raw_event in raw_events:
        if not isinstance(raw_event, dict):
            raise SyxFileError("events[] entries must be mappings")

        step = _as_int(raw_event.get("step"), "events[].step")
        track = _as_int(raw_event.get("track"), f"events[step={step}].track")
        if track < 1 or track > 8:
            raise SyxFileError(f"events step={step}: track must be 1..8")

        max_step = total_steps if canonical_mode == "pattern-wide" else track_scale[track].length
        if step < 1 or step > max_step:
            raise SyxFileError(f"events[].step out of range: {step} (1..{max_step})")

        note = str(raw_event.get("note", "")).strip()
        if not note:
            raise SyxFileError(f"events step={step} track={track}: note is required")
        note_midi = _parse_note_name(note)

        pair = (step, track)
        notes_for_pair = seen_pairs.setdefault(pair, set())
        if note_midi in notes_for_pair:
            raise SyxFileError(
                f"events step={step} track={track}: duplicate note {note} is not allowed"
            )
        if notes_for_pair and track != 8:
            raise SyxFileError(
                f"events step={step} track={track}: multiple notes on the same step are only supported on track 8"
            )
        notes_for_pair.add(note_midi)

        velocity_raw = raw_event.get("velocity", "inherit")
        if isinstance(velocity_raw, str) and velocity_raw.strip().lower() == "inherit":
            velocity: int | str = "inherit"
        else:
            velocity = _as_int(velocity_raw, f"events step={step} track={track} velocity")
            if velocity < 1 or velocity > 127:
                raise SyxFileError(f"events step={step} track={track}: velocity must be 1..127 or inherit")

        length_code: int | None = None
        raw_length_code = raw_event.get("length_code")
        has_explicit_length_field = "length" in raw_event
        raw_length = raw_event.get("length", "inherit")

        if raw_length_code is not None:
            length_code = _parse_length_code_or_error(
                raw_length_code,
                f"events step={step} track={track} length_code",
            )

        if isinstance(raw_length, dict):
            if length_code is not None:
                raise SyxFileError(
                    f"events step={step} track={track}: do not set both length mapping and length_code"
                )
            if "code" not in raw_length:
                raise SyxFileError(
                    f"events step={step} track={track}: length mapping requires 'code'"
                )
            length_code = _parse_length_code_or_error(
                raw_length["code"],
                f"events step={step} track={track} length.code",
            )
            raw_display = raw_length.get("display")
            if raw_display is not None:
                display = str(raw_display).strip()
                expected = DISPLAY_TO_EXPLICIT_LENGTH_CODE.get(display.upper())
                if expected is not None and expected != length_code:
                    raise SyxFileError(
                        f"events step={step} track={track}: length.display={display} does not match code"
                    )
            length = "code"
        else:
            length = str(raw_length).strip().upper()
            if length == "INHERIT":
                if length_code is not None:
                    if has_explicit_length_field:
                        raise SyxFileError(
                            f"events step={step} track={track}: length_code cannot be combined with length=inherit"
                        )
                    length = "CODE"
            elif length not in LENGTH_CODE_MAP:
                raise SyxFileError(f"events step={step} track={track}: invalid length {length}")

        time = _parse_micro_timing(raw_event.get("time", 0), f"events step={step} track={track} time")

        parsed_events.append(
            EventItem(
                step=step,
                track=track,
                note=note,
                note_midi=note_midi,
                velocity=velocity,
                length=("inherit" if length == "INHERIT" else length),
                length_code=length_code,
                time=time,
            )
        )

    parsed_events.sort(key=lambda x: (x.track, x.step, x.note_midi))

    return EventAssignment(
        version=version,
        device="digitone2",
        name=name,
        pattern=PatternSettings(
            mode=canonical_mode,
            tempo=tempo,
            speed=speed,
            total_steps=total_steps,
            change=change,
            reset=reset,
        ),
        track_default_velocity=track_default_velocity,
        track_scale=track_scale,
        events=tuple(parsed_events),
    )
