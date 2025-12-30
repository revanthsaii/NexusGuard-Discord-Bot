import sqlite3
import random
import discord
from discord.ext import commands


DB_PATH = "bot.db"

# Simple static shop definition (you can tweak prices or add items).
SHOP_ITEMS = {
    "lucky-charm": 500,
    "vip-pass": 1500,
    "lottery-ticket": 250,
}


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ensure_tables()

    def get_db(self):
        return sqlite3.connect(DB_PATH)

    def _ensure_tables(self):
        """Create inventory table if it does not exist."""
        conn = self.get_db()
        cur = conn.cursor()

        # Inventory: one row per item a user owns in a guild. [web:359]
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                guild_id INTEGER,
                item_name TEXT,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id, item_name)
            )
            """
        )

        conn.commit()
        conn.close()

    # ---------- Core balance helpers ----------

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

        cur.execute(
            "SELECT balance FROM economy WHERE user_id=? AND guild_id=?",
            (user_id, guild_id),
        )
        row = cur.fetchone()
        current = row[0] if row else 0
        new_balance = current + amount

        if row:
            cur.execute(
                "UPDATE economy SET balance=? WHERE user_id=? AND guild_id=?",
                (new_balance, user_id, guild_id),
            )
        else:
            cur.execute(
                "INSERT INTO economy (user_id, guild_id, balance) VALUES (?, ?, ?)",
                (user_id, guild_id, new_balance),
            )

        conn.commit()
        conn.close()
        return new_balance

    # ---------- Inventory helpers ----------

    def get_inventory(self, user_id: int, guild_id: int) -> list[tuple[str, int]]:
        """Return list of (item_name, quantity) for a user."""
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT item_name, quantity
            FROM inventory
            WHERE user_id=? AND guild_id=? AND quantity > 0
            """,
            (user_id, guild_id),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def change_item(
        self, user_id: int, guild_id: int, item_name: str, delta_qty: int
    ) -> int:
        """Increase quantity of an item and return new quantity."""
        conn = self.get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT quantity
            FROM inventory
            WHERE user_id=? AND guild_id=? AND item_name=?
            """,
            (user_id, guild_id, item_name),
        )
        row = cur.fetchone()
        current = row[0] if row else 0
        new_qty = current + delta_qty

        if row:
            cur.execute(
                """
                UPDATE inventory
                SET quantity = ?
                WHERE user_id=? AND guild_id=? AND item_name=?
                """,
                (new_qty, user_id, guild_id, item_name),
            )
        else:
            cur.execute(
                """
                INSERT INTO inventory (user_id, guild_id, item_name, quantity)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, guild_id, item_name, max(new_qty, 0)),
            )

        conn.commit()
        conn.close()
        return new_qty

    # ---------- Basic economy commands ----------

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

        self.change_balance(ctx.author.id, ctx.guild.id, -amount)
        receiver_new_balance = self.change_balance(member.id, ctx.guild.id, amount)

        await ctx.send(
            f"✅ {ctx.author.mention} paid **${amount}** to {member.mention}.\n"
            f"{member.display_name}'s new balance: **${receiver_new_balance}**."
        )

    # ---------- Shop & inventory ----------

    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context):
        """View the shop items and prices."""
        embed = discord.Embed(
            title="🛒 NexusGuard Shop",
            description="Use `!buy <item> [quantity]` to purchase.\n"
                        "Example: `!buy lucky-charm 2`",
            color=discord.Color.gold(),
        )
        for item, price in SHOP_ITEMS.items():
            embed.add_field(
                name=item,
                value=f"Price: ${price}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        """Buy an item from the shop."""
        item_name = item_name.lower()
        if item_name not in SHOP_ITEMS:
            return await ctx.send(
                "❌ That item does not exist. Use `!shop` to see available items."
            )

        if quantity <= 0:
            return await ctx.send("❌ Quantity must be a positive number.")

        price = SHOP_ITEMS[item_name]
        total_cost = price * quantity

        balance = self.get_balance(ctx.author.id, ctx.guild.id)
        if total_cost > balance:
            return await ctx.send(
                f"💸 You need **${total_cost}**, but you only have **${balance}**."
            )

        # Deduct and add to inventory. [web:359]
        self.change_balance(ctx.author.id, ctx.guild.id, -total_cost)
        new_qty = self.change_item(
            ctx.author.id, ctx.guild.id, item_name, quantity
        )

        await ctx.send(
            f"✅ {ctx.author.mention} bought **{quantity}× {item_name}** "
            f"for **${total_cost}**. You now own **{new_qty}× {item_name}**."
        )

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx: commands.Context):
        """View your inventory."""
        items = self.get_inventory(ctx.author.id, ctx.guild.id)
        if not items:
            return await ctx.send("📦 Your inventory is empty.")

        embed = discord.Embed(
            title=f"🎒 {ctx.author.display_name}'s Inventory",
            color=discord.Color.blurple(),
        )

        for item_name, qty in items:
            embed.add_field(
                name=item_name,
                value=f"Quantity: {qty}",
                inline=False,
            )

        await ctx.send(embed=embed)

    # ---------- Roulette / gamble ----------

    @commands.command(name="roulette")
    async def roulette(self, ctx: commands.Context, amount: int):
        """
        Gamble some of your money.
        50% chance to double, 50% chance to lose.
        """
        if amount <= 0:
            return await ctx.send("❌ Bet amount must be positive.")

        balance = self.get_balance(ctx.author.id, ctx.guild.id)
        if amount > balance:
            return await ctx.send(
                f"💸 You tried to bet **${amount}**, but you only have **${balance}**."
            )

        # Basic 50/50 gamble. [web:358][web:366]
        win = random.choice([True, False])

        if win:
            winnings = amount
            new_balance = self.change_balance(
                ctx.author.id, ctx.guild.id, winnings
            )
            await ctx.send(
                f"🎉 {ctx.author.mention} won **${winnings}** in roulette!\n"
                f"New balance: **${new_balance}**."
            )
        else:
            loss = -amount
            new_balance = self.change_balance(
                ctx.author.id, ctx.guild.id, loss
            )
            await ctx.send(
                f"💀 {ctx.author.mention} lost **${amount}** in roulette...\n"
                f"New balance: **${new_balance}**."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
