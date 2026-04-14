# app/screens/screen_2.py
# Mode 2A / 2B screen — PDF ingestion with confidence-based review table.
#
# Flow:
#   1. User selects a PDF source file.
#   2. Picks mode: 2A (existing spread proxy) or 2B (blank template → new file).
#   3. Runs the appropriate workflow; auto-accepted rows are written immediately.
#   4. pending_review rows are shown in a scrollable table with accept/reject toggles.
#   5. User can set a confidence threshold for bulk-accept.
#   6. "Confirm Selections" writes only accepted pending rows and logs rejected ones.

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
from engine.workflow_2a import Workflow2A
from engine.workflow_2b import Workflow2B
from spread import SpreadWriter
from core.schema import SpreadSchema
from themes.tokens import DS, RADIUS, BORDER_WIDTH


class Screen2(ctk.CTkFrame):
    """Mode 2A/2B: ingest PDF, review fuzzy-matched rows, confirm writes."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", DS["background"])
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)  # review table expands

        self._pending_items: list[dict] = []       # pending_review items from workflow
        self._row_vars:      list[ctk.BooleanVar] = []  # one BooleanVar per row
        self._last_result:   dict | None = None    # full workflow result

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        header.columnconfigure(1, weight=1)

        ctk.CTkButton(
            header,
            text="← Back",
            font=_font("body_sm"),
            width=60,
            fg_color="transparent",
            text_color=_pair("primary"),
            hover_color=_pair("muted"),
            command=lambda: self.winfo_toplevel().show_screen("ModeSelector"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 16))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            title_frame,
            text="Mode 2 — PDF Ingestion",
            font=_font("h1"),
            text_color=_pair("foreground"),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Extract accounts from a PDF and review fuzzy-matched mappings",
            font=_font("body"),
            text_color=_pair("muted_foreground"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # ── Settings Card ────────────────────────────────────────────────
        settings_card = StyledCard(self, padding=14)
        settings_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        settings_card.columnconfigure((0, 1, 2, 3), weight=1)

        # Mode radio: 2A vs 2B
        mode_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        mode_row.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 14))

        ctk.CTkLabel(
            mode_row,
            text="Sub-mode:",
            font=_font("label"),
            text_color=_pair("foreground"),
        ).pack(side="left", padx=(0, 12))

        self.mode_var = ctk.StringVar(value="2a")
        for label, value in (("2A — update existing spread", "2a"), ("2B — create from blank template", "2b")):
            ctk.CTkRadioButton(
                mode_row,
                text=label,
                variable=self.mode_var,
                value=value,
                font=_font("body"),
                text_color=_pair("foreground"),
                fg_color=_pair("primary"),
                border_color=_pair("border"),
                hover_color=_pair("primary_hover"),
                command=self._on_mode_change,
            ).pack(side="left", padx=(0, 20))

        # PDF source
        self.pdf_picker = FilePickerWidget(
            settings_card,
            label="PDF Source:",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        self.pdf_picker.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 8))

        # Spread proxy (2A) / output path (2B)
        self.spread_picker = FilePickerWidget(
            settings_card,
            label="Spread Proxy:",
        )
        self.spread_picker.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, 8))

        self.dest_picker = FilePickerWidget(
            settings_card,
            label="Output Spread:",
            mode="save",
        )
        self.dest_picker.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 8))

        # Company / Period / Dest col / Prior col
        self.company_field = LabeledField(settings_card, label="Company", placeholder="e.g. Minerva")
        self.company_field.grid(row=4, column=0, sticky="ew", padx=(0, 10), pady=(8, 0))

        self.period_field = LabeledField(settings_card, label="Period", placeholder="e.g. 4T24")
        self.period_field.grid(row=4, column=1, sticky="ew", padx=(0, 10), pady=(8, 0))

        self.dest_col_field = LabeledField(settings_card, label="Dest Col", placeholder="e.g. E", width=80)
        self.dest_col_field.grid(row=4, column=2, sticky="ew", padx=(0, 10), pady=(8, 0))

        self.prior_col_field = LabeledField(settings_card, label="Prior Col (opt.)", placeholder="auto", width=80)
        self.prior_col_field.grid(row=4, column=3, sticky="ew", pady=(8, 0))

        # Entity type
        entity_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        entity_row.grid(row=5, column=0, columnspan=4, sticky="w", pady=(12, 0))

        ctk.CTkLabel(entity_row, text="Entity type:", font=_font("label"),
                     text_color=_pair("foreground")).pack(side="left", padx=(0, 12))

        self.entity_var = ctk.StringVar(value="consolidated")
        for label, value in (("Consolidated", "consolidated"), ("Individual", "individual")):
            ctk.CTkRadioButton(
                entity_row, text=label, variable=self.entity_var, value=value,
                font=_font("body"), text_color=_pair("foreground"),
                fg_color=_pair("primary"), border_color=_pair("border"),
                hover_color=_pair("primary_hover"),
            ).pack(side="left", padx=(0, 16))

        # Initialise visibility
        self._on_mode_change()

        # ── Action row ───────────────────────────────────────────────────
        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 8))
        action_row.columnconfigure(1, weight=1)

        self.run_btn = ctk.CTkButton(
            action_row,
            text="Run PDF Ingestion",
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

        # ── Review Table header ──────────────────────────────────────────
        review_header = ctk.CTkFrame(self, fg_color="transparent")
        review_header.grid(row=3, column=0, sticky="ew", padx=24, pady=(4, 0))
        review_header.columnconfigure(0, weight=1)

        SectionHeading(review_header, title="Pending Review").grid(row=0, column=0, sticky="w")

        # Threshold + bulk accept row
        threshold_row = ctk.CTkFrame(review_header, fg_color="transparent")
        threshold_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        ctk.CTkLabel(threshold_row, text="Bulk-accept ≥", font=_font("body_sm"),
                     text_color=_pair("foreground")).pack(side="left", padx=(0, 6))

        self.threshold_var = ctk.StringVar(value="0.80")
        ctk.CTkEntry(
            threshold_row,
            textvariable=self.threshold_var,
            width=55,
            font=_font("body_sm"),
            fg_color=_pair("card"),
            border_color=_pair("border"),
            text_color=_pair("foreground"),
            corner_radius=RADIUS["md"],
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            threshold_row,
            text="Apply Threshold",
            font=_font("body_sm"),
            width=130,
            fg_color=_pair("secondary"),
            hover_color=_pair("secondary_hover"),
            text_color=_pair("secondary_foreground"),
            command=self._apply_threshold,
        ).pack(side="left", padx=(0, 20))

        self.confirm_btn = ctk.CTkButton(
            threshold_row,
            text="Confirm Selections",
            font=_font("body"),
            width=160,
            height=34,
            fg_color=_pair("primary"),
            hover_color=_pair("primary_hover"),
            text_color=_pair("primary_foreground"),
            corner_radius=RADIUS["base"],
            state="disabled",
            command=self._confirm,
        )
        self.confirm_btn.pack(side="left")

        # ── Scrollable review table ──────────────────────────────────────
        self.table_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=_pair("scrollbar"),
            scrollbar_button_hover_color=_pair("scrollbar_hover"),
        )
        self.table_frame.grid(row=4, column=0, sticky="nsew", padx=24, pady=(8, 8))
        self.table_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self._build_table_header()

        # ── Log ──────────────────────────────────────────────────────────
        log_card = StyledCard(self, padding=0)
        log_card.grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 20))

        self.log_box = ctk.CTkTextbox(
            log_card,
            height=90,
            font=_font("mono"),
            fg_color=_pair("card"),
            border_width=0,
            corner_radius=0,
            text_color=_pair("foreground"),
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True, padx=1, pady=1)

    # ── Mode toggle ──────────────────────────────────────────────────────

    def _on_mode_change(self):
        mode = self.mode_var.get()
        # 2A: pick existing spread; 2B: choose output save path
        if mode == "2a":
            self.spread_picker.grid()
            self.dest_picker.grid_remove()
        else:
            self.spread_picker.grid_remove()
            self.dest_picker.grid()

    # ── Table helpers ────────────────────────────────────────────────────

    def _build_table_header(self):
        cols = ["Accept", "Row", "Spread Label", "Value", "Confidence"]
        widths = [60, 50, 260, 110, 100]
        for i, (col, w) in enumerate(zip(cols, widths)):
            ctk.CTkLabel(
                self.table_frame,
                text=col,
                font=_font("label"),
                text_color=_pair("muted_foreground"),
                anchor="w",
                width=w,
            ).grid(row=0, column=i, sticky="w", padx=4, pady=(0, 6))

    def _clear_table(self):
        for widget in self.table_frame.winfo_children():
            if widget.grid_info().get("row", 0) > 0:
                widget.destroy()
        self._row_vars.clear()

    def _populate_table(self, items: list[dict]):
        self._clear_table()
        self._pending_items = items

        if not items:
            ctk.CTkLabel(
                self.table_frame,
                text="No items pending review — all mappings were auto-accepted or rejected.",
                font=_font("body"),
                text_color=_pair("muted_foreground"),
            ).grid(row=1, column=0, columnspan=5, sticky="w", padx=4, pady=8)
            return

        for r_idx, item in enumerate(items, start=1):
            var = ctk.BooleanVar(value=True)
            self._row_vars.append(var)

            ctk.CTkCheckBox(
                self.table_frame,
                text="",
                variable=var,
                width=20,
                fg_color=_pair("primary"),
                border_color=_pair("border"),
                hover_color=_pair("primary_hover"),
            ).grid(row=r_idx, column=0, padx=4, pady=2, sticky="w")

            ctk.CTkLabel(
                self.table_frame,
                text=str(item.get("spread_row", "—")),
                font=_font("body_sm"),
                text_color=_pair("foreground"),
                anchor="w",
                width=50,
            ).grid(row=r_idx, column=1, padx=4, pady=2, sticky="w")

            ctk.CTkLabel(
                self.table_frame,
                text=item.get("label", "—"),
                font=_font("body_sm"),
                text_color=_pair("foreground"),
                anchor="w",
                width=260,
            ).grid(row=r_idx, column=2, padx=4, pady=2, sticky="w")

            ctk.CTkLabel(
                self.table_frame,
                text=item.get("value") or "—",
                font=_font("body_sm"),
                text_color=_pair("foreground"),
                anchor="w",
                width=110,
            ).grid(row=r_idx, column=3, padx=4, pady=2, sticky="w")

            conf = item.get("confidence", 0.0)
            conf_color = (
                _pair("chart_1")[0] if conf >= 0.85
                else _pair("chart_2")[0] if conf >= 0.70
                else _pair("destructive")[0]
            )
            ctk.CTkLabel(
                self.table_frame,
                text=f"{conf:.0%}",
                font=_font("body_sm"),
                text_color=(conf_color, conf_color),
                anchor="w",
                width=100,
            ).grid(row=r_idx, column=4, padx=4, pady=2, sticky="w")

        self.confirm_btn.configure(state="normal")

    # ── Threshold ────────────────────────────────────────────────────────

    def _apply_threshold(self):
        try:
            thresh = float(self.threshold_var.get())
        except ValueError:
            self._log("[!] Invalid threshold — enter a number between 0 and 1.")
            return
        for var, item in zip(self._row_vars, self._pending_items):
            var.set(item.get("confidence", 0.0) >= thresh)

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

    # ── Run ingestion ────────────────────────────────────────────────────

    def _run(self):
        mode = self.mode_var.get()
        pdf    = self.pdf_picker.get_path()
        spread = self.spread_picker.get_path() if mode == "2a" else None
        dest   = self.dest_picker.get_path()   if mode == "2b" else None
        company  = self.company_field.get().strip()
        period   = self.period_field.get().strip()
        dest_col = self.dest_col_field.get().strip()
        prior_col = self.prior_col_field.get().strip() or None
        entity   = self.entity_var.get()

        if not pdf or not company or not period or not dest_col:
            self._log("[!] Fill in PDF, Company, Period, and Dest Column.")
            return
        if mode == "2a" and not spread:
            self._log("[!] Select a Spread Proxy for Mode 2A.")
            return
        if mode == "2b" and not dest:
            self._log("[!] Select an output path for Mode 2B.")
            return

        self.run_btn.configure(state="disabled")
        self.confirm_btn.configure(state="disabled")
        self._clear_table()
        self.progress.update("Starting PDF ingestion…", 0.05)
        self._log(f"[*] Mode {mode.upper()} — {company} {period}")

        entity_enum = EntityType.CONSOLIDATED if entity == "consolidated" else EntityType.INDIVIDUAL
        threading.Thread(
            target=self._execute,
            args=(mode, pdf, spread, dest, company, period, dest_col, prior_col, entity_enum),
            daemon=True,
        ).start()

    def _execute(self, mode, pdf, spread, dest, company, period, dest_col, prior_col, entity_enum):
        try:
            if mode == "2a":
                workflow = Workflow2A()
                result = workflow.execute(
                    pdf_path=pdf,
                    spread_path=spread,
                    company=company,
                    period=period,
                    dest_col=dest_col,
                    prior_col=prior_col,
                    entity_type=entity_enum,
                )
            else:
                workflow = Workflow2B()
                result = workflow.execute(
                    pdf_path=pdf,
                    dest_path=dest,
                    company=company,
                    period=period,
                    dest_col=dest_col,
                    prior_col=prior_col,
                    entity_type=entity_enum,
                )

            if not self._widget_alive():
                return

            self._last_result = result
            auto_count    = len(result.get("auto", []))
            pending       = result.get("pending_review", [])
            rejected_count = len(result.get("rejected", []))

            self.progress.update("Ingestion done — review pending items", 0.7)
            self._log(f"[+] Auto-accepted : {auto_count}")
            self._log(f"    Pending review : {len(pending)}")
            self._log(f"    Rejected       : {rejected_count}")

            # populate table on the main thread
            self.after(0, lambda: self._populate_table(pending))

        except Exception:
            if self._widget_alive():
                self.progress.update("Failed", 0.0)
                self._log(f"[-] Ingestion failed:\n{traceback.format_exc()}")
        finally:
            if self._widget_alive():
                self.run_btn.configure(state="normal")

    # ── Confirm ──────────────────────────────────────────────────────────

    def _confirm(self):
        if not self._last_result:
            return

        mode = self.mode_var.get()
        spread_path = (
            self.spread_picker.get_path() if mode == "2a"
            else self.dest_picker.get_path()
        )
        dest_col = self.dest_col_field.get().strip()

        accepted  = [item for var, item in zip(self._row_vars, self._pending_items) if var.get()]
        rejected  = [item for var, item in zip(self._row_vars, self._pending_items) if not var.get()]

        if not accepted and not rejected:
            self._log("[!] Nothing to confirm.")
            return

        self.confirm_btn.configure(state="disabled")
        self.progress.update("Writing confirmed items…", 0.85)

        threading.Thread(
            target=self._do_confirm,
            args=(accepted, rejected, spread_path, dest_col),
            daemon=True,
        ).start()

    def _do_confirm(self, accepted: list[dict], rejected: list[dict], spread_path: str, dest_col: str):
        try:
            from decimal import Decimal

            class _Stub:
                """Minimal duck-type for SpreadWriter.write_results expected rows."""
                def __init__(self, d):
                    self.spread_row = d["spread_row"]
                    self.value = Decimal(d["value"]) if d.get("value") else None
                    self.confidence = d.get("confidence", 0.0)
                    self.label = d.get("label", "")
                    self.layer = d.get("layer", 1)
                    self.source_account = None

            spread_schema = SpreadSchema.load()
            writer = SpreadWriter(spread_path, sheet_name=spread_schema.sheet_name)
            stubs = [_Stub(item) for item in accepted]
            writer.write_results(dest_col=dest_col, results=stubs, overwrite=False)

            from spread import Highlights
            hl = Highlights(spread_path, sheet_name=spread_schema.sheet_name)
            hl.apply_styles(col=dest_col, results=stubs)

            if not self._widget_alive():
                return

            self.progress.update("Done", 1.0)
            self._log(f"[+] Wrote {len(accepted)} confirmed items.")
            for item in rejected:
                self._log(f"    REJECTED: row {item.get('spread_row')} — {item.get('label')} (reason: user-rejected)")
        except Exception:
            if self._widget_alive():
                self.progress.update("Failed", 0.0)
                self._log(f"[-] Confirm step failed:\n{traceback.format_exc()}")
        finally:
            if self._widget_alive():
                self.confirm_btn.configure(state="normal")
