# NexusGuard Discord Bot

A multipurpose Discord bot built with **Python** and **discord.py** for server moderation, economy management, fun games, and support ticketing. Designed with clean architecture using cogs, SQLite persistence, and comprehensive error handling.

## Features

### Economy System
- `/balance` – Check your current balance
- `/work` – Earn money with hourly cooldown
- `/daily` – Claim daily reward
- `/pay @user amount` – Send money to other members
- `/shop` – View purchasable items
- `/buy item [quantity]` – Buy items from shop
- `/inventory` / `/inv` – View your owned items
- `/roulette amount` – 50/50 gamble to win or lose money

### Leaderboards
- `/leaderboard [limit]` – Show top richest members in the server
- Per-guild balance tracking with SQLite backend
- Slash-command support for modern Discord experience

### Moderation
- `/kick @user [reason]` – Kick a user from the server
- `/ban @user [reason]` – Ban a user from the server
- `/timeout @user minutes [reason]` – Temporarily mute a user
- `/untimeout @user` – Remove timeout
- `/purge amount` – Delete up to 100 messages
- `/warn @user reason` – Issue a warning
- `/warnings @user` – View user's warning history
- **Mod Logs** – All moderation actions logged to designated channel
- **Database Logging** – Actions stored in SQLite for audit trail

### Automod & Safety
- Bad word filtering with automatic message deletion
- Spam detection (5+ messages in 5 seconds triggers timeout)
- Configurable per-guild settings
- Automatic logging of automod actions

### Support Ticket System
- `/ticketpanel` – Spawn ticket creation panel
- Three ticket types: General Support, Bug Report, Ban Appeal
- Auto-created channels with proper permissions
- `/close` button for ticket closure
- `/ticket_stats` – View open ticket statistics

- ### Advanced AI Chat

- `/ask question` – Ask NexusGuard anything (AI Powered with Google Generative AI)
- **Mention Handling** – Reply to the bot when it's mentioned in a channel
- **Async Processing** – Fast, non-blocking AI responses
- **Message Splitting** – Automatically handles long responses (>2000 chars)
- **Context-Aware Responses** – AI understands you're chatting with a Discord bot

### Games
- `/tictactoe @opponent` – Play Tic-Tac-Toe with another user
- `/rps` – Rock Paper Scissors against the bot
- `/coinflip` – Flip a coin
- `/trivia` – Answer random trivia questions
- Interactive button-based gameplay

### Utilities
- Custom `/help` command with command grouping by cog
- Global error handler with user-friendly messages
- Prefix & slash-command support
- Per-guild configuration ready (foundation in place)

## Tech Stack

- **Language:** Python 3.12+
- **Library:** [discord.py](https://discordpy.readthedocs.io/) 2.x
- **Database:** SQLite (`bot.db`) for economy, inventory, warnings, mod logs, and settings
- **Architecture:** Cog-based modular design with custom bot class
- **Error Handling:** Global error handler cog for consistent UX

## Database Schema

- **economy** – User balances per guild (user_id, guild_id, balance)
- **inventory** – User items per guild (user_id, guild_id, item_name, quantity)
- **warnings** – Moderation warnings (user_id, guild_id, reason, mod_id, timestamp)
- **mod_logs** – All moderation actions (guild_id, action, user_id, mod_id, reason, timestamp)
- **settings** – Per-guild configuration (guild_id, key, value)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/revanthsaii/NexusGuard-Discord-Bot.git
cd NexusGuard-Discord-Bot
```

### 2. Install Dependencies

Requires Python 3.12+:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```
DISCORD_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your token from [Discord Developer Portal](https://discord.com/developers/applications).

### 4. Run Locally

```bash
python main.py
```

You should see:
```
Logged in as NexusGuard#1234 ready in X guilds
All cogs loaded!
```

Use `/help` in any Discord server to see all commands.

## Deployment

NexusGuard is designed for 24/7 uptime on:

- **Linux VPS (Ubuntu)** with systemd service for auto-restart
- **Docker** for containerized deployment
- **Student hosting** or cloud providers with persistent uptime

The bot initializes the SQLite database and loads all cogs automatically on startup.

## Project Structure

```
.
├── main.py                 # Bot initialization & database setup
├── cogs/
│   ├── economy.py         # Economy commands and balance management
│   ├── moderation.py      # Moderation & logging
│   ├── support.py         # Support ticket system
│   ├── games.py           # Fun mini-games
│   ├── leaderboard.py     # Ranking & statistics
│   ├── help.py            # Custom help command
│   ├── errors.py          # Global error handler
│   └── ai.py              # AI Chat with Google Generative AI (Gemini)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## Development Notes

**Code Quality:**
- Clean separation of concerns with cogs
- Reusable database helper methods
- Consistent embed styling and error messages
- Per-guild data isolation for multi-server support

**Future Improvements:**
- Slash-command migration for all features
- Advanced economy (stock market, jobs, quests)
- User reputation & XP tracking
- Server analytics dashboard
- Multi-language support

## About the Author

NexusGuard is developed by **Revanth Sai**, a Computer Science undergraduate focusing on full-stack development, algorithms, and practical software engineering.

- **GitHub:** [@revanthsaii](https://github.com/revanthsaii)
- **Email:** [revanthsaitalluri@gmail.com](mailto:revanthsaitalluri@gmail.com)

## License

This project is licensed under the **MIT License** – see [LICENSE](./LICENSE) for details.
