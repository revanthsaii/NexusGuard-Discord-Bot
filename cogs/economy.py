import sqlite3
import random
import discord
from discord import app_commands
from discord.ext import commands

DB_PATH = "bot.db"
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
        conn = self.get_db()
        cur = conn.cursor()
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

    def get_balance(self, user_id: int, guild_id: int) -> int:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT balance FROM economy WHERE user_id=? AND guild_id=?",(user_id, guild_id))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0

    def change_balance(self, user_id: int, guild_id: int, amount: int) -> int:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT balance FROM economy WHERE user_id=? AND guild_id=?",(user_id, guild_id))
        row = cur.fetchone()
        current = row[0] if row else 0
        new_balance = current + amount

        if row:
            cur.execute("UPDATE economy SET balance=? WHERE user_id=? AND guild_id=?",(new_balance, user_id, guild_id))
        else:
            cur.execute("INSERT INTO economy (user_id, guild_id, balance) VALUES (?, ?, ?)",(user_id, guild_id, new_balance))
        conn.commit()
        conn.close()
        return new_balance

    def get_inventory(self, user_id: int, guild_id: int) -> list[tuple[str, int]]:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT item_name, quantity FROM inventory WHERE user_id=? AND guild_id=? AND quantity > 0",(user_id, guild_id))
        rows = cur.fetchall()
        conn.close()
        return rows

    def change_item(self, user_id: int, guild_id: int, item_name: str, delta_qty: int) -> int:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE user_id=? AND guild_id=? AND item_name=?",(user_id, guild_id, item_name))
        row = cur.fetchone()
        current = row[0] if row else 0
        new_qty = current + delta_qty

        if row:
            cur.execute("UPDATE inventory SET quantity = ? WHERE user_id=? AND guild_id=? AND item_name=?", (new_qty, user_id, guild_id, item_name))
        else:
            cur.execute("INSERT INTO inventory (user_id, guild_id, item_name, quantity) VALUES (?, ?, ?, ?)", (user_id, guild_id, item_name, max(new_qty, 0)))
        conn.commit()
        conn.close()
        return new_qty

    # --- Slash Commands ---
    
    # ---------- Jobs & Quests ----------
    
    @app_commands.command(name="jobs", description="List available jobs")
    async def jobs_cmd(self, interaction: discord.Interaction):
        conn = self.get_db()
        cur = conn.execute("SELECT name, min_pay, max_pay, required_level FROM jobs ORDER BY required_level ASC")
        jobs = cur.fetchall()
        
        # Get user level
        cur.execute("SELECT level FROM reputation WHERE user_id = ? AND guild_id = ?", (interaction.user.id, interaction.guild.id))
        row = cur.fetchone()
        user_level = row[0] if row else 1
        
        conn.close()
        
        embed = discord.Embed(title="🏢 Available Jobs", color=discord.Color.blue())
        for name, min_p, max_p, req_lvl in jobs:
            status = "✅ Unlocked" if user_level >= req_lvl else f"🔒 Locked (Lvl {req_lvl})"
            embed.add_field(
                name=f"{name} ({status})", 
                value=f"Pay: ${min_p} - ${max_p}", 
                inline=False
            )
        embed.set_footer(text="Use /work to work your highest unlocked job automatically!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Work at your job")
    async def work(self, interaction: discord.Interaction):
        # 1. Get user level
        conn = self.get_db()
        cur = conn.execute("SELECT level FROM reputation WHERE user_id = ? AND guild_id = ?", (interaction.user.id, interaction.guild.id))
        row = cur.fetchone()
        user_level = row[0] if row else 1
        
        # 2. Get best unlocked job
        cur.execute("SELECT name, min_pay, max_pay FROM jobs WHERE required_level <= ? ORDER BY required_level DESC LIMIT 1", (user_level,))
        job = cur.fetchone()
        conn.close()
        
        if not job:
            job_name, min_p, max_p = "Beggar", 10, 20 # Fallback
        else:
            job_name, min_p, max_p = job
            
        earnings = random.randint(min_p, max_p)
        new_balance = self.change_balance(interaction.user.id, interaction.guild.id, earnings)
        
        await interaction.response.send_message(f"💼 Worked as a **{job_name}** and earned **${earnings}**! New balance: **${new_balance}**.")

    @app_commands.command(name="quests", description="View active quests")
    async def quests(self, interaction: discord.Interaction):
        # Simple placeholder quests for now
        quests = [
            ("Daily Grinder", "Send 50 messages", "0/50", "$100"),
            ("Gambler", "Win 3 coinflips", "1/3", "$250"),
        ]
        
        embed = discord.Embed(title="📜 Active Quests", color=discord.Color.green())
        for name, desc, prog, reward in quests:
            embed.add_field(name=name, value=f"{desc}\nProgress: {prog}\nReward: **{reward}**", inline=False)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim daily reward")
    async def daily(self, interaction: discord.Interaction):
        reward = random.randint(150, 300)
        # Note: Proper daily cooldown logic requires DB timestamp tracking to be robust across restarts
        # For this implementation, we proceed without persistent cooldowns for simplicity, as per previous code style
        new_balance = self.change_balance(interaction.user.id, interaction.guild.id, reward)
        await interaction.response.send_message(f"📅 Daily reward claimed: **${reward}**! New balance: **${new_balance}**.")

    @app_commands.command(name="pay", description="Pay another user")
    @app_commands.describe(user="User to pay", amount="Amount to pay")
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if user.bot:
             await interaction.response.send_message("🤖 You cannot pay bots.", ephemeral=True)
             return
        if user.id == interaction.user.id:
             await interaction.response.send_message("🪞 You cannot pay yourself.", ephemeral=True)
             return
        if amount <= 0:
             await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
             return

        sender_balance = self.get_balance(interaction.user.id, interaction.guild.id)
        if amount > sender_balance:
             await interaction.response.send_message("💸 Insufficient funds.", ephemeral=True)
             return

        self.change_balance(interaction.user.id, interaction.guild.id, -amount)
        new_bal = self.change_balance(user.id, interaction.guild.id, amount)
        await interaction.response.send_message(f"✅ Paid **${amount}** to {user.mention}. Their new balance: **${new_bal}**.")

    @app_commands.command(name="shop", description="View shop items")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🛒 NexusGuard Shop", description="Use `/buy <item> [qty]`", color=discord.Color.gold())
        for item, price in SHOP_ITEMS.items():
            embed.add_field(name=item, value=f"Price: ${price}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Buy an item")
    @app_commands.describe(item="Item name", quantity="Quantity to buy")
    async def buy(self, interaction: discord.Interaction, item: str, quantity: int = 1):
        item = item.lower()
        if item not in SHOP_ITEMS:
            await interaction.response.send_message("❌ Item not found.", ephemeral=True)
            return
        if quantity <= 0:
             await interaction.response.send_message("❌ Quantity must be positive.", ephemeral=True)
             return

        price = SHOP_ITEMS[item]
        cost = price * quantity
        bal = self.get_balance(interaction.user.id, interaction.guild.id)
        
        if cost > bal:
            await interaction.response.send_message(f"💸 You need **${cost}** but have **${bal}**.", ephemeral=True)
            return

        self.change_balance(interaction.user.id, interaction.guild.id, -cost)
        new_qty = self.change_item(interaction.user.id, interaction.guild.id, item, quantity)
        await interaction.response.send_message(f"✅ Bought **{quantity}x {item}** for **${cost}**. You now have {new_qty}.")

    @app_commands.command(name="inventory", description="View your inventory")
    @app_commands.describe(user="User to view")
    async def inventory(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        items = self.get_inventory(target.id, interaction.guild.id)
        if not items:
            await interaction.response.send_message(f"📦 {target.display_name}'s inventory is empty.")
            return

        embed = discord.Embed(title=f"🎒 {target.display_name}'s Inventory", color=discord.Color.blurple())
        for item, qty in items:
            embed.add_field(name=item, value=f"Qty: {qty}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roulette", description="Gamble money")
    @app_commands.describe(amount="Amount to bet")
    async def roulette(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
             await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
             return
             
        bal = self.get_balance(interaction.user.id, interaction.guild.id)
        if amount > bal:
             await interaction.response.send_message(f"💸 You don't have enough money ({bal}).", ephemeral=True)
             return

        win = random.choice([True, False])
        if win:
            self.change_balance(interaction.user.id, interaction.guild.id, amount)
            await interaction.response.send_message(f"🎉 You won **${amount}**!")
        else:
            self.change_balance(interaction.user.id, interaction.guild.id, -amount)
            await interaction.response.send_message(f"💀 You lost **${amount}**...")

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
