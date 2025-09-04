#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

APP_NAME="QRMobile"
ICON_PATH="assets/icon.png"    # PyInstaller примет .png как иконку на macOS
SRC="app/app_gui.py"

# Создаём venv при необходимости
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Сборка .app (windowed)
pyinstaller --noconsole --windowed --name "$APP_NAME" --icon "$ICON_PATH" "$SRC" \
  --add-data "assets/icon.png:assets"

# Создаём DMG
mkdir -p dist/dmg
hdiutil create -volname "$APP_NAME" -srcfolder "dist/$APP_NAME.app" -ov -format UDZO "dist/${APP_NAME}.dmg"

echo "Готово: dist/${APP_NAME}.app и dist/${APP_NAME}.dmg"
