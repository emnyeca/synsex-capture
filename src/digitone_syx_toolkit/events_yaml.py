"""Validation and parsing for Digitone II focused events YAML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

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


@dataclass(frozen=True)
class PatternSettings:
    mode: str
    tempo: float
    speed: str
    total_steps: int


@dataclass(frozen=True)
class EventAssignment:
    version: int
    device: str
    name: str | None
    pattern: PatternSettings
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
        name = str(name)

    device = str(payload.get("device", "digitone2")).strip().lower()
    if device != "digitone2":
        raise SyxFileError(f"Unsupported device: {device}. Expected digitone2")

    pattern = payload.get("pattern")
    if not isinstance(pattern, dict):
        raise SyxFileError("'pattern' must be a mapping.")

    mode = str(pattern.get("mode", "pattern-wide")).strip().lower()
    if mode not in {"pattern-wide", "pattern_wide"}:
        raise SyxFileError("pattern.mode must be 'pattern-wide'")

    tempo = float(pattern.get("tempo", 120.0))
    if tempo < 30.0 or tempo > 300.0:
        raise SyxFileError("pattern.tempo must be in 30.0..300.0")

    speed = str(pattern.get("speed", "1/8")).strip()
    if speed not in {"2", "3/2", "1", "3/4", "1/2", "1/4", "1/8"}:
        raise SyxFileError("pattern.speed must be one of: 2, 3/2, 1, 3/4, 1/2, 1/4, 1/8")

    total_steps = _as_int(pattern.get("total_steps"), "pattern.total_steps")
    if total_steps < 2 or total_steps > 128:
        raise SyxFileError("pattern.total_steps must be in 2..128")

    raw_tracks = payload.get("tracks")
    if raw_tracks not in (None, []):
        raise SyxFileError(
            "'tracks' defaults rewrite is not supported in the current Digitone II encoder scope"
        )

    raw_events = payload.get("events")
    if not isinstance(raw_events, list):
        raise SyxFileError("'events' must be a list")

    parsed_events: list[EventItem] = []
    seen_pairs: set[tuple[int, int]] = set()
    for raw_event in raw_events:
        if not isinstance(raw_event, dict):
            raise SyxFileError("events[] entries must be mappings")

        step = _as_int(raw_event.get("step"), "events[].step")
        if step < 1 or step > total_steps:
            raise SyxFileError(f"events[].step out of range: {step} (1..{total_steps})")

        track = _as_int(raw_event.get("track"), f"events[step={step}].track")
        if track < 1 or track > 8:
            raise SyxFileError(f"events step={step}: track must be 1..8")

        pair = (step, track)
        if pair in seen_pairs:
            raise SyxFileError(
                f"Chord is not supported yet: duplicate event for step={step}, track={track}"
            )
        seen_pairs.add(pair)

        note = str(raw_event.get("note", "")).strip()
        if not note:
            raise SyxFileError(f"events step={step} track={track}: note is required")
        note_midi = _parse_note_name(note)

        velocity_raw = raw_event.get("velocity", "inherit")
        if isinstance(velocity_raw, str) and velocity_raw.strip().lower() == "inherit":
            velocity: int | str = "inherit"
        else:
            velocity = _as_int(velocity_raw, f"events step={step} track={track} velocity")
            if velocity < 1 or velocity > 127:
                raise SyxFileError(f"events step={step} track={track}: velocity must be 1..127 or inherit")

        length = str(raw_event.get("length", "inherit")).strip().upper()
        if length != "INHERIT" and length not in {"0.125", "0.25", "0.5", "1", "2", "4", "8", "16", "32", "64", "128", "INF"}:
            raise SyxFileError(f"events step={step} track={track}: invalid length {length}")

        parsed_events.append(
            EventItem(
                step=step,
                track=track,
                note=note,
                note_midi=note_midi,
                velocity=velocity,
                length=("inherit" if length == "INHERIT" else length),
            )
        )

    parsed_events.sort(key=lambda x: (x.track, x.step))

    return EventAssignment(
        version=version,
        device="digitone2",
        name=name,
        pattern=PatternSettings(
            mode="pattern-wide",
            tempo=tempo,
            speed=speed,
            total_steps=total_steps,
        ),
        events=tuple(parsed_events),
    )
