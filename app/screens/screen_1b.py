# app/screens/screen_1b.py
from __future__ import annotations

import threading
import traceback

import customtkinter as ctk

from app.widgets import (
    FilePickerWidget,
    LabeledField,
    ProgressWidget,
    SectionHeading,
    StyledCard,
    _font,
    _pair,
)
from core.models import EntityType
from core.exceptions import TemplateNotAvailableError
from engine.workflow_1b import Mode1BWorkflow
from themes.tokens import DS, RADIUS, BORDER_WIDTH


class Screen1B(ctk.CTkFrame):
    """Mode 1B: generates a new multi-period Proxy Spread from a blank template."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", DS["background"])
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)  # Expand the scrollable area

        self._rows = []  # To hold data for each period row

        # ── Page header ──────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        header.columnconfigure(1, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back",
            font=_font("body_sm"),
            width=60,
            fg_color="transparent",
            text_color=_pair("primary"),
            hover_color=_pair("muted"),
            command=lambda: self.winfo_toplevel().show_screen("ModeSelector"),
        )
        back_btn.grid(row=0, column=0, sticky="w", padx=(0, 16))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            title_frame,
            text="Mode 1B: Multi-Period Input",
            font=_font("h1"),
            text_color=_pair("foreground"),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Build a new Spread Proxy from multiple CVM source files",
            font=_font("body"),
            text_color=_pair("muted_foreground"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # ── Global Settings Card ─────────────────────────────────────────
        settings_card = StyledCard(self, padding=14)
        settings_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        settings_card.columnconfigure((0, 1, 2, 3), weight=1)

        self.company_field = LabeledField(
            settings_card, label="Company Name", placeholder="e.g. Minerva"
        )
        self.company_field.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 20))

        # Entity type row
        entity_row = ctk.CTkFrame(settings_card, fg_color="transparent", corner_radius=0)
        entity_row.grid(row=0, column=2, columnspan=2, sticky="w", pady=(20, 0))

        ctk.CTkLabel(
            entity_row,
            text="Entity type:",
            font=_font("label"),
            text_color=_pair("foreground"),
        ).pack(side="left", padx=(0, 12))

        self.entity_var = ctk.StringVar(value="consolidated")
        for label, value in (("Consolidated", "consolidated"), ("Individual", "individual")):
            ctk.CTkRadioButton(
                entity_row,
                text=label,
                variable=self.entity_var,
                value=value,
                font=_font("body"),
                text_color=_pair("foreground"),
                fg_color=_pair("primary"),
                border_color=_pair("border"),
                hover_color=_pair("primary_hover"),
            ).pack(side="left", padx=(0, 16))

        self.dest_picker = FilePickerWidget(
            settings_card, label="Output Spread:", mode="save"
        )
        self.dest_picker.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(15, 0))

        # ── Header for sources + Add button ──────────────────────────────
        sources_header = ctk.CTkFrame(self, fg_color="transparent")
        sources_header.grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 0))
        sources_header.columnconfigure(0, weight=1)

        SectionHeading(sources_header, title="Periods / Source Files").grid(
            row=0, column=0, sticky="w"
        )

        add_btn = ctk.CTkButton(
            sources_header,
            text="+ Add Period",
            font=_font("body_sm"),
            width=100,
            fg_color=_pair("secondary"),
            text_color=_pair("secondary_foreground"),
            hover_color=_pair("secondary_hover"),
            command=self._add_period_row,
        )
        add_btn.grid(row=0, column=1, sticky="e")

        # ── Scrollable Sources List ──────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=_pair("scrollbar"),
            scrollbar_button_hover_color=_pair("scrollbar_hover"),
        )
        self.scroll.grid(row=3, column=0, sticky="nsew", padx=24, pady=8)

        # Add initial row
        self._add_period_row()

        # ── Action / Log row ─────────────────────────────────────────────
        bottom_panel = ctk.CTkFrame(self, fg_color="transparent")
        bottom_panel.grid(row=4, column=0, sticky="ew", padx=24, pady=(10, 20))
        bottom_panel.columnconfigure(0, weight=1)

        action_row = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        action_row.pack(fill="x", pady=(0, 10))
        action_row.columnconfigure(1, weight=1)

        self.run_btn = ctk.CTkButton(
            action_row,
            text="Execute Mode 1B",
            font=_font("body"),
            width=180,
            height=38,
            fg_color=_pair("primary"),
            hover_color=_pair("primary_hover"),
            text_color=_pair("primary_foreground"),
            corner_radius=RADIUS["base"],
            command=self._run,
        )
        self.run_btn.grid(row=0, column=0, sticky="w")

        self.progress = ProgressWidget(action_row)
        self.progress.grid(row=0, column=1, sticky="ew", padx=(20, 0))

        log_card = StyledCard(bottom_panel, padding=0)
        log_card.pack(fill="x", expand=True)
        log_card.columnconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(
            log_card,
            height=120,
            font=_font("mono"),
            fg_color=_pair("card"),
            border_width=0,
            corner_radius=0,
            text_color=_pair("foreground"),
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True, padx=1, pady=1)

    def _add_period_row(self):
        row_frame = StyledCard(self.scroll, padding=10)
        row_frame.pack(fill="x", pady=(0, 10))

        # Close button for this row
        top_bar = ctk.CTkFrame(row_frame, fg_color="transparent")
        top_bar.pack(fill="x")
        
        remove_btn = ctk.CTkButton(
            top_bar,
            text="×",
            width=20,
            height=20,
            font=_font("h3"),
            fg_color="transparent",
            text_color=_pair("muted_foreground"),
            hover_color=_pair("muted"),
            command=lambda: self._remove_row(row_frame),
        )
        remove_btn.pack(side="right")

        picker = FilePickerWidget(row_frame, label="CVM File:")
        picker.pack(fill="x", pady=(0, 10))

        fields_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        fields_row.pack(fill="x")

        period_field = LabeledField(fields_row, label="Period (e.g. 2024)", width=120)
        period_field.pack(side="left", padx=(14, 20))

        col_field = LabeledField(fields_row, label="Col (e.g. E)", width=80)
        col_field.pack(side="left")

        # Save refs
        self._rows.append({
            "frame": row_frame,
            "picker": picker,
            "period": period_field,
            "col": col_field,
        })

    def _remove_row(self, frame_to_remove):
        for data in self._rows:
            if data["frame"] == frame_to_remove:
                self._rows.remove(data)
                frame_to_remove.destroy()
                break

    # ── Teardown guard ───────────────────────────────────────────────────
    def _widget_alive(self) -> bool:
        try:
            root = self.winfo_toplevel()
            if getattr(root, "_destroyed", False):
                return False
            return bool(self.winfo_exists())
        except Exception:
            return False

    def _log(self, text: str):
        if not self._widget_alive():
            return
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # ── Workflow ──────────────────────────────────────────────────────────
    def _run(self):
        company = self.company_field.get().strip()
        entity = self.entity_var.get()
        dest_spread = self.dest_picker.get_path()

        if not company or not dest_spread:
            self._log("[!] Please fill Company Name and Output Spread.")
            return

        if not self._rows:
            self._log("[!] Please add at least one period.")
            return

        datasets = []
        for rdata in self._rows:
            path = rdata["picker"].get_path()
            period = rdata["period"].get().strip()
            col = rdata["col"].get().strip()
            if not path or not period or not col:
                self._log("[!] Please fill Source, Period, and Col in all rows.")
                return
            
            datasets.append({
                "source_path": path,
                "company": company,
                "period": period,
                "dest_col": col,
                "entity_type": EntityType.CONSOLIDATED if entity == "consolidated" else EntityType.INDIVIDUAL,
                "source_type": "cvm_excel"  # Hardcoded default for now, could be derived from ext
            })

        self.run_btn.configure(state="disabled")
        self.progress.update("Starting Workflow 1B...", 0.1)
        self._log(f"[*] Mode 1B — Generating full spread for {company} ({len(datasets)} periods)")

        threading.Thread(
            target=self._execute,
            args=(datasets, dest_spread),
            daemon=True,
        ).start()

    def _execute(self, datasets: list[dict], dest_spread: str):
        try:
            workflow = Mode1BWorkflow.from_default()
            self.progress.update("Running mapped periods...", 0.3)

            result = workflow.execute(datasets=datasets, dest_spread=dest_spread)

            if not self._widget_alive():
                return
                
            if "error" in result:
                self.progress.update("Failed", 0.0)
                self._log(f"[!] Validation Error: {result['error']['message']}")
                return

            self.progress.update("Done", 1.0)
            self._log("[+] Mode 1B completed successfully.")

            reports = result.get("reports", {})
            for per, rep in reports.items():
                self._log(f"    [{per}] Mapped: {rep.get('mapped_count')} | Valid: {rep.get('is_valid')}")

        except TemplateNotAvailableError as ex:
            if self._widget_alive():
                self.progress.update("Failed", 0.0)
                self._log(f"[-] Missing Template: {ex}")
                self._log("    Mode 1B requires the blank Spread Proxy template, which has not yet been shipped in this repository (see Issue #17).")
        except Exception:
            if self._widget_alive():
                self.progress.update("Failed", 0.0)
                self._log(f"[-] Execution failed:\n{traceback.format_exc()}")
        finally:
            if self._widget_alive():
                self.run_btn.configure(state="normal")
