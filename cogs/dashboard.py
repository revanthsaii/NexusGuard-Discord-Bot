import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_db_stats(self, guild_id):
        conn = sqlite3.connect('bot.db')
        cur = conn.cursor()
        
        # Count Mod Logs (actions taken)
        cur.execute("SELECT count(*) FROM mod_logs WHERE guild_id = ?", (guild_id,))
        mod_actions = cur.fetchone()[0]
        
        # Count Warns
        cur.execute("SELECT count(*) FROM warnings WHERE guild_id = ?", (guild_id,))
        warnings = cur.fetchone()[0]
        
        # Total XP in server
        cur.execute("SELECT sum(xp) FROM reputation WHERE guild_id = ?", (guild_id,))
        row = cur.fetchone()
        total_xp = row[0] if row and row[0] else 0
        
        conn.close()
        return mod_actions, warnings, total_xp

    @app_commands.command(name="server", description="View server health and stats")
    @app_commands.describe(subcommand="Choose 'health' or 'stats'") 
    # Note: Proper subcommands are better, but simple arg for now fits the singular request
    @app_commands.choices(subcommand=[
        app_commands.Choice(name="health", value="health"),
        app_commands.Choice(name="trends", value="trends")
    ])
    async def server_cmd(self, interaction: discord.Interaction, subcommand: str):
        if subcommand == "health":
            await self.show_health(interaction)
        else:
            await self.show_trends(interaction)

    async def show_health(self, interaction: discord.Interaction):
        mod_actions, warnings, total_xp = self.get_db_stats(interaction.guild_id)
        member_count = interaction.guild.member_count
        
        # --- Score Calculation Logic ---
        # Safety Score: Starts at 100. Decreases with warnings/mod actions (relative to member count)
        # 1 mod action per 10 members = -10 points? 
        # Let's keep it simple.
        safety_deduction = (mod_actions + warnings) * 2
        safety_score = max(0, min(100, 100 - safety_deduction))
        
        safety_emoji = "🟢" if safety_score > 80 else "🟡" if safety_score > 50 else "🔴"
        
        # Activity Score: Based on Avg XP per user
        avg_xp = total_xp / member_count if member_count > 0 else 0
        # Arbitrary scale: 1000 XP avg = 100 score
        activity_score = min(100, int(avg_xp / 10))
        
        activity_emoji = "🔥" if activity_score > 80 else "😐" if activity_score > 40 else "🧊"
        
        embed = discord.Embed(title=f"📊 Server Health: {interaction.guild.name}", color=discord.Color.teal())
        
        embed.add_field(
            name=f"{safety_emoji} Safety Score: {safety_score}/100", 
            value=f"Violations: {mod_actions + warnings}", 
            inline=True
        )
        embed.add_field(
            name=f"{activity_emoji} Activity Score: {activity_score}/100", 
            value=f"Total XP: {total_xp:,}", 
            inline=True
        )
        embed.add_field(
            name="👥 Member Growth",
            value=f"Total Members: **{member_count}**",
            inline=False
        )
        
        if safety_score < 50:
            embed.set_footer(text="⚠️ Safety is low! Check /warnings and consider automod.")
        elif activity_score < 30:
            embed.set_footer(text="💡 Tip: Create some Quests or Events to boost activity!")
        else:
            embed.set_footer(text="✅ Server is looking healthy!")
            
        await interaction.response.send_message(embed=embed)

    async def show_trends(self, interaction: discord.Interaction):
        # Placeholder for trends since we don't have historical data tables
        embed = discord.Embed(title="📈 Server Trends", description="Feature coming soon with historical data tracking!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Dashboard(bot))
