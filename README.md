# Shield NexusGuard Discord Bot

Advanced Discord moderation & economy bot built with **Python**, **discord.py**, and **SQLite**.
Designed as a real, production-style project to showcase clean architecture, database use, and Discord bot development skills.

---

## Sparkles Features

- Shield **Smart moderation**
  - Basic anti-spam: auto-deletes rapid message bursts.
  - `!ban @user <reason>` command for manual moderation.

- Money Bag **Economy system**
  - `!work` to earn random virtual currency.
  - `!balance` to view current balance with a clean embed.
  - Data persisted per user + per guild in SQLite.

- Trophy **Rich leaderboards**
  - `!leaderboard` shows top 10 richest members in the server.
  - Medal styling (Gold, Silver, Bronze) and server icon thumbnail.

- Gear **Modular architecture**
  - Separate cogs for moderation, economy, leaderboard.
  - Centralized database setup in `main.py`.

> Prefix: `!` (e.g. `!work`, `!balance`, `!leaderboard`, `!ban`)

---

## Bricks Tech Stack

- **Language:** Python 3.11+
- **Library:** discord.py 2.x
- **Database:** SQLite (`bot.db`)
- **Other:** python-dotenv for environment variables

---

## Rocket Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/revanthsaii/NexusGuard-Discord-Bot.git
cd NexusGuard-Discord-Bot
```

### 2. Create a Discord Bot & get token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application -> Add a **Bot**.
3. Enable **Message Content Intent** (and Members Intent if needed).
4. Copy the **Bot Token**.

### 3. Environment variables

Create a `.env` file in the project root:

```
DISCORD_TOKEN=your_discord_bot_token_here
```

There is also a `.env.example` file showing the expected format.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the bot

```bash
python main.py
```

You should see:

```
Rocket NexusGuard#1234 ready in X guilds
Check mark All cogs loaded!
```

---

## Book Commands

| Command            | Description                                  |
| ------------------ | -------------------------------------------- |
| `!work`            | Work to earn random virtual currency         |
| `!balance`         | Show your current balance                    |
| `!leaderboard`     | Show top 10 richest users in the server      |
| `!ban @user reason`| Ban a user (requires Ban Members permission) |

---

## Building Project Structure

```
NexusGuard-Discord-Bot/
|-- main.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- bot.db # auto-created by the bot
`-- cogs/
    |-- __init__.py
    |-- moderation.py # spam detection + !ban
    |-- economy.py # !work, !balance
    `-- leaderboard.py # !leaderboard
```

---

## Tools Future Improvements

- Button-based mini-games (e.g. Tic-Tac-Toe).
- Config system per guild (enable/disable features).
- Slash command versions of the main commands.
- Logging and analytics for moderation actions.

---

## Memo License

This project is for educational and portfolio purposes.
You may fork and experiment with it; please credit the original repository if you use it as a base.
