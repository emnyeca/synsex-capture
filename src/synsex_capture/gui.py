"""Tkinter GUI for focused SysEx analysis and partial rewrite workflow."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import yaml

from .diffing import DiffResult, diff_syx_files, format_diff
from .hexview import hex_dump_file
from .patcher import patch_syx_file


class AnalysisGui:
    """A small GUI to support offset discovery and selective byte patching."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("synsex-capture: Pattern Analysis Assistant")
        self.root.geometry("1100x760")

        self.file1_var = tk.StringVar()
        self.file2_var = tk.StringVar()
        self.hex_file_var = tk.StringVar()
        self.template_var = tk.StringVar()
        self.patch_yaml_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.diff_limit_var = tk.StringVar(value="256")

        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab_diff = ttk.Frame(notebook)
        tab_hex = ttk.Frame(notebook)
        tab_patch = ttk.Frame(notebook)

        notebook.add(tab_diff, text="Diff & Mapping")
        notebook.add(tab_hex, text="Hex Viewer")
        notebook.add(tab_patch, text="Selective Patch")

        self._build_diff_tab(tab_diff)
        self._build_hex_tab(tab_hex)
        self._build_patch_tab(tab_patch)

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

    def _pick_file(self, target_var: tk.StringVar, filetypes: list[tuple[str, str]] | None = None) -> None:
        path = filedialog.askopenfilename(filetypes=filetypes or [("SysEx", "*.syx"), ("All", "*.*")])
        if path:
            target_var.set(path)

    def _pick_save_output(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".syx", filetypes=[("SysEx", "*.syx"), ("All", "*.*")])
        if path:
            self.output_var.set(path)

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


def run_gui() -> None:
    """Start Tkinter analysis GUI."""
    root = tk.Tk()
    AnalysisGui(root)
    root.mainloop()
