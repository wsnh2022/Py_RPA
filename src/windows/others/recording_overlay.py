from tkinter import Frame, Label, Toplevel


class RecordingOverlay(Toplevel):
    """Borderless top-right overlay shown while a recording is in progress.

    Displays the configured Stop-record hotkey so the user has a reliable
    way to end the recording without restoring the main window.
    """

    WIDTH = 260
    HEIGHT = 58
    MARGIN = 16
    BG = "#1f1f1f"

    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.93)
        except Exception:
            pass

        screen_w = self.winfo_screenwidth()
        x = screen_w - self.WIDTH - self.MARGIN
        y = self.MARGIN
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        self.configure(background=self.BG)

        body = Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        Label(
            body, text="● REC", bg=self.BG, fg="#ff3b30",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        self.shortcut_label = Label(
            body, text="", bg=self.BG, fg="#dddddd",
            font=("Segoe UI", 9),
        )
        self.shortcut_label.pack(anchor="w")

        self.refresh()
        self.lift()

    def refresh(self):
        stop_keys = (
            self.main_app.settings.settings_dict
            .get("Hotkeys", {})
            .get("Record_Stop", [])
        )
        if stop_keys:
            self.shortcut_label.configure(
                text=f"Press {self._format(stop_keys)} to stop"
            )
        else:
            self.shortcut_label.configure(
                text="No Stop hotkey set (Options → Settings → Hotkeys)"
            )

    @staticmethod
    def _format(keys):
        parts = []
        for k in keys:
            s = (
                str(k)
                .replace("Key.", "")
                .replace("_l", "")
                .replace("_r", "")
                .replace("_gr", "")
            )
            parts.append(s.upper())
        return " + ".join(parts)
