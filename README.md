# TeleGAssistant 🤖📱
An AI-powered personal assistant for managing tasks and deadlines via Telegram.

## Overview

TeleGAssistant is a locally-hosted AI assistant that runs entirely on your computer. It integrates with Telegram to help you manage tasks, deadlines, and daily schedules while keeping all your data private and on your machine.

**Key Features:**
- 💬 Chat with your assistant via Telegram
- 🧠 Local AI that understands tasks naturally
- 📅 Daily briefings at 8 AM
- ⏰ Smart reminders (24h, 2h, 30 min before deadlines)
- 🔒 All data stays on your machine—no cloud uploads

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/cis3296s26/final-project-04-telegassistant.git
cd final-project-04-telegassistant

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your BOT_TOKEN and settings

# 5. Set up local AI (in a separate terminal)
ollama pull gemma:2b
ollama serve

# 6. Initialize database
python scripts/seed_db.py

# 7. Run the bot
python app.py
```

---

## Prerequisites

- **Python** 3.8+
- **Telegram** (app or web version)
- **Ollama** (for local AI) - [Download here](https://ollama.ai)
- **Git** (for cloning)

---

## Configuration

### Getting Your Bot Token

1. Open Telegram and search for `@BotFather`
2. Type `/newbot` and follow the prompts
3. Copy the token and paste it in your `.env` file

### Environment Variables

Create or update `.env` with:
```env
BOT_TOKEN=your_telegram_bot_token
DB_PATH=data/telegassistant.db
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=gemma:2b
```

---

## How to Use

Once running, send messages to your bot in Telegram:

**Add a task:**
```
"I need to complete chapter 8 by Friday"
→ Bot saves task and sets reminders
```

**Get daily briefing:**
The bot automatically sends a summary every morning at 8 AM with:
- Your tasks
- Upcoming deadlines
- Scheduled events

---

## Testing

Run the test suite:
```bash
pytest
```

Check code coverage:
```bash
pytest --cov=jobs --cov-report=term-missing
```

**Coverage Stats:**
- `briefing.py`: 87%
- `reminders.py`: 91%
- **Total**: 88% (exceeds 80% requirement)

---

## Project Structure

```
final-project-04-telegassistant/
├── app.py                  # Main entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── ai/                    # AI & LLM integration
├── bot/                   # Telegram bot
├── data/                  # Database
├── jobs/                  # Scheduled tasks
│   ├── briefing.py        # Daily briefing job
│   └── reminders.py       # Reminder system
├── scripts/               # Utility scripts
│   └── seed_db.py         # Database setup
├── tests/                 # Test suite
│   ├── test_briefing.py
│   └── test_reminders.py
└── stubs/                 # Test mocks
```

---

## Deployment

### Production on Linux/macOS

```bash
# Copy service file
sudo cp telegassistant.service /etc/systemd/system/

# Enable and start
sudo systemctl enable telegassistant
sudo systemctl start telegassistant

# Check status
sudo systemctl status telegassistant
```

### On Raspberry Pi

Install Python 3.8+, follow the Quick Start steps, and use systemd service to keep it running 24/7.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| APScheduler | 3.11.2 | Job scheduling |
| python-telegram-bot | 21.9 | Telegram API |
| python-dotenv | 1.2.2 | Environment config |
| httpx | 0.28.1 | HTTP client |
| pytest | 9.0.3 | Testing |
| pytest-cov | 7.1.0 | Coverage reporting |

---

## Database Schema

| Table | Columns | Purpose |
|-------|---------|---------|
| **Users** | id, telegram_id, name | Store user info |
| **Tasks** | id, user_id, description, created_at | Store tasks |
| **Deadlines** | id, task_id, due_date, completed | Track deadlines |
| **Events** | id, user_id, title, scheduled_time | Store events |

---

## Development

To contribute:

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and write tests
3. Run: `pytest`
4. Commit and push: `git commit -m "Description"`
5. Create a pull request

---

## License

Part of Temple University CIS 3296 (Software Design).

---

**Version:** 1.0 | **Status:** Production Ready ✅


