import json
import subprocess
import threading
import time
import os
import sys
import hashlib
import logging
import tkinter as tk
import winsound
from datetime import datetime, timedelta
from pathlib import Path

import pystray
from PIL import Image, ImageDraw, ImageFont


APP_DIR = Path(__file__).parent.resolve()
LOGS_DIR = APP_DIR / "logs"
CONFIG_PATH = APP_DIR / "config.json"
PROMPT_PATH = APP_DIR / "prompt.txt"
DEDUP_PATH = APP_DIR / "dedup_cache.json"
ALERTS_HISTORY_PATH = APP_DIR / "alerts_history.json"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def get_exe_path():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    # Use pythonw.exe to avoid a console window on startup
    python_dir = Path(sys.executable).parent
    pythonw = python_dir / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)
    return f'"{pythonw}" "{Path(__file__).resolve()}"'


def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"news_{today}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("NewsHelper")


def cleanup_old_logs(retention_days):
    cutoff = datetime.now() - timedelta(days=retention_days)
    for log_file in LOGS_DIR.glob("news_*.log"):
        try:
            date_str = log_file.stem.replace("news_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                log_file.unlink()
        except (ValueError, OSError):
            pass


def create_tray_icon():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size - 2, size - 2], fill=(30, 30, 30, 240))
    points = [(12, 48), (24, 32), (36, 38), (52, 16)]
    draw.line(points, fill=(0, 200, 80, 255), width=3)
    draw.polygon([(46, 20), (52, 16), (52, 24)], fill=(0, 200, 80, 255))
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    draw.text((22, 2), "$", fill=(255, 255, 255, 200), font=font)
    return img


def create_alert_icon():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size - 2, size - 2], fill=(80, 10, 10, 240))
    points = [(12, 48), (24, 32), (36, 38), (52, 16)]
    draw.line(points, fill=(255, 60, 60, 255), width=3)
    draw.polygon([(46, 20), (52, 16), (52, 24)], fill=(255, 60, 60, 255))
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    draw.text((22, 2), "!", fill=(255, 255, 0, 255), font=font)
    return img


def show_alert_popup(alerts):
    """Show a persistent always-on-top popup window with alert details.
    Stays on screen until the user clicks Dismiss. Plays a sound."""

    def _play_sound():
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            time.sleep(0.3)
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

    threading.Thread(target=_play_sound, daemon=True).start()

    root = tk.Tk()
    root.title("NewsHelper - MARKET ALERT")
    root.attributes("-topmost", True)
    root.configure(bg="#1a1a2e")

    # Size and center
    width, height = 750, min(200 + len(alerts) * 160, 850)
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.minsize(750, 300)
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    content_width = 700

    # Header bar
    header_frame = tk.Frame(root, bg="#e94560", padx=12, pady=8)
    header_frame.pack(fill="x")

    header_text = f"MARKET ALERT  -  {len(alerts)} new event{'s' if len(alerts) != 1 else ''}"
    tk.Label(
        header_frame, text=header_text,
        font=("Segoe UI", 14, "bold"), fg="white", bg="#e94560",
    ).pack(side="left")

    tk.Label(
        header_frame, text=datetime.now().strftime("%H:%M"),
        font=("Segoe UI", 12), fg="white", bg="#e94560",
    ).pack(side="right")

    # --- Dismiss button BELOW header, ABOVE alerts ---
    btn_frame = tk.Frame(root, bg="#1a1a2e", pady=8)
    btn_frame.pack(fill="x")

    tk.Button(
        btn_frame, text="Dismiss All", font=("Segoe UI", 11, "bold"),
        fg="white", bg="#0f3460", activebackground="#e94560",
        activeforeground="white", relief="flat", padx=30, pady=5,
        command=root.destroy,
    ).pack()

    # --- Scrollable alert area ---
    container = tk.Frame(root, bg="#1a1a2e")
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg="#1a1a2e", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    alert_frame = tk.Frame(canvas, bg="#1a1a2e")

    alert_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=alert_frame, anchor="nw", width=content_width)
    canvas.configure(yscrollcommand=scrollbar.set)

    # Mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)

    direction_colors = {
        "BULLISH": "#00c853", "BEARISH": "#ff1744", "NEUTRAL": "#ffc107",
    }
    direction_arrows = {
        "BULLISH": "▲ BULLISH", "BEARISH": "▼ BEARISH", "NEUTRAL": "◆ NEUTRAL",
    }

    card_inner_width = content_width - 30  # account for card padding

    for alert in alerts:
        impact = alert.get("impact", "MEDIUM")
        direction = alert.get("direction", "NEUTRAL")
        headline = alert.get("headline", "Unknown Event")
        summary = alert.get("summary", "")
        published = alert.get("published", "")

        card = tk.Frame(alert_frame, bg="#16213e", padx=14, pady=10)
        card.pack(fill="x", pady=5, padx=4)

        # Row 1: Impact badge + Direction + Published time
        tag_frame = tk.Frame(card, bg="#16213e")
        tag_frame.pack(fill="x")

        impact_color = "#ff1744" if impact == "HIGH" else "#ffc107"
        tk.Label(
            tag_frame, text=f" {impact} ",
            font=("Segoe UI", 9, "bold"), fg="white", bg=impact_color,
        ).pack(side="left", padx=(0, 8))

        dir_color = direction_colors.get(direction, "#ffc107")
        dir_text = direction_arrows.get(direction, direction)
        tk.Label(
            tag_frame, text=dir_text,
            font=("Segoe UI", 10, "bold"), fg=dir_color, bg="#16213e",
        ).pack(side="left")

        # Published time from news source on the right
        if published:
            tk.Label(
                tag_frame, text=f"Published: {published}",
                font=("Segoe UI", 9, "italic"), fg="#8888aa", bg="#16213e",
            ).pack(side="right")

        # Headline
        tk.Label(
            card, text=headline,
            font=("Segoe UI", 12, "bold"), fg="white", bg="#16213e",
            wraplength=card_inner_width, justify="left", anchor="w",
        ).pack(fill="x", pady=(6, 2))

        # Summary
        if summary:
            tk.Label(
                card, text=summary,
                font=("Segoe UI", 10), fg="#b0b0b0", bg="#16213e",
                wraplength=card_inner_width, justify="left", anchor="w",
            ).pack(fill="x")

    try:
        root.after(100, lambda: root.focus_force())
    except Exception:
        pass

    root.mainloop()


