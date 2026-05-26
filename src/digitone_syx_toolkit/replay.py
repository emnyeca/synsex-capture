"""SysEx replay logic."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import mido

from .syx import load_syx_file


def replay_sysex(
    out_port_name: str,
    messages: list[bytes],
    delay_ms: float = 0.0,
    logger: logging.Logger | None = None,
) -> int:
    """Replay SysEx packets to the specified output port."""
    log = logger or logging.getLogger(__name__)

    with mido.open_output(out_port_name) as out_port:
        for idx, packet in enumerate(messages, start=1):
            out_port.send(mido.Message.from_bytes(list(packet)))
            log.info("Sent SysEx #%d length=%d bytes", idx, len(packet))
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    return len(messages)


def load_sysex_messages_from_files(syx_files: list[str | Path]) -> list[bytes]:
    """Load packets from one or more .syx files preserving file and packet order."""
    messages: list[bytes] = []
    for syx_file in syx_files:
        messages.extend(load_syx_file(syx_file))
    return messages


def replay_sysex_files(
    out_port_name: str,
    syx_files: list[str | Path],
    delay_ms: float = 0.0,
    logger: logging.Logger | None = None,
) -> int:
    """Replay one or more .syx files to the specified output port."""
    messages = load_sysex_messages_from_files(syx_files)
    return replay_sysex(out_port_name=out_port_name, messages=messages, delay_ms=delay_ms, logger=logger)


def replay_sysex_bundle(
    out_port_name: str,
    bundle_syx_file: str | Path,
    delay_ms: float = 0.0,
    logger: logging.Logger | None = None,
) -> int:
    """Replay a concatenated bundle .syx (containing multiple F0...F7 packets)."""
    return replay_sysex_files(
        out_port_name=out_port_name,
        syx_files=[bundle_syx_file],
        delay_ms=delay_ms,
        logger=logger,
    )
