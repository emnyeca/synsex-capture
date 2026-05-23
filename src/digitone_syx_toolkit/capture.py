"""SysEx capture logic."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import rtmidi


@dataclass
class CaptureResult:
    """Result details from a capture session."""

    messages: list[bytes]
    elapsed_seconds: float


class SysexChunkAssembler:
    """Assemble full SysEx packets from potentially fragmented MIDI chunks."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._collecting = False

    def feed(self, chunk: list[int] | bytes) -> list[bytes]:
        """Feed one MIDI byte chunk and return zero or more completed SysEx packets."""
        completed: list[bytes] = []

        for value in chunk:
            b = int(value) & 0xFF

            if b == 0xF0:
                self._buffer = bytearray([0xF0])
                self._collecting = True
                continue

            if not self._collecting:
                continue

            self._buffer.append(b)
            if b == 0xF7:
                completed.append(bytes(self._buffer))
                self._buffer.clear()
                self._collecting = False

        return completed


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

    midi_in = rtmidi.MidiIn()
    try:
        ports = midi_in.get_ports()
        if in_port_name not in ports:
            raise ValueError(f"Input port not found for rtmidi: {in_port_name}")

        port_index = ports.index(in_port_name)
        midi_in.open_port(port_index)
        midi_in.ignore_types(sysex=False, timing=False, active_sense=True)

        assembler = SysexChunkAssembler()
        log.info("Capture started on input port: %s", in_port_name)

        try:
            while True:
                message = midi_in.get_message()
                if message:
                    chunk, _delta = message
                    for packet in assembler.feed(chunk):
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
    finally:
        try:
            midi_in.close_port()
        except Exception:  # noqa: BLE001
            pass
