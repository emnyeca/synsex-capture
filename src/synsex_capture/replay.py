"""SysEx replay logic."""

from __future__ import annotations

import logging
import time

import mido


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
