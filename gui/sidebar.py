# sidebar.py
# Sidebar component extracted from MotorApp (Strangler Fig — Phase 2)
# Owns: project_combo, section_combo, section_info_label, section_stats_label
# Communicates upward via callbacks; holds no direct reference to MotorApp internals.

import tkinter as tk
from tkinter import ttk


class SidebarPanel(tk.Frame):
    """
    Self-contained left-panel component (~280 px wide).

    Callbacks injected at construction time — no import of MotorApp:
        on_project_changed(project_name: str)
        on_section_changed(section_name: str)
        on_new_project()
        on_manage_projects()
        on_edit_project_info()
        on_manage_sections()

    Public API (called by MotorApp to keep UI in sync):
        set_projects(names: list[str], selected: str | None)
        set_sections(names: list[str], selected: str | None)
        update_info(description: str, device_count: int, io_count: int)
        clear_info()
    """

    def __init__(self, parent: tk.Widget, colors: dict, callbacks: dict, **kwargs):
        """
        Parameter frame (main_r frame (main_panel)
        colors    : dict — COLORS token dict from theme (light, success, accent, secondary, …)
        callbacks : dict — keys match the callback names in the docstring above
        """
        super().__init__(parent, bg=colors["light"], width=280, **kwargs)
        self.pack_propagate(False)

        self._colors = colors
        self._cb = callbacks

        # StringVars exposed as properties so MotorApp can still read them if needed
        self.project_var = tk.StringVar()
        self.section_var = tk.StringVar()

        self._build()

    # ------------------------------------------------------------------ #
    #  Build                                                               #
    # ------------------------------------------------------------------ #

    def _build(self) -> None:
        self._build_project_panel()
        self._build_section_panel()
        self._build_info_panel()

    def _build_project_panel(self) -> None:
        c = self._colors
        frame = tk.Frame(self, bg=c["light"])
        frame.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(
            frame,
            text="🏗️ Project",
            bg=c["light"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        self.project_combo = ttk.Combobox(
            frame,
            textvariable=self.project_var,
            state="readonly",
            font=("Segoe UI", 9),
        )
        self.project_combo.pack(fill=tk.X, pady=(4, 6))
        self.project_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._cb.get("on_project_changed", lambda v: None)(
                self.project_var.get()
            ),
        )

        btn_row = tk.Frame(frame, bg=c["light"])
        btn_row.pack(fill=tk.X)

        self._make_button(btn_row, "New",       c["success"],   "on_new_project")
        self._make_button(btn_row, "Manage",    c["accent"],    "on_manage_projects")
        self._make_button(btn_row, "Edit Info", c["secondary"], "on_edit_project_info")

    def _build_section_panel(self) -> None:
        c = self._colors
        frame = tk.Frame(self, bg=c["light"])
        frame.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(
            frame,
            text="📂 Sections",
            bg=c["light"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        self.section_combo = ttk.Combobox(
            frame,
            textvariable=self.section_var,
            state="readonly",
            font=("Segoe UI", 9),
        )
        self.section_combo.pack(fill=tk.X, pady=(4, 6))
        self.section_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._cb.get("on_section_changed", lambda v: None)(
                self.section_var.get()
            ),
        )

        tk.Button(
            frame,
            text="✏️ Manage Sections",
            bg=c["secondary"],
            font=("Segoe UI", 8, "bold"),
            relief=tk.FLAT,
            command=lambda: self._cb.get("on_manage_sections", lambda: None)(),
        ).pack(fill=tk.X)

    def _build_info_panel(self) -> None:
        c = self._colors
        frame = tk.Frame(self, bg=c["light"])
        frame.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(
            frame,
            text="📊 Section Info",
            bg=c["light"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        self.section_info_label = tk.Label(
            frame,
            text="No section selected",
            bg=c["light"],
            font=("Segoe UI", 9),
            justify=tk.LEFT,
            wraplength=250,
        )
        self.section_info_label.pack(anchor="w", pady=(4, 2))

        self.section_stats_label = tk.Label(
            frame,
            text="Devices: 0 | I/O: 0",
            bg=c["light"],
            font=("Segoe UI", 9, "bold"),
            fg=c["accent"],
        )
        self.section_stats_label.pack(anchor="w")

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _make_button(
        self, parent: tk.Frame, text: str, bg: str, cb_key: str
    ) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            bg=bg,
            font=("Segoe UI", 8, "bold"),
            relief=tk.FLAT,
            command=lambda: self._cb.get(cb_key, lambda: None)(),
        )
        btn.pack(side=tk.LEFT, padx=(0, 4))
        return btn

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def set_projects(self, names: list, selected: str | None = None) -> None:
        """Populate the project combobox and optionally pre-select one entry."""
        self.project_combo["values"] = names
        if selected and selected in names:
            self.project_var.set(selected)
        elif names:
            self.project_var.set(names[0])
        else:
            self.project_var.set("")

    def set_sections(self, names: list, selected: str | None = None) -> None:
        """Populate the section combobox and optionally pre-select one entry."""
        self.section_combo["values"] = names
        if selected and selected in names:
            self.section_var.set(selected)
        elif names:
            self.section_var.set(names[0])
        else:
            self.section_var.set("")

    def update_info(self, description: str, device_count: int, io_count: int) -> None:
        """Refresh the Section Info panel after a section is loaded."""
        self.section_info_label.config(
            text=description if description else "No description"
        )
        self.section_stats_label.config(
            text=f"Devices: {device_count} | I/O: {io_count}"
        )

    def clear_info(self) -> None:
        """Reset info panel to its default empty state."""
        self.section_info_label.config(text="No section selected")
        self.section_stats_label.config(text="Devices: 0 | I/O: 0")
