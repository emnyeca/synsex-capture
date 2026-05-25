"""Build Digitone II .syx files from events YAML."""

from __future__ import annotations

from pathlib import Path

from .digitone2.builder import BuildResult, build_digitone2_syx
from .events_yaml import load_event_assignment_yaml


def default_output_file_for_events(
    events_yaml: str | Path,
    *,
    output_dir: str | Path = "captures/generated",
) -> Path:
    events_path = Path(events_yaml)
    name = events_path.name
    lowered = name.lower()

    if lowered.endswith(".events.yaml"):
        stem = name[: -len(".events.yaml")]
    elif lowered.endswith(".events.yml"):
        stem = name[: -len(".events.yml")]
    elif lowered.endswith(".yaml"):
        stem = name[: -len(".yaml")]
    elif lowered.endswith(".yml"):
        stem = name[: -len(".yml")]
    else:
        stem = events_path.stem

    if not stem:
        stem = "generated"

    return Path(output_dir) / f"{stem}.syx"


def build_syx_from_events(
    *,
    events_yaml: str | Path,
    output_file: str | Path,
    template_file: str | Path | None = None,
) -> BuildResult:
    assignment = load_event_assignment_yaml(events_yaml)
    return build_digitone2_syx(
        assignment=assignment,
        output_file=output_file,
        template_override=template_file,
    )