class DedupCache:
    def __init__(self, window_hours=2):
        self.window = timedelta(hours=window_hours)
        self.cache = {}
        self._load()

    def _load(self):
        if DEDUP_PATH.exists():
            try:
                with open(DEDUP_PATH, "r") as f:
                    raw = json.load(f)
                self.cache = {
                    k: datetime.fromisoformat(v) for k, v in raw.items()
                }
            except (json.JSONDecodeError, ValueError):
                self.cache = {}

    def _save(self):
        raw = {k: v.isoformat() for k, v in self.cache.items()}
        with open(DEDUP_PATH, "w") as f:
            json.dump(raw, f)

    def _hash(self, headline):
        return hashlib.md5(headline.lower().strip().encode()).hexdigest()

    def is_duplicate(self, headline):
        h = self._hash(headline)
        now = datetime.now()
        self.cache = {
            k: v for k, v in self.cache.items() if now - v < self.window
        }
        if h in self.cache:
            return True
        self.cache[h] = now
        self._save()
        return False


class AlertHistory:
    def __init__(self):
        self.alerts = []
        self._load()

    def _load(self):
        if ALERTS_HISTORY_PATH.exists():
            try:
                with open(ALERTS_HISTORY_PATH, "r", encoding="utf-8") as f:
                    self.alerts = json.load(f)
            except (json.JSONDecodeError, ValueError):
                self.alerts = []

    def _save(self):
        with open(ALERTS_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.alerts, f, indent=2)

    def add(self, alert):
        entry = {
            "headline": alert.get("headline", ""),
            "impact": alert.get("impact", "MEDIUM"),
            "direction": alert.get("direction", "NEUTRAL"),
            "summary": alert.get("summary", ""),
            "timestamp": datetime.now().isoformat(),
        }
        self.alerts.insert(0, entry)
        self.alerts = self.alerts[:200]
        self._save()

    def get_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return [a for a in self.alerts if a.get("timestamp", "").startswith(today)]


