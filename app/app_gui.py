import sys, os, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2

# ==== Playwright helpers ====
from playwright.sync_api import sync_playwright
from playwright.__main__ import main as playwright_main

APP_NAME = "QR Mobile"
DEFAULT_ENGINE = "chromium"
DEFAULT_DEVICE = "iPhone 13"

def log_append(text_widget: tk.Text, msg: str):
    text_widget.configure(state="normal")
    text_widget.insert("end", msg + "\n")
    text_widget.see("end")
    text_widget.configure(state="disabled")

def ensure_browser_installed(engine: str, log):
    """Пробует запустить браузер. Если бинарник не найден — скачивает его через playwright install."""
    try:
        with sync_playwright() as p:
            browser_type = getattr(p, engine)
            # Короткий запуск/закрытие для проверки наличия бинарника
            browser = browser_type.launch(headless=True)
            browser.close()
        return True
    except Exception as e:
        log(f"Браузер для Playwright не найден ({engine}). Скачиваем...")
        try:
            playwright_main(["install", engine])
            log("Скачивание завершено.")
            return True
        except Exception as ie:
            log(f"Не удалось установить браузер: {ie}")
            return False

def list_devices():
    """Возвращает список профилей устройств Playwright."""
    with sync_playwright() as p:
        return sorted(p.devices.keys())

def open_mobile(url_or_text: str, device_name: str, engine: str, screenshot_path: Path, log):
    with sync_playwright() as p:
        devices = p.devices
        if device_name not in devices:
            raise ValueError(f"Профиль '{device_name}' не найден.")
        device = devices[device_name]

        browser_type = getattr(p, engine)
        browser = browser_type.launch(headless=False)
        context = browser.new_context(**device)
        page = context.new_page()

        if url_or_text.startswith(("http://", "https://")):
            log(f"Открываем: {url_or_text}")
            page.goto(url_or_text, wait_until="domcontentloaded")
            log(f"Итоговый URL: {page.url}")
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                log(f"Скриншот: {screenshot_path}")
            except Exception as e:
                log(f"Не удалось сделать скриншот: {e}")
        else:
            log("Содержимое QR не URL. Текст ниже:")
            log(url_or_text)

        context.close()
        browser.close()

def decode_qr_from_image(path: Path) -> str:
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Не удалось открыть изображение: {path}")
    detector = cv2.QRCodeDetector()
    data, pts, _ = detector.detectAndDecode(img)
    if data:
        return data
    # multi
    try:
        retval, decoded_info, points, _ = detector.detectAndDecodeMulti(img)
        if retval and decoded_info:
            for d in decoded_info:
                if d:
                    return d
    except Exception:
        pass
    raise ValueError("QR не найден или не распознан.")

