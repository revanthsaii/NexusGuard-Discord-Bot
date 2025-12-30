import sqlite3
import discord
from discord.ext import commands

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_db(self):
        return sqlite3.connect("bot.db")

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx):
        """Show top 10 richest users in this server."""
        conn = self.get_db()
        c = conn.cursor()
        c.execute(
            """
            SELECT user_id, balance 
            FROM economy 
            WHERE guild_id = ?
            ORDER BY balance DESC 
            LIMIT 10
            """,
            (ctx.guild.id,),
        )
        rows = c.fetchall()
        conn.close()

        if not rows:
            await ctx.send("No data yet. Use `!work` to start earning money!")
            return

        embed = discord.Embed(
            title=f"🏆 Top 10 Richest in {ctx.guild.name}",
            colour=discord.Colour.gold(),
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        for idx, (user_id, balance) in enumerate(rows, start=1):
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else f"User `{user_id}`"
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
            embed.add_field(
                name=f"{medal} {name}",
                value=f"Balance: **${balance}**",
                inline=False,
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
