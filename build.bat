@echo off
cd /d %~dp0

if not exist .venv\Scripts\activate.bat (
    echo [build] .venv not found. Create it first: python -m venv .venv ^&^& pip install -r requirements.txt
    exit /b 1
)
call .venv\Scripts\activate.bat

set UPX_FLAG=
if exist upx\upx.exe (
    set UPX_FLAG=--upx-dir upx
) else (
    echo [build] upx\upx.exe not found - building without UPX compression.
)

pyinstaller --noconfirm --onefile --windowed ^
    --icon "src/assets/logo.ico" ^
    --name "PyMacroRecord-portable" ^
    %UPX_FLAG% ^
    --add-data "src/assets;assets/" ^
    --add-data "src/langs;langs/" ^
    --add-data "src/hotkeys;hotkeys/" ^
    --add-data "src/macro;macro/" ^
    --add-data "src/utils;utils/" ^
    --add-data "src/windows;windows/" ^
    "src/main.py"

if errorlevel 1 (
    echo [build] PyInstaller failed.
    exit /b 1
)

echo.
echo [build] Build complete: dist\PyMacroRecord-portable.exe
