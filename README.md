# PyMacroRecord (Py_RPA fork)

A Python + tkinter macro recorder for Windows and Linux (X11). Records mouse movement, clicks, scrolls, and keyboard input; plays them back with configurable speed, repeat, interval, schedule, and after-playback actions.

This fork ([wsnh2022/Py_RPA](https://github.com/wsnh2022/Py_RPA)) adds a workflow-oriented layer: an offline build (no network calls), a folder-scan Macro Library, post-record Save/Cancel prompt, headless autoplay on `.pmr` open, and a multi-file queue for chaining macros from AutoHotkey or batch scripts. See [What's new in this fork](#whats-new-in-this-fork) below.

# What's new in this fork

### 🌐 Fully offline — no network calls
- The startup GitHub release check is removed.
- The Donors window no longer fetches over HTTP.
- `requests` is dropped from `requirements.txt`.
- The app never touches the internet — useful in air-gapped or privacy-sensitive environments.

### 📁 Macro Library (folder-scan)
A built-in browser for your saved macros. Open it from `File → Library...` or with **Ctrl+B**.
- Points at any folder you choose (default: `%LOCALAPPDATA%\PyMacroRecord\macros` on Windows).
- Lists every `.pmr` / `.json` file in that folder with **Name · Modified · Events · Path**, newest first.
- **Run** (or double-click) — load + play the selected macro immediately.
- **Rename** — renames the file on disk and updates references.
- **Open folder** — reveals the file in Explorer / Finder / your file manager.
- **Delete** — permanently removes the file (with confirmation).
- **Change folder...** — point the Library at any directory; switches scan target.

### 💾 Post-record Save / Cancel prompt
When you stop a recording, the app asks whether to **Save** (defaults to the Library folder) or **Cancel** (discard). After Save, the Library opens automatically so you can run the recording right away.

### 🚀 One-click autoplay from a `.pmr` file
Set PyMacroRecord as the default app for `.pmr` files (or pass one as an argument) and:
- The GUI **never paints** — no flash, no window.
- The macro plays immediately, then the app exits.
- Toggle: `Options → Settings → Auto-play when opened from a .pmr file` (default **on**).

### 🔗 Multi-file queue for AutoHotkey / batch chaining
Pass multiple files in one launch and they play in sequence — one cold start, then chained playback:

```ahk
exe := "C:\path\to\PyMacroRecord-portable.exe"
RunWait('"' exe '" "macros\step1.pmr" "macros\step2.pmr" "macros\step3.pmr"')
```

Each file plays once in order; the app exits when the queue is empty. Much faster than running the exe per file (which incurs PyInstaller cold-start each time).

### 🔴 Recording overlay
A small always-on-top **● REC** indicator appears top-right while recording. It shows your configured **Stop record** hotkey so you can stop without restoring the main window or hunting for the tray icon. Disappears the moment recording stops.

### 🐛 Stability fixes
- Playback teardown moved to the main Tk thread — eliminates the post-playback "Not Responding" window on file-association launches.
- `show_toast` no longer crashes when the system lacks `pkg_resources` (modern `setuptools`); the toast just silently no-ops.

# Features

**Recording**
- Mouse movement, clicks, scrolls, keyboard input — each toggleable.
- Configurable global hotkeys to start/stop recording and playback.
- Top-right **● REC** overlay while recording, with the Stop hotkey shown.

**Playback**
- Speed (0.1× – 10×), Repeat (finite or infinite), Delay between repeats.
- Interval and For windows for time-bounded loops.
- Scheduled start (seconds-from-midnight).
- After-playback actions: Idle, Quit, Standby, Log off, Turn off, Restart, Hibernate.

**Files**
- Save / Load `.pmr` (PyMacroRecord) and `.json` formats.
- Folder-scan Library window with Run / Rename / Open folder / Delete.
- Open a `.pmr` directly from Explorer to autoplay headlessly.
- Pass multiple files in one launch to play a queue.

**Other**
- 13 UI languages.
- System tray icon (skipped during headless autoplay).

# Usage

- **Record**: press the red button (or your Start-record hotkey). Stop with the black square or your Stop-record hotkey.
- **Play**: press the green play icon. Stop with `F3` (default Stop-playback hotkey).
- **Library**: `File → Library...` or `Ctrl+B`.


# For bug reports or update requests
For issues with **this fork's additions**, open an issue at [wsnh2022/Py_RPA/issues](https://github.com/wsnh2022/Py_RPA/issues). For upstream behavior, see the [original project](https://github.com/LOUDO56/PyMacroRecord/issues).

# Running from source

```bash
git clone https://github.com/wsnh2022/Py_RPA.git
cd Py_RPA
pip install -r requirements.txt
cd src
python main.py
```

- Requires [Python](https://www.python.org/downloads/) 3.10+.
- **Linux**: install Tkinter (`sudo apt install python3-tk` or distro equivalent). X11 only — Wayland is not supported.
- `main.py` `os.chdir`s to its own directory; always launch it from `src/`.

# Build

The project uses **cx_Freeze** to build the application.

## Linux (AppImage)

Requirements: `cx_Freeze`, `imagemagick` (`convert`), `curl`

```bash
./build.sh
```

This will produce a `PyMacroRecord-x86_64.AppImage` (or the current arch) in the project root.

> **Note:** The AppImage runs in X11 mode only. Wayland is not supported.

## Windows

### Folder
Requirements: `cx_Freeze`

```bash
python setup_cx.py build
```

The output will be in the `build/` directory.

### Portable
Requirements: `PyInstaller`

Run
```bash
build.bat
```

The output will be in the `dist/` directory.

# License

This program is under [GNU General Public License v3.0](LICENSE.md)

# Credits

Based on [PyMacroRecord](https://github.com/LOUDO56/PyMacroRecord) by [LOUDO56](https://github.com/LOUDO56) and its translators / contributors.
