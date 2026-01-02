import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_cache = {}
        self.bad_words = ["badword1", "badword2"]

    def log_to_db(self, guild_id, action, user_id, mod_id, reason):
        conn = sqlite3.connect('bot.db')
        conn.execute(
            'INSERT INTO mod_logs (guild_id, action, user_id, mod_id, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
            (guild_id, action, user_id, mod_id, reason, datetime.datetime.now().timestamp())
        )
        conn.commit()
        conn.close()

    async def log_to_channel(self, guild, action, user, mod, reason):
        # 1. Get channel ID from settings
        conn = sqlite3.connect('bot.db')
        cur = conn.execute('SELECT value FROM settings WHERE guild_id = ? AND key = ?', (guild.id, "mod_log_channel"))
        row = cur.fetchone()
        conn.close()
        
        if not row: return # No log channel set
        
        channel_id = int(row[0])
        channel = guild.get_channel(channel_id)
        if not channel: return
        
        embed = discord.Embed(title=f"Mod Action: {action}", color=discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="Moderator", value=f"{mod.mention}", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        await channel.send(embed=embed)

    async def execute_mod_action(self, interaction, user, action_type, reason, func):
        # Helper to reduce code duplication
        try:
            await func()
            self.log_to_db(interaction.guild.id, action_type, user.id, interaction.user.id, reason)
            await self.log_to_channel(interaction.guild, action_type, user, interaction.user, reason)
            await interaction.response.send_message(f"✅ **{action_type}** {user.mention} | Reason: {reason}")
        except discord.Forbidden:
             await interaction.response.send_message("❌ I do not have permission to do that.", ephemeral=True)
        except Exception as e:
             await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        # Automod: Bad Words
        if any(word in message.content.lower() for word in self.bad_words):
            await message.delete()
            # Log this
            self.log_to_db(message.guild.id, "Automod Delete", message.author.id, self.bot.user.id, "Bad Word")
            # Might be too spammy to log to channel, but skipping for now
            await message.channel.send(f"{message.author.mention} Watch your language!", delete_after=5)
            return

        # Automod: Spam
        user_id = message.author.id
        now = discord.utils.utcnow().timestamp()
        
        if user_id not in self.spam_cache:
            self.spam_cache[user_id] = []
            
        self.spam_cache[user_id].append(now)
        self.spam_cache[user_id] = [t for t in self.spam_cache[user_id] if now - t < 5] 
        
        if len(self.spam_cache[user_id]) > 5:
            try:
                # Timeout
                await message.author.timeout(datetime.timedelta(minutes=5), reason="Automod: Spamming")
                self.log_to_db(message.guild.id, "Automod Timeout", user_id, self.bot.user.id, "Spamming")
                
                await message.channel.send(f"🚫 {message.author.mention} has been temporarily muted for spamming.", delete_after=10)
                self.spam_cache[user_id] = [] 
            except discord.Forbidden:
                pass


    # --- Commands ---

    @app_commands.command(name="kick", description="Kick a user")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot kick this user.", ephemeral=True)
            return
        await self.execute_mod_action(interaction, user, "Kick", reason, lambda: user.kick(reason=reason))

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot ban this user.", ephemeral=True)
            return
        await self.execute_mod_action(interaction, user, "Ban", reason, lambda: user.ban(reason=reason))

    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "No reason"):
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Cannot timeout this user.", ephemeral=True)
            return
        duration = datetime.timedelta(minutes=minutes)
        await self.execute_mod_action(interaction, user, "Timeout", reason, lambda: user.timeout(duration, reason=reason))

    @app_commands.command(name="untimeout", description="Remove timeout")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, user: discord.Member):
        if not user.is_timed_out():
            await interaction.response.send_message("❌ User is not timed out.", ephemeral=True)
            return
        await self.execute_mod_action(interaction, user, "Untimeout", "Manual Removal", lambda: user.timeout(None))

    @app_commands.command(name="purge", description="Delete messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        if amount > 100:
             await interaction.response.send_message("❌ Limit is 100.", ephemeral=True)
             return
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)
        self.log_to_db(interaction.guild.id, "Purge", 0, interaction.user.id, f"Count: {len(deleted)}")

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if user.bot:
             await interaction.response.send_message("❌ Cannot warn bots.", ephemeral=True)
             return
        
        # Add to DB
        conn = sqlite3.connect('bot.db')
        conn.execute('INSERT INTO warnings (user_id, guild_id, reason, moderator_id, timestamp) VALUES (?, ?, ?, ?, ?)',
                     (user.id, interaction.guild.id, reason, interaction.user.id, datetime.datetime.now().timestamp()))
        conn.commit()
        conn.close()

        # Log
        self.log_to_db(interaction.guild.id, "Warn", user.id, interaction.user.id, reason)
        await self.log_to_channel(interaction.guild, "Warn", user, interaction.user, reason)
        
        try:
            await user.send(f"⚠️ You Warned in **{interaction.guild.name}** | {reason}")
        except: pass
        await interaction.response.send_message(f"⚠️ Warned {user.mention} | Reason: {reason}")

    @app_commands.command(name="warnings", description="View warnings")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        conn = sqlite3.connect('bot.db')
        cursor = conn.execute('SELECT reason, moderator_id, timestamp FROM warnings WHERE user_id = ? AND guild_id = ?', (user.id, interaction.guild.id))
        warns = cursor.fetchall()
        conn.close()

        if not warns:
            await interaction.response.send_message(f"✅ {user.mention} has no warnings.")
            return

        embed = discord.Embed(title=f"Warnings for {user.display_name}", color=discord.Color.yellow())
        for reason, mod_id, ts in warns:
             mod = interaction.guild.get_member(mod_id)
             mod_name = mod.display_name if mod else "Unknown"
             date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
             embed.add_field(name=date, value=f"**Reason:** {reason}\n**Mod:** {mod_name}", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
