@echo off
setlocal
cd /d %~dp0\..

set APP_NAME=QRMobile
set ICON_PATH=assets\icon.png
set SRC=app\app_gui.py

if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Сборка в один файл без консоли
pyinstaller --noconsole --onefile --name "%APP_NAME%" --icon "%ICON_PATH%" "%SRC%" ^
  --add-data "assets\icon.png;assets"

echo Done. EXE в dist\%APP_NAME%.exe
endlocal
