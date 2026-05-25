"""Build Digitone II .syx files from events YAML."""

from __future__ import annotations

from pathlib import Path

from .digitone2.builder import BuildResult, build_digitone2_syx
from .events_yaml import load_event_assignment_yaml


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
