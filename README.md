# NexusGuard Discord Bot

A **feature-rich, pro-level Discord bot** built with Python and discord.py. Includes AI chat, advanced economy, comprehensive moderation, AutoMod, games, leveling, support tickets, and more!

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### 🤖 AI Chat (Powered by Gemini)
- `@NexusGuard <message>` – Chat naturally with the bot
- `/ask <question>` – Ask anything and get AI-powered responses
- Context-aware responses with Discord bot persona

### 💰 Advanced Economy System
- **Banking**: `/balance`, `/deposit`, `/withdraw` – Separate wallet and bank
- **Earning**: `/work`, `/daily`, `/crime` – Multiple ways to earn
- **Crime System**: `/rob @user` – Steal from others (with risk!)
- **Gambling**: `/coinflip`, `/slots`, `/roulette` – Win big or lose it all
- **Shop**: `/shop`, `/buy`, `/inventory` – Purchase and use items
- **Jobs**: `/jobs` – Unlock higher-paying jobs as you level up
- **Cooldowns**: Database-backed cooldowns for all commands
- **Interest**: 2% daily interest on bank balance

### 🛡️ Comprehensive AutoMod
- `/automod settings` – View current configuration
- `/automod toggle <feature>` – Enable/disable features:
  - **Anti-Spam** – Auto-timeout for message spam
  - **Anti-Links** – Block all URLs
  - **Anti-Invites** – Block Discord invite links
  - **Anti-Caps** – Block excessive caps
  - **Anti-Mentions** – Block mention spam
- `/automod addword <word>` – Add custom banned words
- `/automod whitelist <channel>` – Exclude channels from AutoMod

### 👮 Moderation
- `/kick`, `/ban`, `/timeout`, `/untimeout` – User management
- `/warn`, `/warnings` – Warning system with history
- `/purge` – Bulk delete messages
- **Mod Logs** – All actions logged to designated channel
- **Database Logging** – Full audit trail in SQLite

### 📊 Leveling & XP System
- Automatic XP gain from chatting
- `/rank` – View your level and XP progress
- `/levels` – Server XP leaderboard

### 🎮 Games
- `/tictactoe @user` – Play Tic-Tac-Toe
- `/rps` – Rock Paper Scissors
- `/coinflip` – Flip a coin
- `/trivia` – Answer trivia questions

### 🎫 Support Tickets
- `/ticketpanel` – Create ticket panel with categories
- Smart tickets: General Support, Bug Report, Ban Appeal
- `/ticket_stats` – View open ticket statistics
- Auto-created private channels with proper permissions

### 🖼️ Welcome System
- `/welcomesetup` – Configure welcome messages
- Auto-role assignment for new members
- Custom welcome channel

### 🎭 Reaction Roles
- `/reactionrole` – Create self-assignable role panels
- Button-based role selection
- Persistent across bot restarts

### 📊 Polls
- `/poll` – Create interactive polls with progress bars
- Anonymous voting with live results

### 🛠️ Utilities
- `/remind <time> <message>` – Set reminders
- `/avatar [user]` – View user's avatar
- `/userinfo [user]` – Detailed user information
- `/server health` – Server safety and activity scores

### ⚙️ Configuration
- `/config` – Server-wide bot configuration
- Per-guild settings stored in database
- `!sync` – Sync slash commands (admin only)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/revanthsaii/NexusGuard-Discord-Bot.git
cd NexusGuard-Discord-Bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file:
```env
DISCORD_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the Bot
```bash
python main.py
```

### 5. Sync Commands
Run `!sync` in your Discord server (admin only) to register slash commands.

## 📁 Project Structure

```
NexusGuard-Discord-Bot/
├── main.py              # Bot initialization & database setup
├── cogs/
│   ├── ai.py           # AI chat with Gemini
│   ├── automod.py      # AutoMod system
│   ├── config.py       # Server configuration
│   ├── dashboard.py    # Server health dashboard
│   ├── economy.py      # Advanced economy system
│   ├── errors.py       # Global error handler
│   ├── games.py        # Mini-games
│   ├── help.py         # Custom help command
│   ├── leaderboard.py  # Economy leaderboard
│   ├── leveling.py     # XP & leveling system
│   ├── moderation.py   # Moderation commands
│   ├── polls.py        # Interactive polls
│   ├── reactionroles.py # Self-assignable roles
│   ├── support.py      # Ticket system
│   ├── utility.py      # Utility commands
│   └── welcome.py      # Welcome system
├── requirements.txt
├── .env.example
└── README.md
```

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `economy` | User wallets and bank balances |
| `inventory` | User items |
| `warnings` | Moderation warnings |
| `mod_logs` | All moderation actions |
| `settings` | Per-guild configuration |
| `reputation` | XP and levels |
| `jobs` | Available jobs with requirements |
| `cooldowns` | Command cooldown tracking |
| `investments` | User investments |
| `automod_settings` | AutoMod configuration |
| `banned_words` | Custom banned words per guild |
| `reaction_roles` | Reaction role panels |

## 🔧 Tech Stack

- **Language:** Python 3.12+
- **Library:** discord.py 2.x
- **AI:** Google Generative AI (Gemini)
- **Database:** SQLite
- **Architecture:** Cog-based modular design

## 👨‍💻 Author

**Revanth Sai** – Computer Science undergraduate

- GitHub: [@revanthsaii](https://github.com/revanthsaii)
- Email: revanthsaitalluri@gmail.com

## 📄 License

This project is licensed under the **MIT License** – see [LICENSE](./LICENSE) for details.
