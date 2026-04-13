# app/screens/screen_1a.py
# Mode 1A screen — Design System UI with full operator controls (2026-04-13).
#
# Operator controls restored vs. legacy gui.py:
#   • Auto-detect columns   — checkbox disables Src/Dst column fields and calls
#                             Mode1AWorkflow.detect_target_slot() at execution time.
#   • Multi-period toggle   — checkbox passes multi_period=True to workflow.execute()
#                             so the prior period is filled first, then the current.

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
from engine.workflow_1a import Mode1AWorkflow
from themes.tokens import DS, RADIUS, BORDER_WIDTH


class Screen1A(ctk.CTkFrame):
    """Mode 1A: fill an existing Spread Proxy from a CVM source file.

    Operator controls
    -----------------
    Auto-detect columns:
        When checked the Src / Dest column fields are disabled.  The engine's
        slot-detection logic (``Mode1AWorkflow.detect_target_slot``) infers the
        correct target columns from the Spread's internal period grid at run time.

    Multi-period:
        When checked the engine fills *both* the prior period and the current
        period in a single pass (``multi_period=True`` path in workflow.execute).
        This mirrors the legacy "Preencher 2 períodos de uma vez" checkbox in
        ``app/gui.py``.
    """

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", DS["background"])
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)   # log area expands (row index shifted +1)

        # ── Page header ──────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Mode 1A",
            font=_font("h1"),
            text_color=_pair("foreground"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Fill existing Spread Proxy from a CVM source file",
            font=_font("body"),
            text_color=_pair("muted_foreground"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # ── File selection card ───────────────────────────────────────────
        files_card = StyledCard(self, padding=0)
        files_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(16, 0))
        files_card.columnconfigure(0, weight=1)

        SectionHeading(files_card, title="Files").pack(
            fill="x", padx=14, pady=(14, 8)
        )

        self.source_picker = FilePickerWidget(files_card, label="Source (CVM Excel):")
        self.source_picker.pack(fill="x", padx=1, pady=(0, 1))

        sep = ctk.CTkFrame(files_card, height=1, fg_color=_pair("border"), corner_radius=0)
        sep.pack(fill="x", padx=14)

        self.spread_picker = FilePickerWidget(files_card, label="Spread Proxy:")
        self.spread_picker.pack(fill="x", padx=1, pady=(1, 0))

        # ── Settings card ─────────────────────────────────────────────────
        settings_card = StyledCard(self, padding=14)
        settings_card.grid(row=2, column=0, sticky="ew", padx=24, pady=(12, 0))
        settings_card.columnconfigure((0, 1, 2, 3), weight=1)

        SectionHeading(settings_card, title="Settings").grid(
            row=0, column=0, columnspan=4, sticky="ew", pady=(0, 12)
        )

        # Company + Period
        self.company_field = LabeledField(
            settings_card, label="Company", placeholder="e.g. Minerva"
        )
        self.company_field.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        self.period_field = LabeledField(
            settings_card, label="Period", placeholder="e.g. 4T24"
        )
        self.period_field.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))

        self.dest_col_field = LabeledField(
            settings_card, label="Dest Column", placeholder="auto", width=80
        )
        self.dest_col_field.grid(row=1, column=2, sticky="ew", padx=(0, 10), pady=(0, 10))

        self.prior_col_field = LabeledField(
            settings_card, label="Prior Col (opt.)", placeholder="auto", width=80
        )
        self.prior_col_field.grid(row=1, column=3, sticky="ew", pady=(0, 10))

        # Entity type row
        entity_row = ctk.CTkFrame(settings_card, fg_color="transparent", corner_radius=0)
        entity_row.grid(row=2, column=0, columnspan=4, sticky="w", pady=(2, 10))

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

        # ── Operator controls card ────────────────────────────────────────
        # Restores legacy gui.py controls: auto-detect columns + multi-period fill.
        ops_card = StyledCard(self, padding=14)
        ops_card.grid(row=3, column=0, sticky="ew", padx=24, pady=(10, 0))
        ops_card.columnconfigure(0, weight=1)

        SectionHeading(ops_card, title="Operator Controls").grid(
            row=0, column=0, sticky="ew", pady=(0, 10)
        )

        ops_inner = ctk.CTkFrame(ops_card, fg_color="transparent", corner_radius=0)
        ops_inner.grid(row=1, column=0, sticky="w")

        # Auto-detect columns checkbox
        self.auto_detect_var = ctk.BooleanVar(value=True)
        self._auto_detect_cb = ctk.CTkCheckBox(
            ops_inner,
            text="Auto-detect Src / Dest columns from Spread grid",
            variable=self.auto_detect_var,
            font=_font("body"),
            text_color=_pair("foreground"),
            fg_color=_pair("primary"),
            border_color=_pair("border"),
            hover_color=_pair("primary_hover"),
            command=self._on_auto_detect_toggle,
        )
        self._auto_detect_cb.pack(side="left", padx=(0, 32))

        # Multi-period checkbox
        self.multi_period_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            ops_inner,
            text="Fill prior + current period (multi-period)",
            variable=self.multi_period_var,
            font=_font("body"),
            text_color=_pair("foreground"),
            fg_color=_pair("primary"),
            border_color=_pair("border"),
            hover_color=_pair("primary_hover"),
        ).pack(side="left")

        # Initialise column field state to match default checkbox state (True → disabled)
        self._on_auto_detect_toggle()

        # ── Action row ────────────────────────────────────────────────────
        action_row = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        action_row.grid(row=4, column=0, sticky="ew", padx=24, pady=(16, 0))
        action_row.columnconfigure(1, weight=1)

        self.run_btn = ctk.CTkButton(
            action_row,
            text="Execute Mode 1A",
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

        # ── Log card ──────────────────────────────────────────────────────
        log_card = StyledCard(self, padding=0)
        log_card.grid(row=5, column=0, sticky="nsew", padx=24, pady=(12, 20))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)

        SectionHeading(log_card, title="Log").pack(
            fill="x", padx=14, pady=(14, 8)
        )

        self.log_box = ctk.CTkTextbox(
            log_card,
            font=_font("mono"),
            fg_color=_pair("card"),
            border_width=0,
            corner_radius=0,
            text_color=_pair("foreground"),
            scrollbar_button_color=_pair("scrollbar"),
            scrollbar_button_hover_color=_pair("scrollbar_hover"),
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True, padx=1, pady=(0, 1))

    # ── Operator-control callbacks ────────────────────────────────────────

    def _on_auto_detect_toggle(self) -> None:
        """Enable/disable column fields based on the auto-detect checkbox state."""
        auto = self.auto_detect_var.get()
        state = "disabled" if auto else "normal"
        # Directly access the CTkEntry inside LabeledField
        self.dest_col_field._entry.configure(state=state)
        self.prior_col_field._entry.configure(state=state)
        if auto:
            # Clear any manually entered values so they don't shadow auto-detect
            self.dest_col_field.set("")
            self.prior_col_field.set("")

    # ── Teardown guard ───────────────────────────────────────────────────

    def _widget_alive(self) -> bool:
        """Return True only if the widget tree still exists.

        Daemon threads must call this before touching any Tk widget.  The root
        window sets ``_destroyed = True`` before calling destroy(), which lets
        threads bail out before Tk raises "invalid command name" errors.
        """
        try:
            root = self.winfo_toplevel()
            if getattr(root, "_destroyed", False):
                return False
            return bool(self.winfo_exists())
        except Exception:
            return False

    # ── Log helper ───────────────────────────────────────────────────────

    def _log(self, text: str):
        if not self._widget_alive():
            return
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # backward-compat alias used in older call sites
    def log(self, text: str):
        self._log(text)

    # ── Workflow ──────────────────────────────────────────────────────────

    def _run(self):
        source = self.source_picker.get_path()
        spread = self.spread_picker.get_path()
        company = self.company_field.get().strip()
        period = self.period_field.get().strip()
        entity = self.entity_var.get()
        auto_detect = self.auto_detect_var.get()
        multi_period = self.multi_period_var.get()

        # Column values — only used when auto-detect is off
        dest_col = self.dest_col_field.get().strip() if not auto_detect else None
        prior_col = self.prior_col_field.get().strip() if not auto_detect else None

        if not all([source, spread, company, period]):
            self._log("[!] Fill in Source, Spread, Company, and Period before running.")
            return

        if not auto_detect and not dest_col:
            self._log("[!] Enter a Dest Column or enable Auto-detect.")
            return

        self.run_btn.configure(state="disabled")
        self.progress.update("Starting…", 0.05)
        mode_label = "multi-period" if multi_period else "single-period"
        col_label = "auto-detect" if auto_detect else f"dest={dest_col}"
        self._log(f"[*] Mode 1A — {company} {period}  [{mode_label} | {col_label}]")

        threading.Thread(
            target=self._execute,
            args=(source, spread, company, period, dest_col, prior_col, entity, multi_period, auto_detect),
            daemon=True,
        ).start()

    def _execute(
        self,
        source: str,
        spread: str,
        company: str,
        period: str,
        dest_col: str | None,
        prior_col: str | None,
        entity: str,
        multi_period: bool,
        auto_detect: bool,
    ):
        try:
            entity_enum = (
                EntityType.CONSOLIDATED if entity == "consolidated" else EntityType.INDIVIDUAL
            )
            workflow = Mode1AWorkflow()

            # Auto-detect: resolve columns before execution and surface them to log
            if auto_detect:
                self.progress.update("Detecting columns…", 0.15)
                slot = workflow.detect_target_slot(spread, period)
                if not slot.has_available_slot:
                    if self._widget_alive():
                        self.progress.update("Failed", 0.0)
                        self._log(f"[!] Slot detection failed: {slot.message}")
                    return
                dest_col = slot.destination_column
                prior_col = slot.source_column
                self._log(f"    Detected  Src={prior_col}  Dst={dest_col}  ({slot.message})")

            self.progress.update("Running workflow…", 0.4)

            result = workflow.execute(
                source_path=source,
                spread_path=spread,
                company=company,
                period=period,
                dest_col=dest_col,
                prior_col=prior_col or None,
                entity_type=entity_enum,
                multi_period=multi_period,
            )

            if not self._widget_alive():
                return

            self.progress.update("Done", 1.0)
            self._log("[+] Workflow completed successfully.")

            # result is list[dict] for multi-period, dict for single
            if isinstance(result, list):
                for r in result:
                    per_label = r.get("period", "?")
                    val = r.get("validation", {})
                    self._log(
                        f"    [{per_label}]  Mapped: {r.get('mapped_count')}  "
                        f"Valid: {val.get('is_valid')}  "
                        f"Missing: {len(val.get('missing', []))}"
                    )
            else:
                val = result.get("validation", {})
                self._log(f"    Mapped  : {result.get('mapped_count')} items")
                self._log(
                    f"    Valid   : {val.get('is_valid')}  |  Missing: {len(val.get('missing', []))}"
                )

        except Exception:
            if self._widget_alive():
                self.progress.update("Failed", 0.0)
                self._log(f"[-] Workflow failed:\n{traceback.format_exc()}")
        finally:
            if self._widget_alive():
                self.run_btn.configure(state="normal")
