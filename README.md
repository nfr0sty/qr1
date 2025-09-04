# QR → Мобильный браузер — установочный комплект (GUI)
Готовый **GUI**-инструмент, который распознаёт QR (из файла или с веб-камеры) и **открывает ссылку как с телефона** (мобильный User-Agent, размер экрана) через Playwright.

## Состав
- `app/app_gui.py` — основной GUI (Tkinter).
- `assets/icon.png` — иконка приложения.
- `requirements.txt` — зависимости для запуска (если не паковать в инсталлятор).
- `build_scripts/build_macos.sh` — сборка `.app` и `.dmg` на macOS.
- `build_scripts/build_windows.bat` — сборка `.exe` (onefile) на Windows.
- `build_scripts/installer.iss` — скрипт Inno Setup для создания установщика под Windows (опционально).

## Как пользоваться (быстро)
Если вы просто хотите **запустить у себя** без упаковки в инсталлятор:
```bash
# macOS / Windows
cd app
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r ../requirements.txt
python app_gui.py   # первый запуск сам скачает браузер Playwright при необходимости
```

## Как собрать инсталлятор (чтобы отдать пользователю без Python)
> Сборку выполняет разработчик у себя, полученный `.dmg`/`.exe` отправляется пользователю.

### macOS (.app + .dmg)
1. Установите инструменты:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```
2. Запустите скрипт сборки:
```bash
bash build_scripts/build_macos.sh
```
Результат: `dist/QRMobile.app` и образ `dist/QRMobile.dmg` (перенесите `.app` в `/Applications`).  
> Примечание: приложение не подписано — при первом запуске используйте *Right click → Open*.

### Windows (.exe + инсталлятор)
1. Установите инструменты в venv:
```bat
pip install -r requirements.txt
pip install pyinstaller
```
2. Соберите exe:
```bat
build_scripts\build_windows.bat
```
Результат: `dist\QRMobile.exe` (portable).  
3. (Опционально) Сделайте установщик через **Inno Setup**: откройте `build_scripts\installer.iss` и соберите. Получите `QRMobile-Setup.exe`.

## Замечания
- **Первый запуск**: приложение автоматически докачает движок браузера Playwright (Chromium по умолчанию). Требуется интернет.
- **Deeplink `myapp://`** — на ПК не откроется в приложении, будет показан текст. Для проверки deep link используйте Android Emulator/iOS Simulator.
- **Безопасность**: не обходите 2FA/платёжные QR; инструмент предназначен для тестов и предпросмотра мобильной версии сайтов.

Лицензия: MIT.
