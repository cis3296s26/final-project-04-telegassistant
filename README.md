# TeleGAssistant

An intelligent Telegram bot assistant powered by Claude AI. TeleGAssistant provides daily briefings, weather updates, and personalized reminders via Telegram.

## Features

- **Daily Briefings**: Automated morning summaries powered by Claude AI
- **Weather Integration**: Real-time weather information  
- **Smart Reminders**: Personalized reminders based on user preferences
- **Message Scheduling**: Job scheduling via APScheduler
- **SQLite Database**: Persistent storage for user data and settings

## Tech Stack

- **Language**: Python 3.12
- **Bot Framework**: Telegram Bot API
- **LLM**: Claude API (Anthropic)
- **Scheduler**: APScheduler
- **Database**: SQLite3

## Project Structure

```
.
├── ai/              # LLM and external API clients
│   ├── llm_client.py      # Claude API integration
│   ├── gmail_client.py    # Gmail integration
│   └── weather_client.py  # Weather data fetching
├── bot/             # Telegram bot interface
│   ├── telegram_client.py # Bot command handlers
│   └── ui.py              # UI/message formatting
├── data/            # Database and persistence
│   └── database_client.py # SQLite wrapper
├── automation/      # Scheduled job management
│   └── scheduler.py       # Job scheduling setup
├── jobs/            # Scheduled tasks
│   ├── briefing.py        # Daily briefing job
│   └── reminders.py       # Reminder checking job
├── app.py           # Main application entry point
└── scheduler.py     # Scheduler factory
```

## Setup Instructions

### Prerequisites

- Python 3.12+
- Telegram Bot Token (create via BotFather on Telegram)
- Claude API Key (from Anthropic)
- (Optional) Gmail credentials for email integration

### Installation

1. Clone the repository:
```bash
git clone https://github.com/nightmarehel/telegassistant.git
cd telegassistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your credentials:
```
BOT_TOKEN=your_telegram_bot_token_here
ANTHROPIC_API_KEY=your_claude_api_key_here
DB_PATH=data/telegassistant.db
```

5. Run the bot:
```bash
python app.py
```

## Configuration

Edit `.env` to customize:
- `BOT_TOKEN`: Get from Telegram BotFather (@BotFather)
- `ANTHROPIC_API_KEY`: Get from Anthropic console
- `DB_PATH`: Path to SQLite database file

Sensitive files (`.env`, `credentials.json`, `token.json`) are in `.gitignore` and will never be committed.

## Usage

Once running, interact with the bot on Telegram:
- `/start` - Initialize the bot
- `/briefing` - Request an immediate briefing  
- `/remind` - Set a reminder
- `/weather` - Get current weather

## Development

Code is organized by function:
- **ai/**: All external API integrations (Claude, Gmail, weather)
- **bot/**: Telegram interface and command handling
- **data/**: Database operations
- **jobs/**: Scheduled background tasks

## License

MIT
