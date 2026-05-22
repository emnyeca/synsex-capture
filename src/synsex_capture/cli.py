"""Command-line interface for synsex-capture."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

import mido

from .capture import capture_sysex
from .diffing import diff_syx_files, format_diff
from .errors import MidiPortError, SynsexCaptureError, SyxFileError
from .gui import run_gui
from .hexview import hex_dump_file
from .logging_utils import configure_logging
from .metadata import write_capture_metadata
from .midi import list_input_ports, list_output_ports, resolve_port_name
from .replay import replay_sysex
from .syx import load_syx_file, save_syx_file

LOG = logging.getLogger("synsex_capture")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synsex_capture")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--log-file", help="Optional log file path")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list_ports", help="List MIDI input/output ports")

    capture_p = sub.add_parser("capture", help="Capture SysEx from an input port")
    capture_p.add_argument("--in-port", required=True, help="Input port name or 1-based index")
    capture_p.add_argument("--out-dir", default="captures", help="Directory for .syx output")
    capture_p.add_argument("--label", help="Label used for output filename")
    capture_p.add_argument("--max-messages", type=int, help="Stop after this many SysEx packets")
    capture_p.add_argument("--duration", type=float, help="Stop after this many seconds")
    capture_p.add_argument("--datasets-dir", default="datasets", help="Directory for YAML metadata")
    capture_p.add_argument("--track", help="Track metadata field")
    capture_p.add_argument("--step", help="Step metadata field")
    capture_p.add_argument("--note", help="Note metadata field")
    capture_p.add_argument("--len-display", help="LEN display metadata field")
    capture_p.add_argument("--velocity", type=int, help="Velocity metadata field")
    capture_p.add_argument("--remarks", help="Remarks metadata field")

    replay_p = sub.add_parser("replay", help="Replay .syx file to an output port")
    replay_p.add_argument("--out-port", required=True, help="Output port name or 1-based index")
    replay_p.add_argument("--file", required=True, help="Input .syx file")
    replay_p.add_argument("--delay-ms", type=float, default=0.0, help="Inter-message delay (ms)")

    diff_p = sub.add_parser("diff", help="Compare two .syx files")
    diff_p.add_argument("--file1", required=True, help="First .syx file")
    diff_p.add_argument("--file2", required=True, help="Second .syx file")
    diff_p.add_argument("--limit", type=int, help="Max number of differences to print")

    view_p = sub.add_parser("view", help="Show hex dump of .syx file")
    view_p.add_argument("--file", required=True, help="Input .syx file")

    sub.add_parser("gui", help="Launch analysis GUI (Tkinter)")

    return parser


def _cmd_list_ports() -> int:
    in_ports = list_input_ports()
    out_ports = list_output_ports()

    print("Input ports:")
    if not in_ports:
        print("  (none)")
    for idx, name in enumerate(in_ports, start=1):
        print(f"  [{idx}] {name}")

    print("\nOutput ports:")
    if not out_ports:
        print("  (none)")
    for idx, name in enumerate(out_ports, start=1):
        print(f"  [{idx}] {name}")
    return 0


def _cmd_capture(args: argparse.Namespace) -> int:
    in_port = resolve_port_name(list_input_ports(), args.in_port)

    label = args.label or datetime.now().strftime("capture_%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    syx_path = out_dir / f"{label}.syx"

    result = capture_sysex(
        in_port_name=in_port,
        max_messages=args.max_messages,
        duration_seconds=args.duration,
        logger=LOG,
    )
    save_syx_file(result.messages, syx_path)

    total_bytes = sum(len(m) for m in result.messages)
    LOG.info(
        "Capture finished: messages=%d total_bytes=%d elapsed=%.2fs file=%s",
        len(result.messages),
        total_bytes,
        result.elapsed_seconds,
        syx_path,
    )

    metadata_path = write_capture_metadata(
        datasets_dir=args.datasets_dir,
        syx_file=syx_path,
        label=label,
        message_count=len(result.messages),
        total_bytes=total_bytes,
        track=args.track,
        step=args.step,
        note=args.note,
        len_display=args.len_display,
        velocity=args.velocity,
        remarks=args.remarks,
    )
    LOG.info("Wrote metadata YAML: %s", metadata_path)
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    out_port = resolve_port_name(list_output_ports(), args.out_port)
    messages = load_syx_file(args.file)
    sent = replay_sysex(out_port_name=out_port, messages=messages, delay_ms=args.delay_ms, logger=LOG)
    LOG.info("Replay finished: sent=%d file=%s", sent, args.file)
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    result = diff_syx_files(args.file1, args.file2)
    print(format_diff(result, limit=args.limit))
    return 0


def _cmd_view(args: argparse.Namespace) -> int:
    print(hex_dump_file(args.file))
    return 0


def _cmd_gui() -> int:
    run_gui()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose, log_file=args.log_file)

    try:
        if args.command == "list_ports":
            return _cmd_list_ports()
        if args.command == "capture":
            return _cmd_capture(args)
        if args.command == "replay":
            return _cmd_replay(args)
        if args.command == "diff":
            return _cmd_diff(args)
        if args.command == "view":
            return _cmd_view(args)
        if args.command == "gui":
            return _cmd_gui()
        raise SynsexCaptureError(f"Unknown command: {args.command}")
    except (SynsexCaptureError, MidiPortError, SyxFileError, OSError, ValueError, mido.BackendError) as exc:
        LOG.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
