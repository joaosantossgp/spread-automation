import customtkinter as ctk
from pathlib import Path

# Apply Design System theme before any widget is created.
_THEME_PATH = Path(__file__).parent.parent / "themes" / "ctk_theme.json"
ctk.set_default_color_theme(str(_THEME_PATH))
ctk.set_appearance_mode("light")

from app.screens.screen_1a import Screen1A


class SpreadApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spread Automation")
        self.geometry("920x700")
        self.minsize(760, 560)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Shared teardown guard.  Background threads must check this flag before
        # touching any Tk widget — once True the widget tree is gone.
        self._destroyed = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.screen_1a = Screen1A(self)
        self.screen_1a.grid(row=0, column=0, sticky="nsew")

    def _on_close(self) -> None:
        """Cancel pending after-callbacks before destroying the window.

        Tkinter fires 'after' callbacks even after destroy() has been called,
        which causes 'invalid command name' errors in daemon threads that try to
        update widgets.  Setting _destroyed=True lets threads bail out early, and
        calling after_cancel on all registered ids stops queued callbacks.
        """
        self._destroyed = True
        # Cancel every pending after-callback registered on this widget.
        for after_id in self.tk.eval("after info").split():
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = SpreadApp()
    app.mainloop()