class NewsHelper:
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging()
        self.dedup = DedupCache(self.config.get("dedup_window_hours", 2))
        self.alert_history = AlertHistory()
        self.running = True
        self.silent_mode = False
        self.last_check = None
        self.last_status = "Starting..."
        self.icon = None
        self.normal_image = create_tray_icon()
        self.alert_image = create_alert_icon()

        cleanup_old_logs(self.config.get("log_retention_days", 7))

        if self.config.get("auto_start", True):
            self._setup_autostart()

    def _setup_autostart(self):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(key, "NewsHelper", 0, winreg.REG_SZ, get_exe_path())
            winreg.CloseKey(key)
            self.logger.info("Auto-start registered in Windows startup")
        except Exception as e:
            self.logger.warning(f"Could not set auto-start: {e}")

    def _remove_autostart(self):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, "NewsHelper")
            winreg.CloseKey(key)
        except Exception:
            pass

    def _read_prompt(self):
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()

    def _build_prompt(self):
        base_prompt = self._read_prompt()

        # Get recent alerts to tell Claude what it already reported
        recent = self.alert_history.get_today()
        if not recent:
            return base_prompt

        # Build a list of already-reported headlines with summaries
        already_reported = []
        for a in recent[:20]:
            line = f"- {a.get('headline', '')}"
            if a.get("summary"):
                line += f" ({a.get('summary', '')})"
            already_reported.append(line)

        dedup_section = (
            "\n\n=== DEDUPLICATION RULES ==="
            "\nThe following news has ALREADY been reported to the user.\n"
            "\nDo NOT report:\n"
            "- The same headline reworded\n"
            "- Market reactions to already-reported events (e.g. 'stocks rally on ceasefire' if ceasefire was already reported)\n"
            "- Analyst commentary or opinions about already-reported events\n"
            "\nDO report (these are allowed):\n"
            "- Genuinely new developments that change the situation (e.g. 'Iran officially accepts ceasefire' after 'Trump proposes ceasefire' - this is a material update)\n"
            "- New events on completely different topics\n"
            "\nAlready reported:\n"
            + "\n".join(already_reported)
        )

        return base_prompt + dedup_section

    def check_news(self):
        self.logger.info("Starting news check...")
        self.last_status = "Checking..."

        if self.icon:
            self.icon.title = "NewsHelper - Checking..."

        try:
            prompt = self._build_prompt()
            claude_path = self.config.get("claude_path", "claude")

            # Hide console window on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

            model = self.config.get("claude_model", "claude-haiku-4-5-20251001")
            result = subprocess.run(
                [
                    claude_path,
                    "-p", prompt,
                    "--model", model,
                    "--allowedTools", "WebSearch",
                    "--output-format", "text",
                ],
                capture_output=True,
                timeout=180,
                cwd=str(APP_DIR),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                startupinfo=startupinfo,
            )

            if result.returncode != 0:
                self.logger.error(f"Claude CLI error: {result.stderr.decode('utf-8', errors='replace')}")
                self.last_status = f"Error at {datetime.now().strftime('%H:%M')}"
                return

            response = result.stdout.decode("utf-8", errors="replace").strip()
            self.logger.info(f"Raw response length: {len(response)} chars")

            alerts_data = self._parse_response(response)
            self._process_alerts(alerts_data)

        except subprocess.TimeoutExpired:
            self.logger.error("Claude CLI timed out after 180s")
            self.last_status = f"Timeout at {datetime.now().strftime('%H:%M')}"
        except Exception as e:
            self.logger.error(f"News check failed: {e}")
            self.last_status = f"Error at {datetime.now().strftime('%H:%M')}"

    def _parse_response(self, response):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        for start_char in ["{", "["]:
            idx = response.find(start_char)
            if idx != -1:
                bracket_count = 0
                end_char = "}" if start_char == "{" else "]"
                for i in range(idx, len(response)):
                    if response[i] == start_char:
                        bracket_count += 1
                    elif response[i] == end_char:
                        bracket_count -= 1
                    if bracket_count == 0:
                        try:
                            return json.loads(response[idx : i + 1])
                        except json.JSONDecodeError:
                            break

        self.logger.warning("Could not parse JSON from response")
        self.logger.debug(f"Response was: {response[:500]}")
        return {"alerts": []}

    def _process_alerts(self, data):
        alerts = data.get("alerts", [])
        threshold = self.config.get("alert_threshold", "MEDIUM")
        valid_impacts = {"HIGH"} if threshold == "HIGH" else {"HIGH", "MEDIUM"}

        new_alerts = []
        for alert in alerts:
            headline = alert.get("headline", "")
            impact = alert.get("impact", "MEDIUM").upper()

            if impact not in valid_impacts:
                continue
            if self.dedup.is_duplicate(headline):
                self.logger.info(f"Skipping duplicate: {headline}")
                continue

            alert["timestamp"] = datetime.now().isoformat()
            new_alerts.append(alert)

        now_str = datetime.now().strftime("%H:%M")

        if new_alerts:
            self.logger.info(f"Found {len(new_alerts)} new alert(s)")
            for alert in new_alerts:
                self.alert_history.add(alert)
                self._log_alert(alert)

            self.last_status = f"{len(new_alerts)} alert(s) at {now_str}"
            if self.icon:
                self.icon.icon = self.alert_image
                self.icon.title = f"NewsHelper - {self.last_status}"

            if self.silent_mode:
                self.logger.info("Silent mode - popup suppressed")
            else:
                popup_thread = threading.Thread(
                    target=show_alert_popup, args=(new_alerts,), daemon=True
                )
                popup_thread.start()

            # Reset tray icon back to normal after 5 minutes
            threading.Timer(300, self._reset_icon).start()
        else:
            self.logger.info("No significant market-moving news found")
            self.last_status = f"No alerts at {now_str}"
            if self.icon:
                self.icon.icon = self.normal_image
                self.icon.title = f"NewsHelper - {self.last_status}"

        self.last_check = datetime.now()

    def _reset_icon(self):
        if self.icon:
            self.icon.icon = self.normal_image

    def _log_alert(self, alert):
        self.logger.info(
            f"ALERT: [{alert.get('impact')}] [{alert.get('direction')}] "
            f"{alert.get('headline')} - {alert.get('summary')}"
        )

    def _is_quiet_hours(self):
        start = self.config.get("quiet_hours_start", "")
        end = self.config.get("quiet_hours_end", "")
        if not start or not end:
            return False

        try:
            now = datetime.now().time()
            quiet_start = datetime.strptime(start, "%H:%M").time()
            quiet_end = datetime.strptime(end, "%H:%M").time()

            if quiet_start <= quiet_end:
                # Same day range (e.g. 09:00 to 17:00)
                return quiet_start <= now <= quiet_end
            else:
                # Overnight range (e.g. 20:00 to 09:00)
                return now >= quiet_start or now <= quiet_end
        except ValueError:
            self.logger.warning(f"Invalid quiet hours format: {start} - {end}")
            return False

    def _check_loop(self):
        if not self._is_quiet_hours():
            self.check_news()
        else:
            self.logger.info("Quiet hours active on startup, skipping initial check")
            if self.icon:
                self.icon.title = f"NewsHelper - Quiet hours (until {self.config.get('quiet_hours_end', '')})"
        interval = self.config.get("check_interval_minutes", 15) * 60
        while self.running:
            time.sleep(interval)
            if not self.running:
                break
            if self._is_quiet_hours():
                now_str = datetime.now().strftime("%H:%M")
                self.logger.info(f"Quiet hours active, skipping check at {now_str}")
                if self.icon:
                    self.icon.title = f"NewsHelper - Quiet hours (until {self.config.get('quiet_hours_end', '')})"
                continue
            self.check_news()

    def _on_check_now(self, icon, item):
        threading.Thread(target=self.check_news, daemon=True).start()

    def _on_toggle_silent(self, icon, item):
        self.silent_mode = not self.silent_mode
        state = "ON" if self.silent_mode else "OFF"
        self.logger.info(f"Silent mode {state}")
        if self.icon:
            suffix = " [SILENT]" if self.silent_mode else ""
            self.icon.title = f"NewsHelper - {self.last_status}{suffix}"

    def _on_view_log(self, icon, item):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = LOGS_DIR / f"news_{today}.log"
        if log_file.exists():
            os.startfile(str(log_file))

    def _on_view_history(self, icon, item):
        today_alerts = self.alert_history.get_today()
        if today_alerts:
            threading.Thread(
                target=show_alert_popup, args=(today_alerts,), daemon=True
            ).start()

    def _on_open_folder(self, icon, item):
        os.startfile(str(APP_DIR))

    def _on_settings(self, icon, item):
        threading.Thread(target=self._show_settings, daemon=True).start()

    def _show_settings(self):
        win = tk.Tk()
        win.title("NewsHelper - Settings")
        win.attributes("-topmost", True)
        win.configure(bg="#1a1a2e")
        win.resizable(False, False)
        win.geometry("380x280")

        # Center on screen
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 380) // 2
        y = (win.winfo_screenheight() - 280) // 2
        win.geometry(f"+{x}+{y}")

        tk.Label(
            win, text="Settings", font=("Segoe UI", 14, "bold"),
            fg="white", bg="#1a1a2e",
        ).pack(pady=(12, 8))

        frame = tk.Frame(win, bg="#1a1a2e")
        frame.pack(padx=20, fill="x")

        # Quiet hours start
        tk.Label(
            frame, text="Quiet hours start:", font=("Segoe UI", 11),
            fg="white", bg="#1a1a2e",
        ).grid(row=0, column=0, sticky="w", pady=6)

        start_var = tk.StringVar(value=self.config.get("quiet_hours_start", "20:00"))
        start_entry = tk.Entry(
            frame, textvariable=start_var, font=("Segoe UI", 11),
            width=8, bg="#16213e", fg="white", insertbackground="white",
        )
        start_entry.grid(row=0, column=1, padx=(10, 0), pady=6)

        # Quiet hours end
        tk.Label(
            frame, text="Quiet hours end:", font=("Segoe UI", 11),
            fg="white", bg="#1a1a2e",
        ).grid(row=1, column=0, sticky="w", pady=6)

        end_var = tk.StringVar(value=self.config.get("quiet_hours_end", "09:00"))
        end_entry = tk.Entry(
            frame, textvariable=end_var, font=("Segoe UI", 11),
            width=8, bg="#16213e", fg="white", insertbackground="white",
        )
        end_entry.grid(row=1, column=1, padx=(10, 0), pady=6)

        # Check interval
        tk.Label(
            frame, text="Check interval (min):", font=("Segoe UI", 11),
            fg="white", bg="#1a1a2e",
        ).grid(row=2, column=0, sticky="w", pady=6)

        interval_var = tk.StringVar(value=str(self.config.get("check_interval_minutes", 15)))
        interval_entry = tk.Entry(
            frame, textvariable=interval_var, font=("Segoe UI", 11),
            width=8, bg="#16213e", fg="white", insertbackground="white",
        )
        interval_entry.grid(row=2, column=1, padx=(10, 0), pady=6)

        # Status label
        status_label = tk.Label(
            win, text="", font=("Segoe UI", 10), fg="#00c853", bg="#1a1a2e",
        )
        status_label.pack(pady=(4, 0))

        def save():
            self.config["quiet_hours_start"] = start_var.get().strip()
            self.config["quiet_hours_end"] = end_var.get().strip()
            try:
                self.config["check_interval_minutes"] = int(interval_var.get().strip())
            except ValueError:
                pass
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.config, f, indent=2)
            status_label.config(text="Saved! Changes take effect next check cycle.")
            self.logger.info(
                f"Settings updated: quiet {self.config['quiet_hours_start']}-"
                f"{self.config['quiet_hours_end']}, interval {self.config['check_interval_minutes']}m"
            )

        tk.Button(
            win, text="Save", font=("Segoe UI", 11, "bold"),
            fg="white", bg="#0f3460", activebackground="#e94560",
            activeforeground="white", relief="flat", padx=30, pady=5,
            command=save,
        ).pack(pady=10)

        win.mainloop()

    def _on_quit(self, icon, item):
        self.running = False
        icon.stop()

    def run(self):
        self.logger.info("NewsHelper starting...")

        quiet_status = ""
        if self._is_quiet_hours():
            quiet_status = f" (quiet until {self.config.get('quiet_hours_end', '')})"

        menu = pystray.Menu(
            pystray.MenuItem("Check Now", self._on_check_now, default=True),
            pystray.MenuItem(
                lambda item: "Silent Mode  [ON]" if self.silent_mode else "Silent Mode  [OFF]",
                self._on_toggle_silent,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Today's Alerts", self._on_view_history),
            pystray.MenuItem("View Log", self._on_view_log),
            pystray.MenuItem("Settings", self._on_settings),
            pystray.MenuItem("Open Folder", self._on_open_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )

        self.icon = pystray.Icon(
            "NewsHelper",
            self.normal_image,
            "NewsHelper - Starting...",
            menu,
        )

        check_thread = threading.Thread(target=self._check_loop, daemon=True)
        check_thread.start()

        self.icon.run()
        self.logger.info("NewsHelper stopped.")


if __name__ == "__main__":
    app = NewsHelper()
    app.run()
