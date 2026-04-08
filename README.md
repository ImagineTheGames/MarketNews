# MarketNews

A system tray application that monitors for major market-moving news every 15 minutes using Claude Code's web search. When significant events are detected (wars, ceasefire deals, Fed decisions, tariff announcements, etc.), a popup alert appears on your screen and stays until you dismiss it.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## What It Does

- Searches the web for breaking market-moving news every 15 minutes
- Shows a **persistent popup window** (not a toast that disappears) with color-coded alerts
- Each alert shows: impact level (HIGH/MEDIUM), market direction (BULLISH/BEARISH/NEUTRAL), headline, summary, and the time the news was published
- Plays a sound when alerts appear
- Lives in your **system tray** with right-click menu
- **Auto-starts with Windows** so you never miss a market event
- Deduplicates alerts so you don't see the same headline twice within 2 hours
- Logs everything to daily log files

## Quick Install (Recommended)

### Prerequisites

1. **Python 3.10+** - [Download here](https://www.python.org/downloads/) (check "Add Python to PATH" during install)
2. **Claude Code CLI (required)** - [Install instructions](https://docs.anthropic.com/en/docs/claude-code/overview)
   - This app uses Claude Code to search the web and analyze news using AI - it will not work without it
   - Install Claude Code, then run `claude` in your terminal and sign in to authenticate
   - You must be signed in and authenticated before running MarketNews
   - Make sure `claude` works in your terminal by running: `claude -p "hello"`

### Steps

1. **Download this repo**

   Click the green **Code** button above, then **Download ZIP**, and extract it somewhere (e.g. `C:\MarketNews`)

   Or clone it:
   ```
   git clone https://github.com/ImagineTheGames/MarketNews.git
   cd MarketNews
   ```

2. **Run the installer**

   Double-click **`install.bat`** - it will:
   - Install the Python dependencies for you
   - Offer to start the app immediately

   Or do it manually:
   ```
   pip install -r requirements.txt
   ```

3. **Start the app**

   ```
   python news_helper.py
   ```

   A small chart icon will appear in your **system tray** (bottom-right of your taskbar, you may need to click the `^` arrow to see it).

4. **That's it!** The app will:
   - Run its first news check immediately
   - Auto-register itself to start with Windows
   - Check again every 15 minutes

## Usage

### System Tray Menu (right-click the icon)

| Option | What it does |
|--------|-------------|
| **Check Now** | Run a news check immediately (also triggered by double-click) |
| **Today's Alerts** | Re-open the popup with all alerts from today |
| **View Log** | Open today's log file |
| **Open Folder** | Open the app's folder in Explorer |
| **Quit** | Exit the app |

### Alert Popup

When market-moving news is found, a popup appears center-screen and **stays until you click Dismiss**. Each alert shows:

- **Impact badge** - RED for HIGH, YELLOW for MEDIUM
- **Direction arrow** - Green BULLISH, Red BEARISH, Yellow NEUTRAL
- **Published time** - When the news was actually reported
- **Headline + Summary** - What happened and why it matters

### Configuration

Edit `config.json` to customize:

```json
{
  "check_interval_minutes": 15,
  "alert_threshold": "MEDIUM",
  "claude_path": "claude",
  "auto_start": true,
  "log_retention_days": 7,
  "dedup_window_hours": 2
}
```

| Setting | Description | Default |
|---------|-------------|---------|
| `check_interval_minutes` | How often to check for news | `15` |
| `alert_threshold` | Minimum impact to alert on (`"HIGH"` or `"MEDIUM"`) | `"MEDIUM"` |
| `claude_path` | Path to Claude Code CLI (usually just `"claude"`) | `"claude"` |
| `auto_start` | Register to start with Windows | `true` |
| `log_retention_days` | How many days of logs to keep | `7` |
| `dedup_window_hours` | Hours before a similar headline can alert again | `2` |

### Customizing What News to Track

Edit `prompt.txt` to change what Claude searches for. You can add or remove categories, change the time window, or adjust what counts as "significant."

## Building a Standalone .exe

If you want a single executable you can share or run without Python installed:

```
# Double-click build.bat, or run:
pip install pyinstaller
pyinstaller --onefile --noconsole --name NewsHelper news_helper.py
```

The `.exe` will be in the `dist/` folder. Copy `prompt.txt` and `config.json` next to it.

## Troubleshooting

**"Claude CLI not found"**
- Make sure Claude Code is installed and `claude` works in your terminal
- If it's installed somewhere unusual, set the full path in `config.json` under `claude_path`

**No tray icon visible**
- Click the `^` arrow in your taskbar to show hidden tray icons
- Drag the NewsHelper icon out so it's always visible

**No alerts appearing**
- Check the log file (right-click tray > View Log) for errors
- Try right-click > Check Now to trigger a manual check
- Make sure your internet connection is working

**"Python not found"**
- Reinstall Python and make sure to check **"Add Python to PATH"**
- Or use the full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python310\python.exe news_helper.py`

## How It Works

```
Every 15 minutes:
  1. Calls Claude Code CLI with a web search prompt
  2. Claude searches multiple news sources for breaking events
  3. Returns structured JSON with headlines, impact, and direction
  4. App checks for duplicates (skips if already alerted)
  5. Shows persistent popup window + plays alert sound
  6. Logs everything to daily log file
```

## License

MIT
