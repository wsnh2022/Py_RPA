# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PyMacroRecord — a Tkinter desktop app that records and replays mouse/keyboard macros. Cross-platform (Windows / Linux X11 / macOS), with Windows as the primary target.

## Running and building

All commands assume you are in the repo root, with deps installed via `pip install -r requirements.txt`.

- Run from source: `cd src && python main.py` — `main.py` `os.chdir`s to its own directory at startup, so the app must be launched from `src/` (or from the frozen exe's directory). Running it as `python src/main.py` will break asset/lang path resolution.
- Windows folder build (cx_Freeze): `python setup_cx.py build` → `build/exe.*/`
- Windows portable single-file build (PyInstaller, requires a `.venv`): `build.bat` → `dist/PyMacroRecord-portable.exe`
- Linux AppImage: `./build.sh` (needs `cx_Freeze`, `imagemagick`, `curl`; uses X11 only — Wayland is unsupported and `build.sh`'s `AppRun` forces `GDK_BACKEND=x11`).
- Release pipeline: `.github/workflows/build-release.yml`.

There is no test suite, linter config, or formatter config in this repo — do not invent commands for them.

## Platform notes that bite

- **Linux must be X11.** `pynput` and `pystray` are wired for X11 only here; do not add Wayland code paths without a deliberate plan.
- **Frozen vs source path handling.** `src/main.py` switches between `sys.executable` dir and `__file__` dir based on `sys.frozen`. Anything that loads bundled assets must go through `utils.get_file.resource_path` so both modes resolve correctly.
- **Bundled data dirs.** `setup_cx.py` (`include_files`) and `build.bat` (`--add-data`) each enumerate `assets`, `langs`, `hotkeys`, `macro`, `utils`, `windows`. If you add a new top-level directory under `src/` that needs to ship, update **both** build configs.
- **Windows-only deps.** `win10toast` and `pyinstaller` are gated in `requirements.txt` with `sys_platform == 'win32'` markers — keep that gating intact.
- **Version string.** `build.sh` greps the version out of `src/utils/version.py` with a regex matching `"X.Y.Z"`. Don't change that literal format.

## Architecture

Entry point `src/main.py` instantiates `MainApp` from `src/windows/main/main_app.py`. `MainApp` subclasses `Window` (a thin Tk root wrapper in `src/windows/window.py`) and is the central object — almost every subsystem is constructed with a back-reference to it (`self.main_app = main_app`) and reads shared state through that handle.

Object graph created in `MainApp.__init__` (order matters — later objects read fields set by earlier ones):

1. `UserSettings` (`src/utils/user_settings.py`) — loads/creates `userSettings.json` under the OS-appropriate config dir (`%LOCALAPPDATA%\PyMacroRecord` on Windows, `~/.config/PyMacroRecord` on Linux, `~/Library/Application Support/PyMacroRecord` on macOS). Holds `settings_dict`, the canonical config surface for the rest of the app.
2. `Version` — version check / update notifier.
3. `MenuBar` — Tk menu, dispatches into the windows under `src/windows/options`, `help`, `others`.
4. `Macro` (`src/macro/macro.py`) — owns the `pynput` keyboard+mouse listeners, the `macro_events` dict (`{"events": [...]}`), record/playback threads, and `RecordFileManagement` for `.pmr` / `.json` save/load.
5. `HotkeysManager` (`src/hotkeys/hotkeys_manager.py`) — a second `pynput.keyboard.Listener` dedicated to global hotkeys (start/stop record, start/stop playback). On Windows it uses a `win32_event_filter`.

Because `Macro` and `HotkeysManager` each start their own `pynput` keyboard listener, key events generally flow through both — be careful adding state that assumes a single listener.

### Window layout (`src/windows/`)

- `window.py` — base Tk window class.
- `main/` — the main app window and its menu bar.
- `options/playback`, `options/settings` — option dialogs; the shape of `settings_dict` (`Playback`, `Recordings`, `Settings`, ...) is what these dialogs read and write.
- `help/`, `others/` — about box, donors, translators, "new version available" popup.
- `popup.py` — shared popup helper.

### i18n

`src/langs/<code>.json` files hold translation tables. `MainApp.load_language()` picks the file by the `Language` setting; new keys must be added to **every** language file (or fall back gracefully) to avoid `KeyError`s in dialogs.

### Settings migration

`UserSettings.check_new_options()` plus the `deepcopy_dict_missing_entries` helper in `main_app.py` exist specifically so that a newer version reading an older `userSettings.json` fills in any missing keys from defaults. When you add a new setting key, make sure the default appears in `UserSettings.init_settings()` so the migration picks it up — don't read keys without ensuring they exist there.

### Macro file format

Records are JSON (`.pmr` is the same format with a custom extension). The `Settings.Compact_macro_data` setting toggles between compact and pretty-printed JSON on save. Loading accepts both `.pmr` and `.json`.
