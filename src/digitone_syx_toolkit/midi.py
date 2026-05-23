"""MIDI port listing and selection helpers."""

from __future__ import annotations

from typing import Sequence

import mido

from .errors import MidiPortError


def list_input_ports() -> list[str]:
    """Return available MIDI input port names."""
    return list(mido.get_input_names())


def list_output_ports() -> list[str]:
    """Return available MIDI output port names."""
    return list(mido.get_output_names())


def resolve_port_name(ports: Sequence[str], selector: str | int) -> str:
    """Resolve 1-based index or exact name into a concrete port name."""
    if not ports:
        raise MidiPortError("No MIDI ports are available.")

    if isinstance(selector, int) or (isinstance(selector, str) and selector.isdigit()):
        index_1_based = int(selector)
        if index_1_based < 1 or index_1_based > len(ports):
            raise MidiPortError(
                f"Port index out of range: {selector}. Valid range is 1..{len(ports)}"
            )
        return ports[index_1_based - 1]

    selector_str = str(selector)
    if selector_str in ports:
        return selector_str

    raise MidiPortError(
        f"Port not found: {selector_str}. Use list_ports to inspect available ports."
    )
