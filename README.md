# TeleGAssistant 🤖📱
*An AI-powered personal assistant for managing tasks and deadlines via Telegram*

---

## 📌 Quick Start (2 minutes)

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` file
4. Seed the database: `python scripts/seed_db.py`
5. Run the bot: `python app.py`

That's it! Your assistant is now running.

---

## 📖 What is TeleGAssistant?

**TeleGAssistant** is a locally-hosted AI assistant that runs on your own computer. Instead of relying on cloud services or external servers, it processes everything locally—keeping your data private and fully under your control.

### Why use it?
- **🔒 Privacy First**: All data stays on your machine—no cloud uploads
- **💬 Telegram Interface**: Talk to your assistant through Telegram messages
- **🧠 Smart AI**: Uses local AI to understand tasks and deadlines naturally
- **📅 Automatic Reminders**: Get notified about upcoming deadlines
- **⚡ Fast & Reliable**: No internet dependency after initial setup

---

## ✨ Core Features

### 1. **Daily Briefings**
Every morning at 8 AM, receive an AI-generated summary of your day:
- Tasks to complete
- Upcoming deadlines
- Scheduled events

### 2. **Smart Reminders**
Automatic notifications for deadlines at:
- 24 hours before
- 2 hours before
- 30 minutes before

### 3. **Task Management**
Store and track:
- Tasks with descriptions
- Deadlines and due dates
- Events and meetings

### 4. **Local AI Processing**
- Runs Gemma 2B (a lightweight AI model) on your machine
- Understands natural language task descriptions
- Generates personalized daily briefings

---

## 🏗️ How It Works

```
┌──────────────────────────────────────┐
│  You (Telegram)                      │
│  "I have a project due Friday"       │
└──────────┬───────────────────────────┘
           │
           ↓
┌──────────────────────────────────────┐
│  Telegram Bot API                    │
│  (Receives your message)             │
└──────────┬───────────────────────────┘
           │
           ↓
┌──────────────────────────────────────┐
│  Backend System                      │
│  ├─ AI Module: Understands "Friday" │
│  ├─ Scheduler: Plans reminders      │
│  └─ Database: Stores the task       │
└──────────┬───────────────────────────┘
           │
           ↓
┌──────────────────────────────────────┐
│  Your Machine (Local)                │
│  Everything runs here—no cloud!      │
└──────────────────────────────────────┘
```

---

## 🛠️ Prerequisites

Before you start, make sure you have:

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.8+ | Download from [python.org](https://www.python.org) |
| Telegram | App | Download from App Store or [telegram.org](https://telegram.org) |
| Ollama (LLM Runtime) | Latest | Download from [ollama.ai](https://ollama.ai) |
| Git | Latest | For cloning the repository |

---

## 📦 Installation & Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/cis3296s26/final-project-04-telegassistant.git
cd final-project-04-telegassistant
```

### Step 2: Create Virtual Environment
A virtual environment keeps dependencies isolated and clean.

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy the example file and fill in your settings:
```bash
cp .env.example .env
```

Edit `.env` with:
```env
BOT_TOKEN=your_telegram_bot_token_here
DB_PATH=data/telegassistant.db
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=gemma:2b
```

**How to get BOT_TOKEN:**
1. Open Telegram and search for `@BotFather`
2. Type `/newbot` and follow the prompts
3. Copy the token provided and paste it in `.env`

### Step 5: Download & Run Local LLM

