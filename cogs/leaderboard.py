import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

DB_PATH = "bot.db"

class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_db(self):
        return sqlite3.connect(DB_PATH)

    @app_commands.command(name="leaderboard", description="Show the richest users")
    @app_commands.describe(limit="Number of users to show (max 25)")
    async def leaderboard(self, interaction: discord.Interaction, limit: int = 10):
        if limit <= 0: limit = 10
        if limit > 25: limit = 25

        conn = self.get_db()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT user_id, balance
            FROM economy
            WHERE guild_id = ?
            ORDER BY balance DESC
            LIMIT ?
            """,
            (interaction.guild.id, limit),
        )
        rows = cur.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message("📉 No economy data found.", ephemeral=True)
            return

        embed = discord.Embed(title=f"🏆 Top {len(rows)} Richest Members", color=discord.Color.gold())
        embed.set_footer(text="NexusGuard Economy Leaderboard")

        desc = []
        for position, (user_id, balance) in enumerate(rows, start=1):
            member = interaction.guild.get_member(user_id)
            name = member.display_name if member else f"User {user_id}"
            desc.append(f"**#{position}** — {name} • ${balance}")

        embed.description = "\n".join(desc)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leaderboard(bot))
