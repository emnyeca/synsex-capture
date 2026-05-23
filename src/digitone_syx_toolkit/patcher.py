"""Selective byte patching utilities for SysEx workflows.

This module intentionally supports targeted byte updates instead of full format parsing.
The primary use case is applying known offsets discovered by binary-diff analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import SyxFileError


@dataclass
class BytePatch:
    """One byte update at a specific offset."""

    offset: int
    value: int
    before: int | None = None


def _parse_patch_value(value: object) -> int:
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        parsed = int(text, 16) if text.lower().startswith("0x") else int(text)
    else:
        raise SyxFileError(f"Unsupported patch value type: {type(value)}")

    if parsed < 0 or parsed > 0xFF:
        raise SyxFileError(f"Patch value out of byte range: {parsed}")
    return parsed


def load_patches_yaml(path: str | Path) -> list[BytePatch]:
    """Load patch list from YAML.

    Expected shape:
    patches:
      - offset: 123
        value: 0x45
        before: 0x41  # optional safety check
    """
    file_path = Path(path)
    if not file_path.exists():
        raise SyxFileError(f"Patch YAML not found: {file_path}")

    payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SyxFileError("Patch YAML must be a mapping with 'patches' key.")

    raw_patches = payload.get("patches")
    if not isinstance(raw_patches, list):
        raise SyxFileError("Patch YAML must contain 'patches' as a list.")

    patches: list[BytePatch] = []
    for item in raw_patches:
        if not isinstance(item, dict):
            raise SyxFileError("Each patch item must be a mapping.")

        if "offset" not in item or "value" not in item:
            raise SyxFileError("Each patch must define 'offset' and 'value'.")

        offset = int(item["offset"])
        value = _parse_patch_value(item["value"])

        before: int | None = None
        if "before" in item and item["before"] is not None:
            before = _parse_patch_value(item["before"])

        patches.append(BytePatch(offset=offset, value=value, before=before))

    return patches


def apply_byte_patches(data: bytes, patches: list[BytePatch], strict_before: bool = True) -> bytes:
    """Apply byte patches to a buffer and return updated bytes."""
    mutable = bytearray(data)

    for patch in patches:
        if patch.offset < 0 or patch.offset >= len(mutable):
            raise SyxFileError(
                f"Patch offset out of range: {patch.offset}. File length is {len(mutable)} bytes."
            )

        current = mutable[patch.offset]
        if strict_before and patch.before is not None and current != patch.before:
            raise SyxFileError(
                f"Before-check failed at offset {patch.offset}: expected {patch.before:02X}, got {current:02X}."
            )

        mutable[patch.offset] = patch.value

    return bytes(mutable)


def patch_syx_file(
    template_file: str | Path,
    patch_yaml: str | Path,
    output_file: str | Path,
    strict_before: bool = True,
) -> Path:
    """Patch a template .syx using YAML-defined byte patches."""
    template_path = Path(template_file)
    if not template_path.exists():
        raise SyxFileError(f"Template .syx not found: {template_path}")

    data = template_path.read_bytes()
    patches = load_patches_yaml(patch_yaml)
    patched = apply_byte_patches(data, patches, strict_before=strict_before)

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(patched)
    return out_path
