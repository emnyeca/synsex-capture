"""Validation and parsing for Harmony Cloud style events YAML."""

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
    track: int
    note: str
    note_midi: int
    duration: int
    velocity: int | None = None


@dataclass(frozen=True)
class StepItem:
    step: int
    chord: str | None
    hold: bool
    events: tuple[EventItem, ...]


@dataclass(frozen=True)
class EventAssignment:
    version: int
    name: str | None
    length_steps: int
    speed: str | None
    time_signature: str | None
    steps: tuple[StepItem, ...]


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

    midi = (octave + 1) * 12 + _NOTE_BASE[root] + accidental
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
    """Load and validate events YAML against the v1 schema."""
    payload = _load_yaml(path)

    version = _as_int(payload.get("version", 1), "version")
    if version != 1:
        raise SyxFileError(f"Unsupported events schema version: {version}")

    name = payload.get("name")
    if name is not None:
        name = str(name)

    pattern = payload.get("pattern")
    if not isinstance(pattern, dict):
        raise SyxFileError("'pattern' must be a mapping.")

    length_steps = _as_int(pattern.get("length_steps"), "pattern.length_steps")
    if length_steps < 1:
        raise SyxFileError("pattern.length_steps must be >= 1")

    speed = pattern.get("speed")
    speed = str(speed) if speed is not None else None
    time_signature = pattern.get("time_signature")
    time_signature = str(time_signature) if time_signature is not None else None

    raw_steps = payload.get("steps")
    if not isinstance(raw_steps, list):
        raise SyxFileError("'steps' must be a list.")

    parsed_steps: list[StepItem] = []
    seen_step_numbers: set[int] = set()

    for raw_step in raw_steps:
        if not isinstance(raw_step, dict):
            raise SyxFileError("Each step must be a mapping.")

        step_number = _as_int(raw_step.get("step"), "steps[].step")
        if step_number < 1 or step_number > length_steps:
            raise SyxFileError(
                f"step out of range: {step_number}. Must be between 1 and {length_steps}."
            )
        if step_number in seen_step_numbers:
            raise SyxFileError(f"Duplicate step entry: {step_number}")
        seen_step_numbers.add(step_number)

        chord = raw_step.get("chord")
        chord = str(chord) if chord is not None else None

        hold = bool(raw_step.get("hold", False))
        raw_events = raw_step.get("events")

        if hold and raw_events:
            raise SyxFileError(f"step {step_number}: hold=true cannot be combined with events")

        parsed_events: list[EventItem] = []
        track_seen: set[int] = set()

        if raw_events is not None:
            if not isinstance(raw_events, list):
                raise SyxFileError(f"step {step_number}: events must be a list")

            for raw_event in raw_events:
                if not isinstance(raw_event, dict):
                    raise SyxFileError(f"step {step_number}: event entries must be mappings")

                track = _as_int(raw_event.get("track"), f"step {step_number} events[].track")
                if track < 0 or track > 6:
                    raise SyxFileError(f"step {step_number}: track must be 0..6, got {track}")
                if track in track_seen:
                    raise SyxFileError(f"step {step_number}: duplicate track assignment {track}")
                track_seen.add(track)

                note = str(raw_event.get("note", "")).strip()
                if not note:
                    raise SyxFileError(f"step {step_number} track {track}: note is required")
                note_midi = _parse_note_name(note)

                duration = _as_int(raw_event.get("duration"), f"step {step_number} track {track} duration")
                if duration < 1:
                    raise SyxFileError(f"step {step_number} track {track}: duration must be >= 1")

                velocity: int | None = None
                if "velocity" in raw_event and raw_event["velocity"] is not None:
                    velocity = _as_int(raw_event["velocity"], f"step {step_number} track {track} velocity")
                    if velocity < 1 or velocity > 127:
                        raise SyxFileError(f"step {step_number} track {track}: velocity must be 1..127")

                parsed_events.append(
                    EventItem(
                        track=track,
                        note=note,
                        note_midi=note_midi,
                        duration=duration,
                        velocity=velocity,
                    )
                )

        parsed_steps.append(
            StepItem(
                step=step_number,
                chord=chord,
                hold=hold,
                events=tuple(parsed_events),
            )
        )

    parsed_steps.sort(key=lambda x: x.step)

    return EventAssignment(
        version=version,
        name=name,
        length_steps=length_steps,
        speed=speed,
        time_signature=time_signature,
        steps=tuple(parsed_steps),
    )
