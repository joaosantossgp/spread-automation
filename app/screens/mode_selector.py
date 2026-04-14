import customtkinter as ctk

from app.widgets import _font, _pair
from themes.tokens import RADIUS, DS


class ModeSelector(ctk.CTkFrame):
    """Landing screen to select operation mode."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="Select Execution Mode",
            font=_font("h1"),
            text_color=_pair("foreground"),
        )
        title.grid(row=1, column=0, pady=(0, 30))

        # Buttons container
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.grid(row=2, column=0)

        # Mode 1A Button
        btn_1a = ctk.CTkButton(
            btn_container,
            text="Mode 1A\n\nSingle Period Update",
            font=_font("h3"),
            width=220,
            height=140,
            fg_color=_pair("primary"),
            hover_color=_pair("primary_hover"),
            text_color=_pair("primary_foreground"),
            corner_radius=RADIUS["lg"],
            command=lambda: self.winfo_toplevel().show_screen("Screen1A"),
        )
        btn_1a.grid(row=0, column=0, padx=14)

        # Mode 1B Button
        btn_1b = ctk.CTkButton(
            btn_container,
            text="Mode 1B\n\nMulti-Period Generation",
            font=_font("h3"),
            width=220,
            height=140,
            fg_color=_pair("primary"),
            hover_color=_pair("primary_hover"),
            text_color=_pair("primary_foreground"),
            corner_radius=RADIUS["lg"],
            command=lambda: self.winfo_toplevel().show_screen("Screen1B"),
        )
        btn_1b.grid(row=0, column=1, padx=14)

        # Mode 2 Button
        btn_2 = ctk.CTkButton(
            btn_container,
            text="Mode 2\n\nPDF Ingestion & Review",
            font=_font("h3"),
            width=220,
            height=140,
            fg_color=_pair("primary"),
            hover_color=_pair("primary_hover"),
            text_color=_pair("primary_foreground"),
            corner_radius=RADIUS["lg"],
            command=lambda: self.winfo_toplevel().show_screen("Screen2"),
        )
        btn_2.grid(row=0, column=2, padx=14)
