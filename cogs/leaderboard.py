import sqlite3
import discord
from discord.ext import commands


DB_PATH = "bot.db"


class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_db(self):
        return sqlite3.connect(DB_PATH)

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx: commands.Context, limit: int = 10):
        """
        Show the richest users in this server.
        Usage: !leaderboard or !leaderboard 5
        """
        if limit <= 0:
            limit = 10
        if limit > 25:
            limit = 25  # hard cap to keep embed readable

        conn = self.get_db()
        cur = conn.cursor()
        # Top balances for this guild. [web:250][web:253]
        cur.execute(
            """
            SELECT user_id, balance
            FROM economy
            WHERE guild_id = ?
            ORDER BY balance DESC
            LIMIT ?
            """,
            (ctx.guild.id, limit),
        )
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return await ctx.send("📉 No economy data found for this server yet.")

        embed = discord.Embed(
            title=f"🏆 Top {len(rows)} Richest Members",
            color=discord.Color.gold(),
        )
        embed.set_footer(text="NexusGuard Economy Leaderboard")

        description_lines = []
        for position, (user_id, balance) in enumerate(rows, start=1):
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else f"User ID {user_id}"
            description_lines.append(
                f"**#{position}** — {name} • ${balance}"
            )

        embed.description = "\n".join(description_lines)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Leaderboard(bot))
