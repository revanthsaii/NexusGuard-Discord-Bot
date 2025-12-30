# NexusGuard Discord Bot

NexusGuard is a multipurpose Discord bot built with **Python** and **discord.py** that focuses on server moderation, a rich economy system, fun games, and quality-of-life utilities. It is designed as a clean, extensible project with cogs, SQLite storage, and clear error handling.

---

## Features

- **Economy**
  - `!balance` – Check your current balance.
  - `!work` – Earn money with an hourly cooldown.
  - `!daily` – Claim a daily reward.
  - `!pay @user amount` – Send money to other members.
  - `!shop` – View purchasable items.
  - `!buy <item> [quantity]` – Buy items from the shop.
  - `!inventory` / `!inv` – View your owned items.
  - `!roulette amount` – 50/50 gamble to win or lose money. [web:180][web:183][web:358]

- **Leaderboards**
  - `!leaderboard` / `!lb` / `!top` – Show top richest members in the current server, based on balances stored in SQLite. [web:250][web:253]

- **Moderation**
  - Modular moderation commands (e.g., kick/ban, clear, etc.) organized in a dedicated cog and integrated with global error handling. *(Commands depend on the current version of `cogs/moderation.py`.)* [web:169][web:191]

- **Games**
  - Fun mini‑games implemented as separate cogs (e.g., tic‑tac‑toe and more), using the same command framework and embed style. [web:169]

- **Custom Help & Error Handling**
  - Custom `!help` command with embeds showing commands grouped by cog and short descriptions.
  - Global error handler cog that converts common errors (missing arguments, missing permissions, cooldowns) into user‑friendly messages instead of raw tracebacks. [web:187][web:295][web:304]

---

## Tech Stack

- **Language:** Python 3.12+
- **Library:** [discord.py](https://discordpy.readthedocs.io/en/stable/) commands extension (prefix commands). [web:169][web:380]
- **Database:** SQLite (`bot.db`) for persistent economy and inventory data.
- **Structure:** Cog-based architecture (`cogs/`) with a custom `NexusGuardBot` class and `setup_hook` for database initialization and cog loading. [web:182][web:191]

---

## Getting Started

### 1. Clone the repository

git clone https://github.com/revanthsaii/NexusGuard-Discord-Bot.git
cd NexusGuard-Discord-Bot


### 2. Install dependencies

Make sure you have Python 3.12+ installed.

pip install -r requirements.txt

### 3. Configure environment variables

Create a `.env` file in the project root:

DISCORD_TOKEN=your_real_discord_bot_token_here


- The token is **not** committed to Git and stays only in this file. [web:165][web:168]

### 4. Run the bot locally

python main.py

You should see a log similar to:

🚀 NexusGuard#1234 ready in X guilds
✅ All cogs loaded!

Use `!help` in your server to see all available commands.

---

## Economy & Database Design

- Balances are stored in an `economy` table with per‑guild rows:

  - `user_id` – Discord user ID.
  - `guild_id` – Server ID.
  - `balance` – User’s balance in that server.

- Inventory is stored in an `inventory` table:

  - `user_id`, `guild_id`, `item_name`, `quantity`.

- All queries are kept simple and explicit (no ORMs), using helper methods like `get_balance`, `change_balance`, and `get_inventory` for reuse across commands. [web:180][web:200][web:359]

---

## Deployment

NexusGuard is designed to run 24/7 on:

- A small **Linux VPS** (Ubuntu) using `systemd`:
  - `NexusGuardBot` creates the database and loads all cogs in `setup_hook`.
  - A systemd service can keep the bot online across reboots with automatic restart. [web:118][web:182]
- Or free / student‑friendly platforms (bot hosts or cloud credits) for persistent uptime during development. [web:100][web:110][web:120]

---

## Roadmap

Planned improvements include:

- Slash-command versions of core features for a more modern Discord experience.
- Additional games and advanced economy mechanics (e.g., stock market, jobs, or quests). [web:183][web:356]
- Logging and analytics (mod logs, transaction logs) using the existing SQLite backend.

---
## About the Author

NexusGuard is developed and maintained by **Revanth Sai**, a Computer Science undergraduate with a focus on full‑stack development, algorithms, and practical software projects.

- GitHub: [@revanthsaii](https://github.com/revanthsaii)
- Email: revanthsaitalluri@gmail.com

## License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for full license text.
