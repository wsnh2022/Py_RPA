import copy
import json
import sys
from json import load
from os import path
from sys import argv, platform
from threading import Thread
from tkinter import (
    BOTH,
    BOTTOM,
    DISABLED,
    LEFT,
    RIGHT,
    SUNKEN,
    PhotoImage,
    W,
    X,
    messagebox,
)
from tkinter.ttk import Button, Frame, Label

from PIL import Image

from pystray import Icon, MenuItem

from hotkeys.hotkeys_manager import HotkeysManager
from macro import Macro
from utils.get_file import resource_path
from utils.macro_library import MacroLibrary as MacroLibraryRegistry
from utils.record_file_management import RecordFileManagement
from utils.user_settings import UserSettings
from utils.version import Version
from utils.warning_pop_up_save import confirm_save
from windows.main.menu_bar import MenuBar
from windows.others.library import MacroLibrary
from windows.others.recording_overlay import RecordingOverlay
from windows.window import Window


def deepcopy_dict_missing_entries(dst:dict,src:dict):
# recursively copy entries that are in src but not in dst
    for k,v in src.items():
        if k not in dst:
            dst[k] = copy.deepcopy(v)
        elif isinstance(v,dict):
            deepcopy_dict_missing_entries(dst[k],v)

class MainApp(Window):
    """Main windows of the application"""

    def __init__(self):
        super().__init__("PyMacroRecord", 350, 200)

        # Headless autoplay path: hide the root window BEFORE any window-manager
        # interaction so there's no flash. We don't know yet whether the
        # Autoplay_on_open setting is on, but we assume it is when launched with
        # a file argv (default). If it's off, we deiconify a few lines down.
        self._macro_queue = []
        self._autoplay_active = False
        macro_args = [a for a in argv[1:] if a.lower().endswith(('.pmr', '.json'))]
        if macro_args:
            self.withdraw()
        else:
            self.attributes("-topmost", 1)

        if platform == "win32":
            self.iconbitmap(resource_path(path.join("assets", "logo.ico")))

        self.settings = UserSettings(self)

        # Resolve autoplay decision now that settings are loaded.
        autoplay = bool(macro_args) and self.settings.settings_dict["Library"]["Autoplay_on_open"]
        if macro_args and not autoplay:
            # File launch but autoplay disabled — show the window.
            self.deiconify()
            self.attributes("-topmost", 1)
        self._autoplay_active = autoplay

        self.load_language()

        # For save message purpose
        self.macro_saved = False
        self.macro_recorded = False
        self.current_file = None
        self.prevent_record = False

        self.version = Version(self.settings.settings_dict, self)

        self.macro_library = MacroLibraryRegistry(self)
        self.library_window = None
        self.recording_overlay = None

        self.menu = MenuBar(self)  # Menu Bar
        self.macro = Macro(self)

        self.validate_cmd = self.register(self.validate_input)

        self.hotkeyManager = HotkeysManager(self)

        self.status_text = Label(self, text='', relief=SUNKEN, anchor=W)
        if self.settings.settings_dict["Recordings"]["Show_Events_On_Status_Bar"]:
            self.status_text.pack(side=BOTTOM, fill=X)

        # Main Buttons (Start record, stop record, start playback, stop playback)

        # Play Button
        self.playImg = PhotoImage(file=resource_path(path.join("assets", "button", "play.png")))

        self.center_frame = Frame(self)
        self.center_frame.pack(expand=True, fill=BOTH)

        # Import record if opened with .pmr / .json file arg(s).
        if macro_args:
            with open(macro_args[0], 'r', encoding='utf-8') as record:
                loaded_content = load(record)
            self.macro.import_record(loaded_content)
            self.current_file = macro_args[0]
            self._macro_queue = list(macro_args[1:])
            self.playBtn = Button(self.center_frame, image=self.playImg, command=self.macro.start_playback)
            self.macro_recorded = True
            self.macro_saved = True
        else:
            self.playBtn = Button(self.center_frame, image=self.playImg, state=DISABLED)
        self.playBtn.pack(side=LEFT, padx=50)

        # Record Button
        self.recordImg = PhotoImage(file=resource_path(path.join("assets", "button", "record.png")))
        self.recordBtn = Button(self.center_frame, image=self.recordImg, command=self.macro.start_record)
        self.recordBtn.pack(side=RIGHT, padx=50)

        # Stop Button
        self.stopImg = PhotoImage(file=resource_path(path.join("assets", "button", "stop.png")))

        record_management = RecordFileManagement(self, self.menu)

        self.bind('<Control-Shift-S>', record_management.save_macro_as)
        self.bind('<Control-s>', record_management.save_macro)
        self.bind('<Control-l>', record_management.load_macro)
        self.bind('<Control-n>', record_management.new_macro)
        self.bind('<Control-b>', lambda _e: self.open_library())

        self.protocol("WM_DELETE_WINDOW", self.quit_software)
        # Skip the tray icon when running headless — saves ~0.5s and avoids
        # leaving a tray icon behind after auto-quit on some systems.
        self.icon = None
        if not self._autoplay_active:
            Thread(target=self.systemTray).start()

        if not self._autoplay_active:
            self.attributes("-topmost", 0)

        if self._autoplay_active:
            # File-association launch: force quit-after-playback (in-memory
            # only, never persisted) and kick the first macro.
            self.settings.settings_dict["After_Playback"]["Mode"] = "Quit_software"
            self.after(150, self.macro.start_playback)

        self.mainloop()

    def load_language(self):
        self.lang = self.settings.settings_dict["Language"]
        with open(resource_path(path.join('langs', self.lang + '.json')), encoding='utf-8') as f:
            self.text_content = json.load(f)
        self.text_content = self.text_content["content"]

        if self.lang != "en":
            with open(resource_path(path.join('langs', 'en.json')), encoding='utf-8') as f:
                en = json.load(f)
            deepcopy_dict_missing_entries(self.text_content, en["content"])

    def systemTray(self):
        """Just to show little icon on system tray"""
        image = Image.open(resource_path(path.join("assets", "logo.ico")))
        menu = (
            MenuItem('Show', action=self.deiconify, default=True),
        )
        self.icon = Icon("name", image, "PyMacroRecord", menu)
        self.icon.run()

    def validate_input(self, action, value_if_allowed):
        """Prevents from adding letters on an Entry label"""
        if action == "1":  # Insert
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        return True

    def quit_software(self, force=False):
        if not self.macro_saved and self.macro_recorded and not force:
            wantToSave = confirm_save(self)
            if wantToSave:
                RecordFileManagement(self, self.menu).save_macro()
            elif wantToSave is None:
                return
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
        # Always tear the root down on the main thread to avoid the
        # "Not Responding" state when called from a playback worker.
        self.after(0, self._finalize_quit)

    def _finalize_quit(self):
        try:
            self.destroy()
        except Exception:
            pass
        try:
            self.quit()
        except Exception:
            pass

    def show_recording_overlay(self):
        if getattr(self, "_autoplay_active", False):
            return
        try:
            if self.recording_overlay is None or not self.recording_overlay.winfo_exists():
                self.recording_overlay = RecordingOverlay(self)
            else:
                self.recording_overlay.refresh()
                self.recording_overlay.deiconify()
                self.recording_overlay.lift()
        except Exception:
            self.recording_overlay = None

    def hide_recording_overlay(self):
        overlay = self.recording_overlay
        if overlay is None:
            return
        try:
            overlay.destroy()
        except Exception:
            pass
        self.recording_overlay = None

    def play_next_in_queue(self):
        """Load and play the next queued macro file. Returns True if a macro
        was kicked off, False if the queue is empty (or all entries failed)."""
        while self._macro_queue:
            next_file = self._macro_queue.pop(0)
            try:
                with open(next_file, 'r', encoding='utf-8') as f:
                    self.macro.import_record(load(f))
            except (OSError, ValueError):
                continue
            self.current_file = next_file
            self.macro_recorded = True
            self.macro_saved = True
            self.after(150, self.macro.start_playback)
            return True
        return False

    def open_library(self):
        if self.macro.record or self.macro.playback:
            return
        if self.library_window is not None:
            try:
                self.library_window.lift()
                return
            except Exception:
                self.library_window = None
        self.library_window = MacroLibrary(self, self)

    def post_record_prompt(self):
        events = self.macro.macro_events.get("events", []) if isinstance(self.macro.macro_events, dict) else []
        if not events:
            return
        text = self.text_content["library"]
        self.prevent_record = True
        try:
            save_it = messagebox.askyesno(text["save_prompt_title"], text["save_prompt_text"])
        finally:
            self.prevent_record = False
        if save_it:
            RecordFileManagement(self, self.menu).save_macro_as()
            if self.macro_saved and self.current_file:
                self.open_library()
        else:
            self.macro.macro_events = {"events": []}
            self.macro_recorded = False
            self.macro_saved = False
            self.current_file = None
            self.playBtn.configure(state=DISABLED)

