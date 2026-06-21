import subprocess
from json import load
from os import path, remove, rename
from sys import platform
from tkinter import BOTH, BOTTOM, LEFT, RIGHT, TOP, X, Y, END, filedialog, messagebox, simpledialog
from tkinter.ttk import Button, Frame, Label, Scrollbar, Treeview

from windows.popup import Popup


class MacroLibrary(Popup):
    """Folder-scanning macro browser."""

    def __init__(self, parent, main_app):
        text = main_app.text_content["library"]
        super().__init__(text["title"], 660, 380, parent)
        self.main_app = main_app
        self.text = text
        self._entries = []
        main_app.prevent_record = True

        header = Frame(self)
        header.pack(side=TOP, fill=X, padx=8, pady=(6, 2))
        Label(header, text=text["title"], font=("Arial", 12, "bold")).pack(side=LEFT)
        Button(header, text=text["change_folder_button"], command=self._change_folder).pack(side=RIGHT)
        Button(header, text=text["refresh_button"], command=self._refresh).pack(side=RIGHT, padx=4)

        self.folder_label = Label(self, text="", foreground="#555")
        self.folder_label.pack(side=TOP, fill=X, padx=8)

        table_area = Frame(self)
        table_area.pack(side=TOP, fill=BOTH, expand=True, padx=8, pady=4)

        columns = ("name", "saved_at", "events", "path")
        self.tree = Treeview(table_area, columns=columns, show="headings", height=10)
        self.tree.heading("name", text=text["name_col"])
        self.tree.heading("saved_at", text=text["saved_at_col"])
        self.tree.heading("events", text=text["events_col"])
        self.tree.heading("path", text=text["path_col"])
        self.tree.column("name", width=160, anchor="w")
        self.tree.column("saved_at", width=140, anchor="w")
        self.tree.column("events", width=60, anchor="center")
        self.tree.column("path", width=270, anchor="w")

        vsb = Scrollbar(table_area, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda _e: self._run_selected())

        self.status_label = Label(self, text="")
        self.status_label.pack(side=TOP, pady=2)

        btn_area = Frame(self)
        btn_area.pack(side=BOTTOM, fill=X, pady=8, padx=8)
        Button(btn_area, text=text["run_button"], command=self._run_selected).pack(side=LEFT, padx=4)
        Button(btn_area, text=text["rename_button"], command=self._rename_selected).pack(side=LEFT, padx=4)
        Button(btn_area, text=text["open_folder_button"], command=self._open_folder_selected).pack(side=LEFT, padx=4)
        Button(btn_area, text=text["delete_button"], command=self._delete_selected).pack(side=LEFT, padx=4)
        Button(btn_area, text=text["close_button"], command=self.destroy).pack(side=RIGHT, padx=4)

        self._refresh()
        self.wait_window()
        main_app.prevent_record = False

    def destroy(self):
        try:
            self.main_app.library_window = None
        except Exception:
            pass
        return super().destroy()

    def _refresh(self):
        folder = self.main_app.macro_library.folder()
        self.folder_label.configure(text=folder or "")
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._entries = self.main_app.macro_library.scan()
        if not self._entries:
            self.status_label.configure(text=self.text["empty_text"])
            return
        self.status_label.configure(text="")
        for entry in self._entries:
            self.tree.insert("", END, values=(
                entry.get("name", ""),
                entry.get("saved_at", ""),
                entry.get("event_count", 0),
                entry.get("path", ""),
            ))

    def _selected_entry(self):
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        if idx >= len(self._entries):
            return None
        return self._entries[idx]

    def _change_folder(self):
        current = self.main_app.macro_library.folder()
        chosen = filedialog.askdirectory(
            title=self.text["choose_folder_title"],
            initialdir=current if current and path.isdir(current) else None,
            parent=self,
        )
        if not chosen:
            return
        self.main_app.macro_library.set_folder(chosen)
        self._refresh()

    def _run_selected(self):
        entry = self._selected_entry()
        if entry is None:
            return
        file_path = entry["path"]
        if not path.isfile(file_path):
            messagebox.showerror(
                self.main_app.text_content["global"]["error"],
                self.text["missing_file"],
            )
            return
        if self.main_app.macro.record or self.main_app.macro.playback:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                record = load(f)
        except (OSError, ValueError) as e:
            messagebox.showerror(self.main_app.text_content["global"]["error"], str(e))
            return
        self.main_app.macro.import_record(record)
        self.main_app.macro_recorded = True
        self.main_app.macro_saved = True
        self.main_app.current_file = file_path
        self.main_app.playBtn.configure(
            state="normal", command=self.main_app.macro.start_playback
        )
        self.destroy()
        self.main_app.after(50, self.main_app.macro.start_playback)

    def _delete_selected(self):
        entry = self._selected_entry()
        if entry is None:
            return
        file_path = entry["path"]
        if not messagebox.askyesno(
            self.text["delete_confirm_title"],
            self.text["delete_confirm"].format(name=entry.get("name", "")),
            parent=self,
        ):
            return
        try:
            remove(file_path)
        except OSError as e:
            messagebox.showerror(self.main_app.text_content["global"]["error"], str(e))
            return
        if self.main_app.current_file == file_path:
            self.main_app.current_file = None
            self.main_app.macro_saved = False
        self._refresh()

    def _rename_selected(self):
        entry = self._selected_entry()
        if entry is None:
            return
        file_path = entry["path"]
        if not path.isfile(file_path):
            messagebox.showerror(
                self.main_app.text_content["global"]["error"],
                self.text["missing_file"],
            )
            return
        directory, base = path.split(file_path)
        stem, ext = path.splitext(base)
        new_stem = simpledialog.askstring(
            self.text["rename_title"],
            self.text["rename_prompt"],
            initialvalue=stem,
            parent=self,
        )
        if not new_stem:
            return
        new_stem = new_stem.strip().replace("/", "_").replace("\\", "_")
        if not new_stem or new_stem == stem:
            return
        new_path = path.join(directory, new_stem + ext)
        if path.exists(new_path):
            messagebox.showerror(
                self.main_app.text_content["global"]["error"],
                self.text["rename_error"],
            )
            return
        try:
            rename(file_path, new_path)
        except OSError:
            messagebox.showerror(
                self.main_app.text_content["global"]["error"],
                self.text["rename_error"],
            )
            return
        if self.main_app.current_file == file_path:
            self.main_app.current_file = new_path
        self._refresh()

    def _open_folder_selected(self):
        entry = self._selected_entry()
        target = entry["path"] if entry else self.main_app.macro_library.folder()
        if not target:
            return
        if entry and not path.isfile(entry["path"]):
            target = self.main_app.macro_library.folder()
        try:
            if platform == "win32":
                if entry and path.isfile(target):
                    subprocess.Popen(["explorer", "/select,", path.normpath(target)])
                else:
                    subprocess.Popen(["explorer", path.normpath(target)])
            elif platform == "darwin":
                if entry and path.isfile(target):
                    subprocess.Popen(["open", "-R", target])
                else:
                    subprocess.Popen(["open", target])
            else:
                folder = path.dirname(target) if path.isfile(target) else target
                subprocess.Popen(["xdg-open", folder])
        except OSError as e:
            messagebox.showerror(self.main_app.text_content["global"]["error"], str(e))