def decode_qr_from_webcam(camera_index: int, log) -> str:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Не удалось открыть камеру.")
    detector = cv2.QRCodeDetector()
    data_seen = None
    log("Окно камеры открыто. Наведите QR. Нажмите ESC для выхода.")
    result = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        data, points, _ = detector.detectAndDecode(frame)
        if points is not None:
            pts = points.astype(int).reshape(-1, 2)
            for i in range(len(pts)):
                cv2.line(frame, tuple(pts[i]), tuple(pts[(i+1)%len(pts)]), (0,255,0), 2)
        if data and data != data_seen:
            data_seen = data
            result = data
            cv2.putText(frame, "QR detected", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.imshow("QR Camera (ESC to exit)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or result:  # ESC или нашли QR
            break
    cap.release()
    cv2.destroyAllWindows()
    if not result:
        raise RuntimeError("QR не найден.")
    return result

# ==== GUI ====
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("640x420")
        self.resizable(False, False)

        self.icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        try:
            if self.icon_path.exists():
                self.iconphoto(False, tk.PhotoImage(file=str(self.icon_path)))
        except Exception:
            pass

        # Controls
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        # Engine
        ttk.Label(frm, text="Движок:").grid(row=0, column=0, sticky="w")
        self.engine_var = tk.StringVar(value=DEFAULT_ENGINE)
        self.engine_cb = ttk.Combobox(frm, textvariable=self.engine_var, values=["chromium","webkit","firefox"], state="readonly", width=12)
        self.engine_cb.grid(row=0, column=1, sticky="w", padx=(8,20))

        # Device
        ttk.Label(frm, text="Устройство:").grid(row=0, column=2, sticky="w")
        self.device_var = tk.StringVar(value=DEFAULT_DEVICE)
        try:
            devices = list_devices()
        except Exception:
            devices = [DEFAULT_DEVICE]
        self.device_cb = ttk.Combobox(frm, textvariable=self.device_var, values=devices, width=30)
        self.device_cb.grid(row=0, column=3, sticky="w")

        # Buttons
        self.btn_file = ttk.Button(frm, text="Скан из файла…", command=self.on_scan_file)
        self.btn_cam  = ttk.Button(frm, text="Скан с камеры…", command=self.on_scan_cam)
        self.btn_open = ttk.Button(frm, text="Открыть URL как телефон…", command=self.on_open_url)
        self.btn_file.grid(row=1, column=0, pady=10, sticky="w")
        self.btn_cam.grid(row=1, column=1, pady=10, sticky="w")
        self.btn_open.grid(row=1, column=2, pady=10, sticky="w")

        # Log
        self.log = tk.Text(frm, height=16, state="disabled")
        self.log.grid(row=2, column=0, columnspan=4, sticky="nsew")
        frm.rowconfigure(2, weight=1)
        frm.columnconfigure(3, weight=1)

        # Defaults
        self.screenshot_path = Path.home() / "Desktop" / "QRMobile_screenshot.png"

    def log(self, msg: str):
        log_append(self.log, msg)

    def disable_ui(self):
        for w in [self.btn_file, self.btn_cam, self.btn_open, self.engine_cb, self.device_cb]:
            w.configure(state="disabled")

    def enable_ui(self):
        for w in [self.btn_file, self.btn_cam, self.btn_open, self.engine_cb, self.device_cb]:
            w.configure(state="normal")

    def _ensure_and_open(self, content_getter):
        def worker():
            try:
                self.disable_ui()
                engine = self.engine_var.get()
                device = self.device_var.get()
                if not ensure_browser_installed(engine, self.log):
                    messagebox.showerror(APP_NAME, "Не удалось установить браузер Playwright.")
                    self.enable_ui()
                    return

                data = content_getter()
                if not data:
                    self.log("Пустое содержимое.")
                    self.enable_ui()
                    return

                open_mobile(data, device, engine, self.screenshot_path, self.log)
            except Exception as e:
                messagebox.showerror(APP_NAME, str(e))
            finally:
                self.enable_ui()
        threading.Thread(target=worker, daemon=True).start()

    def on_scan_file(self):
        path = filedialog.askopenfilename(title="Выберите файл с QR",
                                          filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы","*.*")])
        if not path:
            return
        def getter():
            return decode_qr_from_image(Path(path))
        self._ensure_and_open(getter)

    def on_scan_cam(self):
        def getter():
            return decode_qr_from_webcam(0, self.log)
        self._ensure_and_open(getter)

    def on_open_url(self):
        win = tk.Toplevel(self)
        win.title("Вставьте URL")
        win.geometry("500x120")
        ttk.Label(win, text="URL:").pack(anchor="w", padx=10, pady=(10,0))
        url_var = tk.StringVar()
        ent = ttk.Entry(win, textvariable=url_var)
        ent.pack(fill="x", padx=10, pady=5)
        ent.focus_set()
        def go():
            url = url_var.get().strip()
            if not url:
                return
            win.destroy()
            self._ensure_and_open(lambda: url)
        ttk.Button(win, text="Открыть", command=go).pack(pady=10)

if __name__ == "__main__":
    app = App()
    app.mainloop()
