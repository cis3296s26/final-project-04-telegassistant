# TeleGAssistant

A locally-hosted Telegram bot assistant that delivers daily briefings, manages tasks and reminders, and triages your Gmail inbox — all through a conversational Telegram interface. Built as the final project for Software Design (Temple University, Spring 2026).

**Repo:** https://github.com/NightmareHel/telegassistant

---

## What It Does

- Sends a morning briefing every day: pending tasks, upcoming deadlines, today's schedule, weather, and unread email count
- Lets you add, view, and remove tasks through guided Telegram conversations with a calendar picker
- Fires reminders at a chosen date/time — one-time, daily, or weekly
- On demand: `/briefing` for an instant briefing, `/emails` to AI-triage your Gmail inbox
- Optional Gmail integration — connect once with OAuth, all future briefings include your inbox

**Everything runs on your own machine.** No cloud AI subscription required — the LLM runs locally via [ollama](https://ollama.ai).

---

## Architecture

```
app.py                  # entry point — wires DB, LLM, bot, scheduler
├── ai/
│   ├── llm_client.py       # calls local ollama (gemma2:2b)
│   ├── gmail_client.py     # Gmail OAuth + unread email fetch
│   └── weather_client.py   # OpenWeatherMap API
├── bot/
│   ├── telegram_client.py  # all command handlers + conversation flows
│   └── ui.py               # inline calendar + time pickers
├── data/
│   └── database_client.py  # SQLite wrapper (users, tasks, reminders, deadlines, events)
├── jobs/
│   ├── briefing.py         # daily briefing pipeline
│   └── reminders.py        # reminder fire-and-notify job
└── automation/
    └── scheduler.py        # APScheduler setup (briefing @ 8 AM, reminders every minute)
```

**Stack:** Python 3.12 · python-telegram-bot 21 · ollama (gemma2:2b) · SQLite · APScheduler · OpenWeatherMap API · Gmail API (optional)

---

## Prerequisites

Install these before anything else:

| Requirement | Where to get it |
|---|---|
| Python 3.12+ | https://www.python.org/downloads/ |
| ollama | https://ollama.ai — download and install for your OS |
| Telegram account | Any phone — download the Telegram app |
| Telegram Bot Token | Create a bot via [@BotFather](https://t.me/BotFather) on Telegram (free) |
| OpenWeatherMap API key | https://openweathermap.org/api — free tier is enough |
| Gmail credentials (optional) | Google Cloud Console — see Gmail Setup section below |

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/NightmareHel/telegassistant.git
cd telegassistant
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Pull the AI model with ollama

ollama must be installed first (step in Prerequisites above).

```bash
ollama pull gemma2:2b
```

This downloads ~1.6 GB. It only needs to run once.

### 5. Create your `.env` file

In the project root, create a file named `.env` (no extension) with the following contents:

```
BOT_TOKEN=your_telegram_bot_token_here
WEATHER_API_KEY=your_openweathermap_key_here
DB_PATH=data/telegassistant.db
```

**How to get each value:**

- `BOT_TOKEN` — Open Telegram, search for **@BotFather**, send `/newbot`, follow the prompts. BotFather will give you a token that looks like `123456789:ABCdef...`
- `WEATHER_API_KEY` — Sign up at https://openweathermap.org/api, go to "API keys" in your account dashboard, copy the default key. It activates within ~10 minutes of sign-up.
- `DB_PATH` — Leave this as `data/telegassistant.db` (the app creates the database automatically on first run)

---

## Running the Bot

You need **two terminals open at the same time.**

**Terminal 1 — start the local AI model:**

```bash
ollama serve
```

Leave this running. It listens on `localhost:11434`.

**Terminal 2 — start the bot (with your virtual environment activated):**

```bash
python app.py
```

You should see log output like:

```
TeleGAssistant starting up...
Startup complete. Briefings will run on schedule.
Scheduler started. Jobs will run on schedule.
Telegram bot polling started
```

The bot is now live. Open Telegram, find your bot by the username you gave it in BotFather, and send `/start`.

---

## Bot Commands

| Command | What it does |
|---|---|
| `/start` | Register your account with the bot |
| `/help` | Show all commands |
| `/status` | Check if the bot is online |
| `/briefing` | Get your daily briefing right now |
| `/emails` | AI-triage your unread Gmail (requires Gmail setup) |
| `/tasks` | View your pending tasks |
| `/addtask` | Add a new task — guided flow with calendar and time picker |
| `/removetask` | Remove or complete a task |
| `/remindme` | Set a one-time, daily, or weekly reminder |
| `/setupgmail` | Connect your Gmail account via OAuth |
| `/cancel` | Cancel any in-progress command |

**Daily briefing schedule:** Fires automatically at **8:00 AM** every day. Contains tasks due in the next 7 days, upcoming deadlines, today's schedule, weather, and unread email count (if Gmail is connected).

---

## Gmail Setup (Optional)

If you skip this, the bot works fine — Gmail sections just won't appear in briefings.

To enable it:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Enable the **Gmail API** for that project
4. Go to **APIs & Services > Credentials**, click **Create Credentials > OAuth client ID**
5. Choose **Desktop app**, download the JSON file
6. Rename the file to `credentials.json` and place it in the project root (next to `app.py`)
7. Start the bot, then send `/setupgmail` in Telegram
8. The bot will send you an authorization link — open it in a browser, sign in, authorize, then paste the code back into Telegram

Once connected, a `token.json` file is created locally. Future sessions use it automatically.

---

## Stopping the Bot

Press `Ctrl+C` in Terminal 2. The bot will shut down cleanly. You can also stop `ollama serve` in Terminal 1.

---

## Troubleshooting

**"LLM server unreachable — briefings will use fallback"**
ollama is not running. Open a new terminal and run `ollama serve`, then restart `app.py`.

**"Gmail isn't connected yet"**
Either you haven't run `/setupgmail`, or `token.json` is missing. Run `/setupgmail` in Telegram.

**Bot doesn't respond**
Check that `BOT_TOKEN` in `.env` is correct. If you regenerate the token in BotFather, update `.env` and restart.

**"model 'gemma2:2b' not found"**
Run `ollama pull gemma2:2b` again in a terminal where ollama is installed.

---

## Notes for Graders

- No cloud AI service is required. Everything runs locally — the LLM (gemma2:2b via ollama), the database (SQLite), and the scheduler.
- The bot must be running on someone's local machine to be live. It is not deployed to a server.
- Gmail integration is optional and requires a one-time OAuth flow per machine.
- The `.env`, `credentials.json`, and `token.json` files are in `.gitignore` and are never committed — you must create `.env` yourself using the template above.
