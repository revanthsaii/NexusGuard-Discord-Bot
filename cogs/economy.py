import sqlite3
import random
import discord
from discord.ext import commands


DB_PATH = "bot.db"


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_db(self):
        return sqlite3.connect(DB_PATH)

    def get_balance(self, user_id: int, guild_id: int) -> int:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT balance FROM economy WHERE user_id=? AND guild_id=?",
            (user_id, guild_id),
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0

    def change_balance(self, user_id: int, guild_id: int, amount: int) -> int:
        """Increase balance by amount (can be negative) and return new balance."""
        conn = self.get_db()
        cur = conn.cursor()

        # Get current balance
        cur.execute(
            "SELECT balance FROM economy WHERE user_id=? AND guild_id=?",
            (user_id, guild_id),
        )
        row = cur.fetchone()
        current = row[0] if row else 0
        new_balance = current + amount

        if row:
            # Update existing row
            cur.execute(
                "UPDATE economy SET balance=? WHERE user_id=? AND guild_id=?",
                (new_balance, user_id, guild_id),
            )
        else:
            # Insert new row
            cur.execute(
                "INSERT INTO economy (user_id, guild_id, balance) VALUES (?, ?, ?)",
                (user_id, guild_id, new_balance),
            )

        conn.commit()
        conn.close()
        return new_balance

    @commands.command(name="balance")
    async def balance(self, ctx: commands.Context):
        """Check your balance."""
        balance = self.get_balance(ctx.author.id, ctx.guild.id)

        embed = discord.Embed(title="💰 Balance", color=0x00FF00)
        embed.add_field(
            name=ctx.author.display_name,
            value=f"${balance}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="work")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        """Work to earn some money."""
        earnings = random.randint(50, 150)
        new_balance = self.change_balance(ctx.author.id, ctx.guild.id, earnings)
        await ctx.send(
            f"💼 {ctx.author.mention} worked hard and earned **${earnings}**! "
            f"New balance: **${new_balance}**."
        )

    @work.error
    async def work_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            remaining = int(error.retry_after // 60) or 1
            await ctx.send(
                f"⏳ You are tired, {ctx.author.mention}! "
                f"Try again in about **{remaining} minutes**."
            )

    @commands.command(name="daily")
    @commands.cooldown(1, 24 * 3600, commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        """Claim your daily reward."""
        reward = random.randint(150, 300)
        new_balance = self.change_balance(ctx.author.id, ctx.guild.id, reward)
        await ctx.send(
            f"📅 {ctx.author.mention} claimed a daily reward of **${reward}**!\n"
            f"New balance: **${new_balance}**."
        )

    @daily.error
    async def daily_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            hours = int(error.retry_after // 3600) or 1
            await ctx.send(
                f"⏳ You already claimed your daily, {ctx.author.mention}. "
                f"Try again in about **{hours} hour(s)**."
            )

    @commands.command(name="pay")
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Pay another user some of your balance."""
        if member.bot:
            return await ctx.send("🤖 You cannot pay bots.")

        if member.id == ctx.author.id:
            return await ctx.send("🪞 You cannot pay yourself.")

        if amount <= 0:
            return await ctx.send("❌ Amount must be a positive number.")

        sender_balance = self.get_balance(ctx.author.id, ctx.guild.id)
        if amount > sender_balance:
            return await ctx.send("💸 You don't have enough money for that payment.")

        # Subtract from sender, add to receiver
        self.change_balance(ctx.author.id, ctx.guild.id, -amount)
        receiver_new_balance = self.change_balance(member.id, ctx.guild.id, amount)

        await ctx.send(
            f"✅ {ctx.author.mention} paid **${amount}** to {member.mention}.\n"
            f"{member.display_name}'s new balance: **${receiver_new_balance}**."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
