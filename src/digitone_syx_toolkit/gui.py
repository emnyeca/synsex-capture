"""Tkinter GUI for focused SysEx analysis and partial rewrite workflow."""

from __future__ import annotations

from contextlib import ExitStack
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import mido
import rtmidi
import yaml

from .capture import SysexChunkAssembler
from .diffing import DiffResult, diff_syx_files, format_diff
from .events_to_syx import (
    build_syx_from_events,
    default_output_file_for_events,
)
from .events_yaml import load_event_assignment_yaml
from .hexview import hex_dump_file
from .midi import list_input_ports, list_output_ports
from .patcher import patch_syx_file
from .replay import replay_sysex
from .syx import load_syx_file, save_syx_file


class AnalysisGui:
    """A small GUI to support offset discovery and selective byte patching."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("digitone-syx-toolkit: Pattern Analysis Assistant")
        self.root.geometry("1100x760")

        self.file1_var = tk.StringVar()
        self.file2_var = tk.StringVar()
        self.hex_file_var = tk.StringVar()
        self.template_var = tk.StringVar()
        self.patch_yaml_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.diff_limit_var = tk.StringVar(value="256")
        self.capture_in_port_var = tk.StringVar()
        self.capture_all_inputs_var = tk.BooleanVar(value=False)
        self.capture_log_all_var = tk.BooleanVar(value=False)
        self.replay_out_port_var = tk.StringVar()
        self.capture_out_dir_var = tk.StringVar(value="captures")
        self.capture_label_var = tk.StringVar()
        self.capture_max_messages_var = tk.StringVar(value="")
        self.capture_duration_var = tk.StringVar(value="")
        self.replay_file_var = tk.StringVar()
        self.replay_delay_var = tk.StringVar(value="0")
        self.events_yaml_var = tk.StringVar()
        self.events_output_var = tk.StringVar()

        self._capture_thread: threading.Thread | None = None
        self._stop_capture_event = threading.Event()
        self._captured_packets: list[bytes] = []

        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab_diff = ttk.Frame(notebook)
        tab_hex = ttk.Frame(notebook)
        tab_patch = ttk.Frame(notebook)
        tab_midi = ttk.Frame(notebook)
        tab_events = ttk.Frame(notebook)

        notebook.add(tab_midi, text="MIDI Capture/Replay")
        notebook.add(tab_diff, text="Diff & Mapping")
        notebook.add(tab_hex, text="Hex Viewer")
        notebook.add(tab_patch, text="Selective Patch")
        notebook.add(tab_events, text="Events -> SYX")

        self._build_midi_tab(tab_midi)
        self._build_diff_tab(tab_diff)
        self._build_hex_tab(tab_hex)
        self._build_patch_tab(tab_patch)
        self._build_events_tab(tab_events)

    def _build_midi_tab(self, parent: ttk.Frame) -> None:
        ports_frame = ttk.LabelFrame(parent, text="Ports")
        ports_frame.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(ports_frame, text="Input port").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.in_port_combo = ttk.Combobox(
            ports_frame, textvariable=self.capture_in_port_var, width=70, state="readonly"
        )
        self.in_port_combo.grid(row=0, column=1, padx=4, pady=4)
        ttk.Checkbutton(
            ports_frame,
            text="Capture all input ports (auto detect)",
            variable=self.capture_all_inputs_var,
        ).grid(row=0, column=3, sticky="w", padx=4, pady=4)
        ttk.Checkbutton(
            ports_frame,
            text="Log all MIDI messages (diagnostic)",
            variable=self.capture_log_all_var,
        ).grid(row=1, column=3, sticky="w", padx=4, pady=4)

        ttk.Label(ports_frame, text="Output port").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.out_port_combo = ttk.Combobox(
            ports_frame, textvariable=self.replay_out_port_var, width=70, state="readonly"
        )
        self.out_port_combo.grid(row=1, column=1, padx=4, pady=4)

        ttk.Button(ports_frame, text="Refresh Ports", command=self._refresh_ports).grid(
            row=0, column=2, rowspan=2, padx=4, pady=4
        )

        capture_frame = ttk.LabelFrame(parent, text="Capture SysEx")
        capture_frame.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(capture_frame, text="Out dir").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(capture_frame, textvariable=self.capture_out_dir_var, width=60).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Button(
            capture_frame,
            text="Browse",
            command=lambda: self._pick_directory(self.capture_out_dir_var),
        ).grid(row=0, column=2, padx=4, pady=4)

        ttk.Label(capture_frame, text="Label").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(capture_frame, textvariable=self.capture_label_var, width=24).grid(
            row=1, column=1, sticky="w", padx=4, pady=4
        )

        ttk.Label(capture_frame, text="Max messages (blank=unlimited)").grid(
            row=2, column=0, sticky="w", padx=4, pady=4
        )
        ttk.Entry(capture_frame, textvariable=self.capture_max_messages_var, width=12).grid(
            row=2, column=1, sticky="w", padx=4, pady=4
        )

        ttk.Label(capture_frame, text="Duration sec (optional)").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(capture_frame, textvariable=self.capture_duration_var, width=12).grid(
            row=3, column=1, sticky="w", padx=4, pady=4
        )

        capture_btn_row = ttk.Frame(capture_frame)
        capture_btn_row.grid(row=4, column=0, columnspan=3, sticky="w", padx=4, pady=6)
        self.capture_start_btn = ttk.Button(capture_btn_row, text="Start Capture", command=self._start_capture)
        self.capture_start_btn.pack(side=tk.LEFT)
        self.capture_stop_btn = ttk.Button(
            capture_btn_row, text="Stop Capture", command=self._stop_capture, state=tk.DISABLED
        )
        self.capture_stop_btn.pack(side=tk.LEFT, padx=6)

        replay_frame = ttk.LabelFrame(parent, text="Replay SysEx")
        replay_frame.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(replay_frame, text=".syx file").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(replay_frame, textvariable=self.replay_file_var, width=60).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Button(
            replay_frame,
            text="Browse",
            command=lambda: self._pick_file(self.replay_file_var),
        ).grid(row=0, column=2, padx=4, pady=4)

        ttk.Label(replay_frame, text="Delay ms").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(replay_frame, textvariable=self.replay_delay_var, width=12).grid(
            row=1, column=1, sticky="w", padx=4, pady=4
        )

        ttk.Button(replay_frame, text="Send to Output Port", command=self._run_replay_from_gui).grid(
            row=2, column=0, columnspan=3, sticky="w", padx=4, pady=6
        )

        log_frame = ttk.LabelFrame(parent, text="MIDI Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.midi_log_text = tk.Text(log_frame, wrap=tk.NONE, height=14)
        self.midi_log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._refresh_ports()

    def _build_diff_tab(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Template / Before .syx").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.file1_var, width=90).grid(row=0, column=1, padx=6)
        ttk.Button(top, text="Browse", command=lambda: self._pick_file(self.file1_var)).grid(row=0, column=2)

        ttk.Label(top, text="Changed / After .syx").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.file2_var, width=90).grid(row=1, column=1, padx=6)
        ttk.Button(top, text="Browse", command=lambda: self._pick_file(self.file2_var)).grid(row=1, column=2)

        ttk.Label(top, text="Show first N diffs").grid(row=2, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.diff_limit_var, width=12).grid(row=2, column=1, sticky="w", padx=6)

        btn_row = ttk.Frame(parent)
        btn_row.pack(fill=tk.X, padx=8)
        ttk.Button(btn_row, text="Run Diff", command=self._run_diff).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Export Patch YAML", command=self._export_patch_yaml).pack(side=tk.LEFT, padx=6)

        self.diff_text = tk.Text(parent, wrap=tk.NONE, height=30)
        self.diff_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_hex_tab(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text=".syx file").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.hex_file_var, width=90).grid(row=0, column=1, padx=6)
        ttk.Button(top, text="Browse", command=lambda: self._pick_file(self.hex_file_var)).grid(row=0, column=2)
        ttk.Button(top, text="View Hex", command=self._run_hex_view).grid(row=0, column=3, padx=6)

        self.hex_text = tk.Text(parent, wrap=tk.NONE, height=32)
        self.hex_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_patch_tab(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Template .syx").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.template_var, width=90).grid(row=0, column=1, padx=6)
        ttk.Button(top, text="Browse", command=lambda: self._pick_file(self.template_var)).grid(row=0, column=2)

        ttk.Label(top, text="Patch YAML").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.patch_yaml_var, width=90).grid(row=1, column=1, padx=6)
        ttk.Button(top, text="Browse", command=lambda: self._pick_file(self.patch_yaml_var, [("YAML", "*.yaml *.yml")])).grid(row=1, column=2)

        ttk.Label(top, text="Output .syx").grid(row=2, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.output_var, width=90).grid(row=2, column=1, padx=6)
        ttk.Button(top, text="Browse", command=self._pick_save_output).grid(row=2, column=2)

        ttk.Button(parent, text="Apply Patch", command=self._apply_patch).pack(anchor="w", padx=8, pady=8)

        hint = (
            "Patch YAML format:\n"
            "patches:\n"
            "  - offset: 1234\n"
            "    before: 0x2A  # optional safety check\n"
            "    value: 0x30\n"
        )
        self.patch_hint = tk.Text(parent, height=8, wrap=tk.WORD)
        self.patch_hint.pack(fill=tk.BOTH, expand=False, padx=8, pady=8)
        self.patch_hint.insert("1.0", hint)
        self.patch_hint.config(state=tk.DISABLED)

    def _build_events_tab(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Events YAML").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.events_yaml_var, width=90).grid(row=0, column=1, padx=6)
        ttk.Button(
            top,
            text="Browse",
            command=self._pick_events_yaml,
        ).grid(row=0, column=2)

        ttk.Label(top, text="Output .syx").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.events_output_var, width=90).grid(row=1, column=1, padx=6)
        ttk.Button(top, text="Browse", command=self._pick_events_output).grid(row=1, column=2)

        btn_row = ttk.Frame(parent)
        btn_row.pack(fill=tk.X, padx=8, pady=4)
        ttk.Button(btn_row, text="Validate Events YAML", command=self._validate_events_yaml).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Generate Digitone II SYX", command=self._generate_syx_from_events).pack(
            side=tk.LEFT, padx=6
        )

        hint = (
            "This flow generates a Digitone II pattern from bundled BASE_EMPTY.syx\n"
            "- Required input: events.yaml\n"
            "- Required output: output .syx\n"
            "\n"
            "Current constraints:\n"
            "- Digitone II focused implementation\n"
            "- Deterministic slot order: track asc -> step asc\n"
            "- Same track/step duplicate triggers are rejected"
        )
        self.events_hint = tk.Text(parent, height=8, wrap=tk.WORD)
        self.events_hint.pack(fill=tk.BOTH, expand=False, padx=8, pady=8)
        self.events_hint.insert("1.0", hint)
        self.events_hint.config(state=tk.DISABLED)

        log_frame = ttk.LabelFrame(parent, text="Events Build Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.events_log_text = tk.Text(log_frame, wrap=tk.NONE, height=14)
        self.events_log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _pick_file(self, target_var: tk.StringVar, filetypes: list[tuple[str, str]] | None = None) -> None:
        path = filedialog.askopenfilename(filetypes=filetypes or [("SysEx", "*.syx"), ("All", "*.*")])
        if path:
            target_var.set(path)

    def _pick_save_output(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".syx", filetypes=[("SysEx", "*.syx"), ("All", "*.*")])
        if path:
            self.output_var.set(path)

    def _pick_events_output(self) -> None:
        initial = self.events_output_var.get().strip()
        default_path = initial or str(default_output_file_for_events(self.events_yaml_var.get().strip() or "events.yaml"))
        path = filedialog.asksaveasfilename(
            defaultextension=".syx",
            filetypes=[("SysEx", "*.syx"), ("All", "*.*")],
            initialfile=Path(default_path).name,
            initialdir=str(Path(default_path).parent),
        )
        if path:
            self.events_output_var.set(path)

    def _pick_events_yaml(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("YAML", "*.yaml *.yml"), ("All", "*.*")])
        if not path:
            return
        self.events_yaml_var.set(path)
        self.events_output_var.set(str(default_output_file_for_events(path)))

    def _pick_directory(self, target_var: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            target_var.set(path)

    def _log_midi(self, message: str) -> None:
        self.midi_log_text.insert(tk.END, message + "\n")
        self.midi_log_text.see(tk.END)

    def _log_events(self, message: str) -> None:
        self.events_log_text.insert(tk.END, message + "\n")
        self.events_log_text.see(tk.END)

    def _refresh_ports(self) -> None:
        try:
            in_ports = list_input_ports()
            out_ports = list_output_ports()
            self.in_port_combo["values"] = in_ports
            self.out_port_combo["values"] = out_ports

            if in_ports and not self.capture_in_port_var.get():
                self.capture_in_port_var.set(in_ports[0])
            if out_ports and not self.replay_out_port_var.get():
                self.replay_out_port_var.set(out_ports[0])

            self._log_midi(f"Ports refreshed: in={len(in_ports)} out={len(out_ports)}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Port Error", str(exc))

    def _start_capture(self) -> None:
        if self._capture_thread is not None and self._capture_thread.is_alive():
            messagebox.showerror("Capture Running", "Capture is already running.")
            return

        in_port = self.capture_in_port_var.get().strip()
        if not in_port:
            messagebox.showerror("Input Error", "Please select an input port.")
            return

        self._captured_packets = []
        self._stop_capture_event.clear()
        self.capture_start_btn.config(state=tk.DISABLED)
        self.capture_stop_btn.config(state=tk.NORMAL)

        self._capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
        self._capture_thread.start()

    def _stop_capture(self) -> None:
        self._stop_capture_event.set()
        self._log_midi("Stop requested.")

    def _capture_worker(self) -> None:
        in_port = self.capture_in_port_var.get().strip()
        capture_all = self.capture_all_inputs_var.get()
        log_all_messages = self.capture_log_all_var.get()
        out_dir = Path(self.capture_out_dir_var.get().strip() or "captures")
        label = self.capture_label_var.get().strip() or datetime.now().strftime("capture_%Y%m%d_%H%M%S")

        max_messages: int | None = None
        if self.capture_max_messages_var.get().strip():
            max_messages = int(self.capture_max_messages_var.get().strip())
            if max_messages <= 0:
                raise RuntimeError("Max messages must be a positive integer or blank.")

        duration_seconds: float | None = None
        if self.capture_duration_var.get().strip():
            duration_seconds = float(self.capture_duration_var.get().strip())

        started = time.perf_counter()
        non_sysex_count = 0
        saved_files: list[Path] = []
        out_dir.mkdir(parents=True, exist_ok=True)

        def ui_log(msg: str) -> None:
            self.root.after(0, lambda: self._log_midi(msg))

        try:
            if capture_all:
                port_names = list_input_ports()
                if not port_names:
                    raise RuntimeError("No input ports available.")
                ui_log("Capture start: input=ALL")
            else:
                if not in_port:
                    raise RuntimeError("No input port selected.")
                port_names = [in_port]
                ui_log(f"Capture start: input={in_port}")

            with ExitStack() as stack:
                midi_ins: list[tuple[str, rtmidi.MidiIn, SysexChunkAssembler]] = []
                for name in port_names:
                    midi_in = rtmidi.MidiIn()
                    available = midi_in.get_ports()
                    if name not in available:
                        raise RuntimeError(f"Input port not found for rtmidi: {name}")

                    port_index = available.index(name)
                    midi_in.open_port(port_index)
                    midi_in.ignore_types(sysex=False, timing=False, active_sense=True)
                    stack.callback(midi_in.close_port)
                    midi_ins.append((name, midi_in, SysexChunkAssembler()))

                while True:
                    for src_name, midi_in, assembler in midi_ins:
                        message = midi_in.get_message()
                        if not message:
                            continue

                        chunk, _delta = message
                        parsed_packets = assembler.feed(chunk)

                        if parsed_packets:
                            for packet in parsed_packets:
                                self._captured_packets.append(packet)
                                packet_index = len(self._captured_packets)
                                packet_label = f"{label}_{packet_index:04d}"
                                syx_path = out_dir / f"{packet_label}.syx"
                                save_syx_file([packet], syx_path)
                                saved_files.append(syx_path)
                                ui_log(
                                    f"Captured SysEx #{packet_index} "
                                    f"length={len(packet)} source={src_name} "
                                    f"saved={syx_path}"
                                )

                                if max_messages is not None and len(self._captured_packets) >= max_messages:
                                    raise StopIteration
                            continue

                        non_sysex_count += 1
                        if log_all_messages and non_sysex_count <= 64:
                            ui_log(
                                f"MIDI(non-sysex/chunk) source={src_name} bytes={chunk}"
                            )

                    if self._stop_capture_event.is_set():
                        break

                    if duration_seconds is not None and (time.perf_counter() - started) >= duration_seconds:
                        break

                    time.sleep(0.01)
        except StopIteration:
            pass
        except Exception as exc:  # noqa: BLE001
            self.root.after(0, lambda: messagebox.showerror("Capture Error", str(exc)))
        finally:
            elapsed = time.perf_counter() - started
            try:
                if not self._captured_packets:
                    if non_sysex_count > 0:
                        ui_log(
                            f"Diagnostic: non-sysex MIDI was received ({non_sysex_count} messages), "
                            "but no SysEx arrived. Device SysEx send/filter setting is likely blocking."
                        )
                    else:
                        ui_log(
                            "Diagnostic: no MIDI traffic detected on selected inputs. "
                            "Check port routing or whether another app has the MIDI device open."
                        )
                    ui_log(
                        "No SysEx captured. Nothing was saved. "
                        "Check Digitone USB routing/SysEx send settings and selected input port."
                    )
                    ui_log(
                        "Troubleshooting: 1) Digitone MIDI CONFIG > PORT CONFIG output includes USB, "
                        "2) SysEx send is enabled, 3) no DAW/app is holding the same MIDI port, "
                        "4) try Capture all input ports to identify actual route."
                    )
                else:
                    total_bytes = sum(len(m) for m in self._captured_packets)
                    ui_log(
                        "Capture finished: "
                        f"messages={len(self._captured_packets)} "
                        f"bytes={total_bytes} elapsed={elapsed:.2f}s "
                        f"saved_files={len(saved_files)} out_dir={out_dir}"
                    )
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, lambda: messagebox.showerror("Save Error", str(exc)))
            finally:
                self.root.after(0, lambda: self.capture_start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.capture_stop_btn.config(state=tk.DISABLED))

    def _run_replay_from_gui(self) -> None:
        out_port = self.replay_out_port_var.get().strip()
        syx_file = self.replay_file_var.get().strip()

        if not out_port:
            messagebox.showerror("Input Error", "Please select an output port.")
            return
        if not syx_file:
            messagebox.showerror("Input Error", "Please choose a .syx file to replay.")
            return

        try:
            delay_ms = float(self.replay_delay_var.get().strip() or "0")
            messages = load_syx_file(syx_file)
            sent = replay_sysex(out_port_name=out_port, messages=messages, delay_ms=delay_ms)
            self._log_midi(f"Replay finished: sent={sent} file={syx_file} out={out_port}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Replay Error", str(exc))

    def _run_diff(self) -> None:
        file1 = self.file1_var.get().strip()
        file2 = self.file2_var.get().strip()

        if not file1 or not file2:
            messagebox.showerror("Input Error", "Please select both before/after .syx files.")
            return

        try:
            limit = int(self.diff_limit_var.get()) if self.diff_limit_var.get().strip() else None
            result = diff_syx_files(file1, file2)
            rendered = format_diff(result, limit=limit)
            self.diff_text.delete("1.0", tk.END)
            self.diff_text.insert("1.0", rendered)
            self._last_diff_result = result
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Diff Error", str(exc))

    def _export_patch_yaml(self) -> None:
        result: DiffResult | None = getattr(self, "_last_diff_result", None)
        if result is None:
            messagebox.showerror("No Diff", "Run Diff first.")
            return

        output = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML", "*.yaml *.yml"), ("All", "*.*")],
            initialfile="patches.yaml",
        )
        if not output:
            return

        payload = {
            "patches": [
                {
                    "offset": d.offset,
                    "before": f"0x{d.before:02X}" if d.before is not None else None,
                    "value": f"0x{d.after:02X}" if d.after is not None else None,
                }
                for d in result.differences
                if d.after is not None
            ]
        }

        Path(output).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        messagebox.showinfo("Export Complete", f"Wrote patch YAML:\n{output}")

    def _run_hex_view(self) -> None:
        file_path = self.hex_file_var.get().strip()
        if not file_path:
            messagebox.showerror("Input Error", "Please select a .syx file.")
            return
        try:
            rendered = hex_dump_file(file_path)
            self.hex_text.delete("1.0", tk.END)
            self.hex_text.insert("1.0", rendered)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Hex View Error", str(exc))

    def _apply_patch(self) -> None:
        template = self.template_var.get().strip()
        patch_yaml = self.patch_yaml_var.get().strip()
        output = self.output_var.get().strip()

        if not template or not patch_yaml or not output:
            messagebox.showerror(
                "Input Error", "Template .syx, patch YAML, and output .syx are all required."
            )
            return

        try:
            out = patch_syx_file(template, patch_yaml, output, strict_before=True)
            messagebox.showinfo("Patch Complete", f"Patched file saved:\n{out}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Patch Error", str(exc))

    def _validate_events_yaml(self) -> None:
        events_path = self.events_yaml_var.get().strip()
        if not events_path:
            messagebox.showerror("Input Error", "Please choose an events YAML file.")
            return

        try:
            assignment = load_event_assignment_yaml(events_path)
            event_count = len(assignment.events)
            self._log_events(
                "Validation OK: "
                f"version={assignment.version} "
                f"total_steps={assignment.pattern.total_steps} events={event_count}"
            )
            messagebox.showinfo("Validation OK", f"Events YAML is valid.\nEvents: {event_count}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Validation Error", str(exc))

    def _generate_syx_from_events(self) -> None:
        events_path = self.events_yaml_var.get().strip()
        output_path = self.events_output_var.get().strip() or str(default_output_file_for_events(events_path))
        self.events_output_var.set(output_path)

        if not events_path or not output_path:
            messagebox.showerror(
                "Input Error",
                "events YAML and output .syx are required.",
            )
            return

        try:
            result = build_syx_from_events(
                events_yaml=events_path,
                output_file=output_path,
            )
            self.replay_file_var.set(str(result.output_file))
            self._log_events(f"Build complete: output={result.output_file} events={result.written_events}")
            for warning in result.warnings:
                self._log_events(f"Warning: {warning}")

            messagebox.showinfo(
                "Build Complete",
                f"Generated .syx:\n{result.output_file}\n\n"
                "Replay file field was auto-filled in MIDI tab.",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Build Error", str(exc))


def run_gui() -> None:
    """Start Tkinter analysis GUI."""
    root = tk.Tk()
    AnalysisGui(root)
    root.mainloop()
