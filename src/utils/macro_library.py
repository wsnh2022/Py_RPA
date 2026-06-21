"""Folder-scan model for the Macro Library.

The Library doesn't keep its own index. It scans whatever folder the user
points it at and surfaces every .pmr / .json macro file it finds.
"""

from datetime import datetime
from json import load
from os import listdir, makedirs, path


MACRO_EXTENSIONS = (".pmr", ".json")


class MacroLibrary:
    def __init__(self, main_app):
        self.main_app = main_app
        self._ensure_folder()

    def folder(self):
        return self.main_app.settings.settings_dict["Library"]["Folder"]

    def set_folder(self, new_folder):
        self.main_app.settings.change_settings("Library", "Folder", None, new_folder)
        self._ensure_folder()

    def _ensure_folder(self):
        folder = self.folder()
        try:
            if folder and not path.isdir(folder):
                makedirs(folder, exist_ok=True)
        except OSError:
            pass

    def scan(self):
        folder = self.folder()
        if not folder or not path.isdir(folder):
            return []
        entries = []
        try:
            names = listdir(folder)
        except OSError:
            return []
        for name in names:
            if not name.lower().endswith(MACRO_EXTENSIONS):
                continue
            file_path = path.join(folder, name)
            if not path.isfile(file_path):
                continue
            entries.append(self._describe(file_path))
        entries.sort(key=lambda e: e.get("mtime", 0), reverse=True)
        return entries

    def _describe(self, file_path):
        try:
            mtime = path.getmtime(file_path)
            saved_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except OSError:
            mtime = 0
            saved_at = ""
        event_count = self._event_count(file_path)
        return {
            "name": path.splitext(path.basename(file_path))[0],
            "path": file_path,
            "saved_at": saved_at,
            "mtime": mtime,
            "event_count": event_count,
        }

    @staticmethod
    def _event_count(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = load(f)
        except (OSError, ValueError):
            return "?"
        if isinstance(data, dict):
            events = data.get("events", [])
            if isinstance(events, list):
                return len(events)
        return "?"
