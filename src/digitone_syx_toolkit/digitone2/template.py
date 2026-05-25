"""Bundled template loading for Digitone II."""

from __future__ import annotations

from importlib.resources import files


def load_base_empty_template() -> bytes:
    return files("digitone_syx_toolkit.resources.digitone2").joinpath("BASE_EMPTY.syx").read_bytes()
