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

        conn.commit()
        conn.close()

        # Load cogs
        await self.load_extension('cogs.moderation')
        await self.load_extension('cogs.economy')
        await self.load_extension('cogs.leaderboard')
        await self.load_extension('cogs.games')
        await self.load_extension('cogs.help')
        await self.load_extension('cogs.errors')
        # later:
        # await self.load_extension('cogs.ai')


intents = discord.Intents.default()
intents.message_content = True

bot = NexusGuardBot(command_prefix='!', intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f'🚀 {bot.user} ready in {len(bot.guilds)} guilds')
    print("✅ All cogs loaded!")
    await bot.change_presence(
        activity=discord.Game(name='!help | NexusGuard')
    )


if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise RuntimeError('DISCORD_TOKEN not set in environment.')
    bot.run(token)
