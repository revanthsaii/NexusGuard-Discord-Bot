import discord
import os
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🚀 {bot.user} ready in {len(bot.guilds)} guilds')
    print("✅ All cogs loaded!")

async def setup_hook():
    # Create database if it doesn't exist
    conn = sqlite3.connect('bot.db')
    conn.execute(
        '''CREATE TABLE IF NOT EXISTS economy 
           (user_id INTEGER PRIMARY KEY,
            guild_id INTEGER,
            balance INTEGER DEFAULT 0)'''
    )
    conn.commit()
    conn.close()

    # Load cogs
    await bot.load_extension('cogs.moderation')
    await bot.load_extension('cogs.economy')
    await bot.load_extension('cogs.leaderboard')
    # later:
    # await bot.load_extension('cogs.games')
    # await bot.load_extension('cogs.ai')

bot.setup_hook = setup_hook
bot.run(os.getenv('DISCORD_TOKEN'))
