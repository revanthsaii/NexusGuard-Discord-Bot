import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime
import re

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_cache = {}
        self.bad_words = ["badword1", "badword2"] # Add more as needed or move to DB/Config
        
    def add_warning(self, user_id, guild_id, reason, moderator_id):
        conn = sqlite3.connect('bot.db')
        conn.execute(
            'INSERT INTO warnings (user_id, guild_id, reason, moderator_id, timestamp) VALUES (?, ?, ?, ?, ?)',
            (user_id, guild_id, reason, moderator_id, datetime.datetime.now().timestamp())
        )
        conn.commit()
        conn.close()

    def get_warnings(self, user_id, guild_id):
        conn = sqlite3.connect('bot.db')
        cursor = conn.execute(
            'SELECT reason, moderator_id, timestamp FROM warnings WHERE user_id = ? AND guild_id = ?',
            (user_id, guild_id)
        )
        warnings = cursor.fetchall()
        conn.close()
        return warnings

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        # Automod: Bad Words
        if any(word in message.content.lower() for word in self.bad_words):
            await message.delete()
            await message.channel.send(f"{message.author.mention} Watch your language!", delete_after=5)
            return

        # Automod: Spam
        user_id = message.author.id
        now = discord.utils.utcnow().timestamp()
        
        if user_id not in self.spam_cache:
            self.spam_cache[user_id] = []
            
        self.spam_cache[user_id].append(now)
        self.spam_cache[user_id] = [t for t in self.spam_cache[user_id] if now - t < 5] # 5 seconds window
        
        if len(self.spam_cache[user_id]) > 5: # > 5 messages in 5 seconds
            try:
                await message.author.timeout(datetime.timedelta(minutes=5), reason="Automod: Spamming")
                await message.channel.send(f"🚫 {message.author.mention} has been temporarily muted for spamming.", delete_after=10)
                # Clear cache to prevent loop
                self.spam_cache[user_id] = [] 
            except discord.Forbidden:
                pass


    # --- Commands ---

    @app_commands.command(name="kick", description="Kick a user")
    @app_commands.describe(user="User to kick", reason="Reason for kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot kick this user.", ephemeral=True)
            return
            
        await user.kick(reason=reason)
        await interaction.response.send_message(f"👢 Kicked {user.mention} | Reason: {reason}")

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.describe(user="User to ban", reason="Reason for ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot ban this user.", ephemeral=True)
            return

        await user.ban(reason=reason)
        await interaction.response.send_message(f"🔨 Banned {user.mention} | Reason: {reason}")

    @app_commands.command(name="timeout", description="Timeout (mute) a user")
    @app_commands.describe(user="User to timeout", minutes="Duration in minutes", reason="Reason")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "No reason"):
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot timeout this user.", ephemeral=True)
            return

        duration = datetime.timedelta(minutes=minutes)
        await user.timeout(duration, reason=reason)
        await interaction.response.send_message(f"🤐 Timed out {user.mention} for {minutes}m | Reason: {reason}")

    @app_commands.command(name="untimeout", description="Remove timeout from a user")
    @app_commands.describe(user="User to untimeout")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, user: discord.Member):
        if not user.is_timed_out():
            await interaction.response.send_message(f"❌ {user.mention} is not timed out.", ephemeral=True)
            return
            
        await user.timeout(None, reason="Untimeout by moderator")
        await interaction.response.send_message(f"🔊 Removed timeout from {user.mention}")

    @app_commands.command(name="purge", description="Delete a number of messages")
    @app_commands.describe(amount="Number of messages to delete")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        if amount > 100:
            await interaction.response.send_message("❌ Can only delete up to 100 messages at a time.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True) 
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(user="User to warn", reason="Reason for warning")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if user.bot:
             await interaction.response.send_message("❌ Cannot warn bots.", ephemeral=True)
             return
             
        self.add_warning(user.id, interaction.guild.id, reason, interaction.user.id)
        
        try:
            await user.send(f"⚠️ You have been warned in **{interaction.guild.name}** | Reason: {reason}")
        except:
            pass
            
        await interaction.response.send_message(f"⚠️ Warned {user.mention} | Reason: {reason}")

    @app_commands.command(name="warnings", description="View warnings for a user")
    @app_commands.describe(user="User to check")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        warns = self.get_warnings(user.id, interaction.guild.id)
        
        if not warns:
            await interaction.response.send_message(f"✅ {user.mention} has no warnings.")
            return
            
        embed = discord.Embed(title=f"Warnings for {user.display_name}", color=discord.Color.yellow())
        for reason, mod_id, ts in warns:
             mod = interaction.guild.get_member(mod_id)
             mod_name = mod.display_name if mod else "Unknown"
             date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
             embed.add_field(name=date_str, value=f"**Reason:** {reason}\n**Mod:** {mod_name}", inline=False)
             
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
