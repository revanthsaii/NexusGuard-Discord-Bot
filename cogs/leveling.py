import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import random
import time

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    def get_user_data(self, user_id, guild_id):
        conn = sqlite3.connect('bot.db')
        cur = conn.cursor()
        cur.execute('SELECT xp, level, last_xp_time FROM reputation WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
        row = cur.fetchone()
        conn.close()
        return row

    def update_xp(self, user_id, guild_id, xp, level, timestamp):
        conn = sqlite3.connect('bot.db')
        conn.execute(
            'INSERT OR REPLACE INTO reputation (user_id, guild_id, xp, level, last_xp_time) VALUES (?, ?, ?, ?, ?)',
            (user_id, guild_id, xp, level, timestamp)
        )
        conn.commit()
        conn.close()

    def get_xp_for_level(self, level):
        return 5 * (level ** 2) + (50 * level) + 100

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        
        # Cooldown check (1 minute)
        now = time.time()
        if user_id in self.cooldowns and now - self.cooldowns[user_id] < 60:
             return
             
        self.cooldowns[user_id] = now
        
        # Fetch current data
        data = self.get_user_data(user_id, guild_id)
        current_xp = 0
        current_level = 1
        
        if data:
            current_xp, current_level, _ = data
            
        # Add random XP
        xp_gain = random.randint(15, 25)
        new_xp = current_xp + xp_gain
        
        # Check level up
        xp_needed = self.get_xp_for_level(current_level)
        new_level = current_level
        
        if new_xp >= xp_needed:
            new_level += 1
            new_xp -= xp_needed # Reset XP for next level or keep accumulating? 
            # Usual discord bot style: Cumulative or Reset? 
            # Let's go with "XP to next level" style where XP resets, or total XP style.
            # Simple implementation: Cumulative XP, but formula calculates total needed.
            # actually, let's stick to "XP resets" for simplicity in bar display, 
            # OR keep total XP and math out the current progress.
            # Let's do: XP is total cumulative. Level is calculated.
            # Wait, my table has `xp` column. Let's make `xp` be TOTAL XP.
            
            # Recalculating approach:
            # XP in DB is TOTAL.
            # Level is stored for convenience/notifications.
            pass
            
        # Actually, simpler path: 
        # XP in DB = Current progress to next level? No that's messy.
        # Let's do: XP in DB = Total accumulated XP.
        # We calculate level based on Total XP? Or store level?
        # Storing level is easier for queries.
        
        # Let's stick to: XP in DB is "Current XP towards next level".
        # When > required, Level++, XP -= required.
        
        if new_xp >= xp_needed:
            new_level += 1
            new_xp -= xp_needed
            await message.channel.send(f"🎉 {message.author.mention} leveled up to **Level {new_level}**!")

        self.update_xp(user_id, guild_id, new_xp, new_level, now)

    @app_commands.command(name="rank", description="Check your rank and level")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = self.get_user_data(target.id, interaction.guild.id)
        
        if not data:
            xp, level = 0, 1
        else:
            xp, level, _ = data
            
        needed = self.get_xp_for_level(level)
        
        embed = discord.Embed(title=f"Rank: {target.display_name}", color=discord.Color.purple())
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp} / {needed}", inline=True)
        
        # Simple Progress Bar
        percent = min(xp / needed, 1.0)
        bars = int(percent * 20)
        progress = "█" * bars + "░" * (20 - bars)
        embed.add_field(name="Progress", value=f"`{progress}`", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="levels", description="View the leaderboard")
    async def levels_lb(self, interaction: discord.Interaction):
        conn = sqlite3.connect('bot.db')
        cur = conn.cursor()
        cur.execute('SELECT user_id, level, xp FROM reputation WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT 10', (interaction.guild.id,))
        rows = cur.fetchall()
        conn.close()
        
        if not rows:
             await interaction.response.send_message("📉 No one has ranked up, yet!")
             return

        embed = discord.Embed(title="🏆 Level Leaderboard", color=discord.Color.gold())
        desc = []
        for idx, (uid, lvl, xp) in enumerate(rows, 1):
            member = interaction.guild.get_member(uid)
            name = member.display_name if member else f"User {uid}"
            desc.append(f"**#{idx}** {name} — Level {lvl} ({xp} XP)")
            
        embed.description = "\n".join(desc)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
