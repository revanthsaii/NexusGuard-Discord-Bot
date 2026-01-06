import os
import sqlite3
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class NexusGuardBot(commands.Bot):
    async def setup_hook(self):
        # Create database if it doesn't exist
        conn = sqlite3.connect('bot.db')
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER,
                guild_id INTEGER,
                balance INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )'''
        )
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                reason TEXT,
                moderator_id INTEGER,
                timestamp REAL
            )'''
        )
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS settings (
                guild_id INTEGER,
                key TEXT,
                value TEXT,
                PRIMARY KEY (guild_id, key)
            )'''
        )
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS mod_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                action TEXT,
                user_id INTEGER,
                mod_id INTEGER,
                reason TEXT,
                timestamp REAL
            )'''
        )
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS reputation (
                user_id INTEGER,
                guild_id INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                last_xp_time REAL DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )'''
        )
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                name TEXT,
                min_pay INTEGER,
                max_pay INTEGER,
                required_level INTEGER
            )'''
        )
        # Pre-seed some jobs if empty
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM jobs")
        if cursor.fetchone()[0] == 0:
            jobs_data = [
                ("dishwasher", "Dishwasher", 50, 100, 1),
                ("cashier", "Cashier", 100, 200, 5),
                ("manager", "Manager", 300, 500, 10),
                ("ceo", "CEO", 1000, 2000, 25)
            ]
            cursor.executemany("INSERT INTO jobs VALUES (?,?,?,?,?)", jobs_data)

        conn.commit()
        conn.close()

        # Load cogs
        await self.load_extension('cogs.moderation')
        await self.load_extension('cogs.economy')
        await self.load_extension('cogs.leaderboard')
        await self.load_extension('cogs.games')
        await self.load_extension('cogs.help')
        await self.load_extension('cogs.errors')
        await self.load_extension('cogs.support')
        await self.load_extension('cogs.config')
        await self.load_extension('cogs.leveling')
        await self.load_extension('cogs.dashboard')
        await self.load_extension('cogs.ai')
        await self.load_extension('cogs.welcome')
        await self.load_extension('cogs.reactionroles')
        await self.load_extension('cogs.polls')
        await self.load_extension('cogs.utility')


intents = discord.Intents.default()
intents.message_content = True

bot = NexusGuardBot(command_prefix='!', intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} ready in {len(bot.guilds)} guilds')
    print("All cogs loaded!")
    await bot.change_presence(
        activity=discord.Game(name='!help | NexusGuard')
    )


if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise RuntimeError('DISCORD_TOKEN not set in environment.')
    bot.run(token)
