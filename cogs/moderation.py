import discord
from discord.ext import commands
from discord import app_commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_cache = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        user_id = message.author.id
        
        now = discord.utils.utcnow().timestamp()
        if user_id not in self.spam_cache:
            self.spam_cache[user_id] = []
        self.spam_cache[user_id].append(now)
        self.spam_cache[user_id] = [t for t in self.spam_cache[user_id] if now - t < 10]
        
        if len(self.spam_cache[user_id]) > 5:
            await message.delete()
            await message.channel.send(f"{message.author.mention} spam detected!", delete_after=5)

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.describe(user="User to ban", reason="Ban reason")
    @commands.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        await user.ban(reason=reason)
        await interaction.response.send_message(f"🔨 Banned {user.mention}: {reason}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
