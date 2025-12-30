import sqlite3
import random
import discord
from discord.ext import commands

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_db(self):
        return sqlite3.connect("bot.db")

    @commands.command(name="balance")
    async def balance(self, ctx):
        """Check your balance."""
        conn = self.get_db()
        c = conn.cursor()
        c.execute(
            "SELECT balance FROM economy WHERE user_id=? AND guild_id=?",
            (ctx.author.id, ctx.guild.id),
        )
        result = c.fetchone()
        balance = result[0] if result else 0
        conn.close()

        embed = discord.Embed(title="💰 Balance", color=0x00FF00)
        embed.add_field(name=ctx.author.display_name, value=f"${balance}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="work")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx):
        """Work to earn some money."""
        earnings = random.randint(50, 150)
        conn = self.get_db()
        c = conn.cursor()
        c.execute(
            """INSERT OR REPLACE INTO economy (user_id, guild_id, balance) 
               VALUES (
                 ?, ?, 
                 COALESCE((SELECT balance FROM economy WHERE user_id=? AND guild_id=?), 0) + ?
               )""",
            (ctx.author.id, ctx.guild.id, ctx.author.id, ctx.guild.id, earnings),
        )
        conn.commit()
        conn.close()
        await ctx.send(f"💼 {ctx.author.mention} worked hard and earned **${earnings}**!")

async def setup(bot):
    await bot.add_cog(Economy(bot))
