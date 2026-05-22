"""SysEx capture logic."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import mido


@dataclass
class CaptureResult:
    """Result details from a capture session."""

    messages: list[bytes]
    elapsed_seconds: float


def capture_sysex(
    in_port_name: str,
    max_messages: int | None = None,
    duration_seconds: float | None = None,
    poll_interval_seconds: float = 0.01,
    logger: logging.Logger | None = None,
) -> CaptureResult:
    """Capture SysEx packets from the specified input port.

    Stops when one of these conditions is met:
    - KeyboardInterrupt
    - max_messages reached (if provided)
    - duration_seconds elapsed (if provided)
    """
    log = logger or logging.getLogger(__name__)
    packets: list[bytes] = []
    started = time.perf_counter()

    with mido.open_input(in_port_name) as in_port:
        log.info("Capture started on input port: %s", in_port_name)
        try:
            while True:
                for msg in in_port.iter_pending():
                    if msg.type != "sysex":
                        continue

                    packet = bytes(msg.bytes())
                    packets.append(packet)
                    log.info(
                        "Captured SysEx #%d length=%d bytes", len(packets), len(packet)
                    )

                    if max_messages is not None and len(packets) >= max_messages:
                        elapsed = time.perf_counter() - started
                        log.info("Capture stopped by max_messages=%d", max_messages)
                        return CaptureResult(messages=packets, elapsed_seconds=elapsed)

                if duration_seconds is not None:
                    elapsed_now = time.perf_counter() - started
                    if elapsed_now >= duration_seconds:
                        log.info("Capture stopped by duration=%.2f seconds", duration_seconds)
                        return CaptureResult(messages=packets, elapsed_seconds=elapsed_now)

                time.sleep(poll_interval_seconds)
        except KeyboardInterrupt:
            elapsed = time.perf_counter() - started
            log.info("Capture interrupted by user")
            return CaptureResult(messages=packets, elapsed_seconds=elapsed)