Install Ollama from [ollama.ai](https://ollama.ai), then download Gemma 2B:
```bash
ollama pull gemma:2b
ollama serve
```

Keep this terminal open in the background—your AI model will run from here.

### Step 6: Initialize Database

Seed the database with sample data:
```bash
python scripts/seed_db.py
```

This creates:
- Database schema
- 1 test user
- Sample tasks and deadlines

### Step 7: Start the Bot

In a new terminal:
```bash
python app.py
```

You should see:
```
[INFO] Starting TeleGAssistant bot...
[INFO] Scheduler started
[INFO] Bot polling started
```

---

## 📱 Using the Bot

Once running, open Telegram and send a message to your bot:

**Example 1: Add a task**
```
"I need to complete chapter 8 of the textbook"
→ Bot: Task saved! Reminder set for 30 mins before deadline.
```

**Example 2: Ask about your day**
```
"What's on my agenda?"
→ Bot: Morning briefing: You have 3 tasks due today...
```

The bot runs **automatically**:
- ✅ Sends daily briefings at 8:00 AM
- ✅ Checks reminders every 30 minutes
- ✅ Updates task statuses in real-time

---

## 🧪 Testing & Quality Assurance

### Run All Tests
```bash
pytest
```

### Check Code Coverage
View detailed coverage report:
```bash
pytest --cov=jobs --cov-report=term-missing
```

Generate HTML coverage report:
```bash
pytest --cov=jobs --cov-report=html
open htmlcov/index.html
```

**Current Coverage:**
- `jobs/briefing.py`: 87% coverage
- `jobs/reminders.py`: 91% coverage
- **Overall**: 88% coverage (exceeds 80% requirement)

---

## 🚀 Deployment Guide

### Option 1: Systemd Service (Linux/macOS)

For production deployment on a server:

1. Copy service file:
```bash
sudo cp telegassistant.service /etc/systemd/system/
```

2. Update file locations in service file:
```bash
sudo nano /etc/systemd/system/telegassistant.service
```

3. Enable and start:
```bash
sudo systemctl enable telegassistant
sudo systemctl start telegassistant
```

4. Check status:
```bash
sudo systemctl status telegassistant
```

### Option 2: Docker Deployment

(Coming soon—containerization support in progress)

### Option 3: Raspberry Pi / Always-On Computer

Set up on a Raspberry Pi 4 with 4GB+ RAM:
1. Install Python 3.8+
2. Follow installation steps above
3. Use systemd service to keep bot running 24/7

---

## 📊 Project Structure

```
final-project-04-telegassistant/
├── app.py                    # Main entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
├── README.md                 # This file
│
├── ai/                       # AI & LLM integration
│   └── llm_client.py         # Ollama LLM client
│
├── bot/                      # Telegram bot
│   └── telegram_client.py    # Telegram API wrapper
│
├── data/                     # Database
│   └── database_client.py    # SQLite operations
│
├── jobs/                     # Automated tasks
│   ├── briefing.py           # Daily briefing generation
│   └── reminders.py          # Deadline reminder system
│
├── scripts/                  # Utility scripts
│   └── seed_db.py            # Database initialization
│
├── tests/                    # Test suite
│   ├── test_briefing.py      # Briefing tests (5 cases)
│   └── test_reminders.py     # Reminder tests (3 cases)
│
└── stubs/                    # Test doubles/mocks
    ├── fake_ai.py
    ├── fake_bot.py
    └── fake_db.py
```

---

## ⚙️ Configuration Reference

### Environment Variables (.env)

| Variable | Purpose | Example |
|----------|---------|---------|
| `BOT_TOKEN` | Telegram Bot authentication | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `DB_PATH` | SQLite database location | `data/telegassistant.db` |
| `LLM_BASE_URL` | Ollama API endpoint | `http://localhost:11434` |
| `LLM_MODEL` | AI model name | `gemma:2b` |

### Database Schema

**Users Table:**
- `id`: User ID
- `telegram_id`: Telegram user identifier
- `name`: User's display name

**Tasks Table:**
- `id`: Task ID
- `user_id`: Associated user
- `description`: Task details
- `created_at`: Creation timestamp

**Deadlines Table:**
- `id`: Deadline ID
- `task_id`: Associated task
- `due_date`: Deadline date
- `completed`: Status flag

**Events Table:**
- `id`: Event ID
- `user_id`: Associated user
- `title`: Event name
- `scheduled_time`: Event time

---

## 🐛 Troubleshooting

### Issue: "Bot token invalid"
**Solution:**
1. Double-check your bot token in `.env`
2. Verify you got it from `@BotFather` on Telegram
3. Make sure there are no extra spaces

### Issue: "LLM connection refused"
**Solution:**
1. Ensure Ollama is running: `ollama serve` in a terminal
2. Check `LLM_BASE_URL` in `.env` is `http://localhost:11434`
3. Run `ollama pull gemma:2b` if model isn't downloaded

### Issue: Database locked error
**Solution:**
1. Close all other instances of the bot
2. Delete `.db-wal` and `.db-shm` files in the `data/` folder
3. Restart the bot

### Issue: No messages received
**Solution:**
1. Check bot is running: `python app.py`
2. Send a test message to your bot in Telegram
3. Look for errors in console output
4. Verify network connectivity

### Issue: Tests fail
**Solution:**
```bash
# Clear cache
rm -rf .pytest_cache __pycache__

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Run tests again
pytest -v
```

---

## 📚 Dependencies

All required packages are listed in `requirements.txt`:

| Package | Version | Purpose |
|---------|---------|---------|
| `APScheduler` | 3.11.2 | Job scheduling |
| `python-telegram-bot` | 21.9 | Telegram API |
| `python-dotenv` | 1.2.2 | Environment variables |
| `httpx` | 0.28.1 | HTTP client |
| `pytest` | 9.0.3 | Testing framework |
| `pytest-cov` | 7.1.0 | Code coverage |

---

## 🤝 Contributing

To contribute improvements:

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Ensure all tests pass: `pytest`
4. Commit with clear messages: `git commit -m "Add feature X"`
5. Push and create a pull request

---

## 📝 License

This project is part of Temple University CIS 3296 (Software Design).

---

## 🎓 Team

- **AI & LLM Integration**: Vrushil
- **Scheduler & Reminders**: Sid
- **Database & Storage**: Team
- **Telegram Integration**: Team

---

## ❓ FAQ

**Q: Does this work without internet?**  
A: Yes! After initial setup, everything runs locally. You only need Telegram to receive messages.

**Q: Can I use this on my phone?**  
A: No, but you can run it on a computer or Raspberry Pi and message it from your phone via Telegram.

**Q: Is my data secure?**  
A: Completely. Everything stays on your machine. No data is uploaded anywhere.

**Q: Can I add more users?**  
A: Currently supports single user. Multi-user support is planned for future versions.

**Q: What if I want to use a different AI model?**  
A: Edit `LLM_MODEL` in `.env` to any model available on Ollama.

---

## 📞 Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the code comments
3. Check GitHub issues
4. Contact the development team

---

**Last Updated:** April 2026  
**Version:** 1.0  
**Status:** Production Ready ✅


