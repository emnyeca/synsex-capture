"""Dataset metadata output in YAML format."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml


def write_capture_metadata(
    datasets_dir: str | Path,
    syx_file: str | Path,
    label: str,
    message_count: int,
    total_bytes: int,
    track: str | None = None,
    step: str | None = None,
    note: str | None = None,
    len_display: str | None = None,
    velocity: int | None = None,
    remarks: str | None = None,
) -> Path:
    """Write capture metadata YAML into datasets directory."""
    out_dir = Path(datasets_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "file": str(Path(syx_file)),
        "label": label,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "message_count": message_count,
        "total_bytes": total_bytes,
        "track": track,
        "step": step,
        "note": note,
        "len_display": len_display,
        "velocity": velocity,
        "remarks": remarks,
    }

    out_file = out_dir / f"{label}.yaml"
    out_file.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return out_file
