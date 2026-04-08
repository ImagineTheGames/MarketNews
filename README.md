# MarketNews

A system tray application that monitors for major market-moving news every 15 minutes using Claude Code's web search. When significant events are detected (wars, ceasefire deals, Fed decisions, tariff announcements, etc.), a popup alert appears on your screen and stays until you dismiss it.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## What It Does

- Searches the web for breaking market-moving news every 15 minutes
- Shows a **persistent popup window** (not a toast that disappears) with color-coded alerts
- Each alert shows: impact level (HIGH/MEDIUM), market direction (BULLISH/BEARISH/NEUTRAL), headline, summary, and the time the news was published
- Plays a sound when alerts appear
- Lives in your **system tray** with right-click menu
- **Quiet hours** - no alerts during nights/weekends (configurable)
- **Settings UI** - right-click tray icon to configure without editing files
- **Smart deduplication** - won't spam you with the same story reworded, but will alert on genuinely new developments
- **Auto-starts with Windows** so you never miss a market event
- Logs everything to daily log files

## One-Click Install (Recommended)

1. **Download the latest release** from the [Releases page](https://github.com/ImagineTheGames/MarketNews/releases/latest)
2. **Extract the zip** anywhere (e.g. `C:\MarketNews`)
3. **Double-click `install.bat`** - it will automatically:
   - Check for Python and install it if missing
   - Check for Claude Code CLI and install it if missing
   - Verify Claude Code is authenticated (opens it for you to sign in if not)
   - Install Python dependencies
   - Offer to start MarketNews immediately

> **Important:** This app requires [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/overview) to work. Claude Code is what searches the web and analyzes news using AI. You must have it installed and signed in. The installer will guide you through this.

## Manual Install (From Source)

### Prerequisites

1. **Python 3.10+** - [Download here](https://www.python.org/downloads/) (check "Add Python to PATH" during install)
2. **Claude Code CLI (required)** - [Install instructions](https://docs.anthropic.com/en/docs/claude-code/overview)
   - This app uses Claude Code to search the web and analyze news using AI - it will not work without it
   - Install Claude Code, then run `claude` in your terminal and sign in to authenticate
   - You must be signed in and authenticated before running MarketNews
   - Make sure `claude` works in your terminal by running: `claude -p "hello"`

### Steps

1. **Clone the repo**
   ```
   git clone https://github.com/ImagineTheGames/MarketNews.git
   cd MarketNews
   ```

2. **Install dependencies**
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
| **Settings** | Open settings window (quiet hours, check interval) |
| **Open Folder** | Open the app's folder in Explorer |
| **Quit** | Exit the app |

### Alert Popup

When market-moving news is found, a popup appears center-screen and **stays until you click Dismiss**. Each alert shows:

- **Impact badge** - RED for HIGH, YELLOW for MEDIUM
- **Direction arrow** - Green BULLISH, Red BEARISH, Yellow NEUTRAL
- **Published time** - When the news was actually reported by the source
- **Headline + Summary** - What happened and why it matters

### Quiet Hours

By default, alerts are paused between **8:00 PM and 9:00 AM**. During quiet hours:
- No news checks are run (saves API usage)
- Tray icon shows "Quiet hours" in the tooltip
- Change the times via right-click > **Settings**, or edit `config.json`
- Set both to `""` to disable quiet hours entirely

### Configuration

Edit `config.json` or use right-click > **Settings**:

```json
{
  "check_interval_minutes": 15,
  "alert_threshold": "MEDIUM",
  "claude_path": "claude",
  "auto_start": true,
  "log_retention_days": 7,
  "dedup_window_hours": 6,
  "quiet_hours_start": "20:00",
  "quiet_hours_end": "09:00"
}
```

| Setting | Description | Default |
|---------|-------------|---------|
| `check_interval_minutes` | How often to check for news | `15` |
| `alert_threshold` | Minimum impact to alert on (`"HIGH"` or `"MEDIUM"`) | `"MEDIUM"` |
| `claude_path` | Path to Claude Code CLI (usually just `"claude"`) | `"claude"` |
| `auto_start` | Register to start with Windows | `true` |
| `log_retention_days` | How many days of logs to keep | `7` |
| `dedup_window_hours` | Hours before a similar headline can alert again | `6` |
| `quiet_hours_start` | When to stop checking (24h format, e.g. `"20:00"`) | `"20:00"` |
| `quiet_hours_end` | When to resume checking (24h format, e.g. `"09:00"`) | `"09:00"` |

### Smart Deduplication

The app prevents alert spam in two ways:

1. **Hash-based dedup** - identical or near-identical headlines are blocked for 6 hours
2. **AI-aware dedup** - Claude receives a list of all previously reported headlines so it skips reworded versions of the same story, market reactions to old news, and analyst commentary on already-reported events. Genuinely new developments on the same topic (e.g. "Iran accepts ceasefire" after "Trump proposes ceasefire") are still allowed through.

### Customizing What News to Track

Edit `prompt.txt` to change what Claude searches for. You can add or remove categories, change the time window, or adjust what counts as "significant."

## Building a Standalone .exe

If you want a single executable you can share or run without Python installed:

```
# Double-click build.bat, or run:
pip install pyinstaller
pyinstaller --onefile --noconsole --name MarketNews news_helper.py
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

**Getting too many alerts**
- Set `alert_threshold` to `"HIGH"` in config.json to only see high-impact events
- Adjust quiet hours to limit when alerts can appear

**Getting old/stale news**
- The prompt is configured to only return news from the last 30 minutes
- If you still see old news, check that your system clock is correct

**"Python not found"**
- Reinstall Python and make sure to check **"Add Python to PATH"**
- Or use the full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python310\python.exe news_helper.py`

## How It Works

```
Every 15 minutes (during active hours):
  1. Checks if quiet hours are active - skips if so
  2. Builds prompt with list of already-reported headlines
  3. Calls Claude Code CLI with web search enabled
  4. Claude searches multiple news sources for breaking events
  5. Returns structured JSON with headlines, impact, direction, and publish time
  6. App checks for duplicates (hash-based + AI-aware)
  7. Shows persistent popup window + plays alert sound
  8. Saves alerts to history for dedup and "Today's Alerts" view
  9. Logs everything to daily log file
```

## License

MIT
