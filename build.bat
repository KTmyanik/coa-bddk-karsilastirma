@echo off
setlocal
cd /d "%~dp0"

python -m pip install -r requirements-dev.txt
python -m PyInstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name CoaBddkCompare ^
  --add-data "config.json;." ^
  --add-data "connection.json;." ^
  --add-data "queries;queries" ^
  --add-data "data;data" ^
  src\main.py

echo.
echo EXE: dist\CoaBddkCompare.exe
echo Config ve queries klasorunu exe ile ayni dizinde birakmaniz yeterli.
pause
