import sqlite3
import random
import discord
from discord import app_commands
from discord.ext import commands
import time

DB_PATH = "bot.db"
SHOP_ITEMS = {
    "lucky-charm": 500,
    "vip-pass": 1500,
    "lottery-ticket": 250,
    "padlock": 1000,
    "bank-note": 5000,
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

    # --- Core Balance Methods ---
    
    def get_balance(self, user_id: int, guild_id: int) -> int:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT balance FROM economy WHERE user_id=? AND guild_id=?",(user_id, guild_id))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0

    def get_bank(self, user_id: int, guild_id: int) -> int:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT bank FROM economy WHERE user_id=? AND guild_id=?",(user_id, guild_id))
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
            cur.execute("INSERT INTO economy (user_id, guild_id, balance, bank, daily_streak) VALUES (?, ?, ?, 0, 0)",(user_id, guild_id, new_balance))
        conn.commit()
        conn.close()
        return new_balance

    def change_bank(self, user_id: int, guild_id: int, amount: int) -> int:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT bank FROM economy WHERE user_id=? AND guild_id=?",(user_id, guild_id))
        row = cur.fetchone()
        current = row[0] if row else 0
        new_bank = current + amount

        if row:
            cur.execute("UPDATE economy SET bank=? WHERE user_id=? AND guild_id=?",(new_bank, user_id, guild_id))
        else:
            cur.execute("INSERT INTO economy (user_id, guild_id, balance, bank, daily_streak) VALUES (?, ?, 0, ?, 0)",(user_id, guild_id, new_bank))
        conn.commit()
        conn.close()
        return new_bank

    # --- Cooldown Methods ---
    
    def get_cooldown(self, user_id: int, guild_id: int, command: str) -> float:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT last_used FROM cooldowns WHERE user_id=? AND guild_id=? AND command=?",(user_id, guild_id, command))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0

    def set_cooldown(self, user_id: int, guild_id: int, command: str):
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO cooldowns (user_id, guild_id, command, last_used) VALUES (?, ?, ?, ?)",
                    (user_id, guild_id, command, time.time()))
        conn.commit()
        conn.close()

    def check_cooldown(self, user_id: int, guild_id: int, command: str, cooldown_seconds: int) -> tuple[bool, int]:
        last_used = self.get_cooldown(user_id, guild_id, command)
        elapsed = time.time() - last_used
        if elapsed < cooldown_seconds:
            remaining = int(cooldown_seconds - elapsed)
            return False, remaining
        return True, 0

    # --- Inventory Methods ---
    
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

    def has_item(self, user_id: int, guild_id: int, item_name: str) -> bool:
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE user_id=? AND guild_id=? AND item_name=?",(user_id, guild_id, item_name))
        row = cur.fetchone()
        conn.close()
        return row[0] > 0 if row else False

    # --- Slash Commands ---
    
    @app_commands.command(name="balance", description="Check your wallet and bank balance")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        wallet = self.get_balance(target.id, interaction.guild.id)
        bank = self.get_bank(target.id, interaction.guild.id)
        total = wallet + bank
        
        embed = discord.Embed(title=f"💰 {target.display_name}'s Balance", color=discord.Color.gold())
        embed.add_field(name="👛 Wallet", value=f"${wallet:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"${bank:,}", inline=True)
        embed.add_field(name="📊 Total", value=f"${total:,}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deposit", description="Deposit money to your bank")
    async def deposit(self, interaction: discord.Interaction, amount: str):
        wallet = self.get_balance(interaction.user.id, interaction.guild.id)
        
        if amount.lower() == "all":
            amount = wallet
        else:
            try:
                amount = int(amount)
            except:
                await interaction.response.send_message("❌ Invalid amount.", ephemeral=True)
                return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        if amount > wallet:
            await interaction.response.send_message(f"❌ You only have ${wallet:,} in your wallet.", ephemeral=True)
            return
        
        self.change_balance(interaction.user.id, interaction.guild.id, -amount)
        new_bank = self.change_bank(interaction.user.id, interaction.guild.id, amount)
        await interaction.response.send_message(f"🏦 Deposited **${amount:,}**! Bank balance: **${new_bank:,}**")

    @app_commands.command(name="withdraw", description="Withdraw money from your bank")
    async def withdraw(self, interaction: discord.Interaction, amount: str):
        bank = self.get_bank(interaction.user.id, interaction.guild.id)
        
        if amount.lower() == "all":
            amount = bank
        else:
            try:
                amount = int(amount)
            except:
                await interaction.response.send_message("❌ Invalid amount.", ephemeral=True)
                return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        if amount > bank:
            await interaction.response.send_message(f"❌ You only have ${bank:,} in your bank.", ephemeral=True)
            return
        
        self.change_bank(interaction.user.id, interaction.guild.id, -amount)
        new_wallet = self.change_balance(interaction.user.id, interaction.guild.id, amount)
        await interaction.response.send_message(f"💸 Withdrew **${amount:,}**! Wallet balance: **${new_wallet:,}**")

    # --- Crime System ---
    
    @app_commands.command(name="rob", description="Attempt to rob another user")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        if user.bot or user.id == interaction.user.id:
            await interaction.response.send_message("❌ Invalid target.", ephemeral=True)
            return
        
        # Check cooldown (30 minutes)
        can_use, remaining = self.check_cooldown(interaction.user.id, interaction.guild.id, "rob", 1800)
        if not can_use:
            await interaction.response.send_message(f"⏰ You can rob again in **{remaining // 60}m {remaining % 60}s**.", ephemeral=True)
            return
        
        # Check if target has padlock
        if self.has_item(user.id, interaction.guild.id, "padlock"):
            self.change_item(user.id, interaction.guild.id, "padlock", -1)
            await interaction.response.send_message(f"🔒 {user.mention}'s padlock protected them! The padlock broke.")
            self.set_cooldown(interaction.user.id, interaction.guild.id, "rob")
            return
        
        target_wallet = self.get_balance(user.id, interaction.guild.id)
        if target_wallet < 100:
            await interaction.response.send_message(f"❌ {user.display_name} doesn't have enough money to rob.", ephemeral=True)
            return
        
        # 40% success rate
        if random.random() < 0.4:
            stolen = random.randint(min(100, target_wallet), min(target_wallet, 500))
            self.change_balance(user.id, interaction.guild.id, -stolen)
            self.change_balance(interaction.user.id, interaction.guild.id, stolen)
            await interaction.response.send_message(f"💰 You robbed **${stolen:,}** from {user.mention}!")
        else:
            fine = random.randint(100, 300)
            self.change_balance(interaction.user.id, interaction.guild.id, -fine)
            await interaction.response.send_message(f"🚔 You got caught! Paid **${fine:,}** in fines.")
        
        self.set_cooldown(interaction.user.id, interaction.guild.id, "rob")

    @app_commands.command(name="crime", description="Commit a random crime")
    async def crime(self, interaction: discord.Interaction):
        # Check cooldown (45 seconds)
        can_use, remaining = self.check_cooldown(interaction.user.id, interaction.guild.id, "crime", 45)
        if not can_use:
            await interaction.response.send_message(f"⏰ You can commit crime again in **{remaining}s**.", ephemeral=True)
            return
        
        crimes = [
            ("🏪 robbed a convenience store", 200, 600, 0.5),
            ("💻 hacked a bank database", 500, 1500, 0.3),
            ("🚗 stole a car", 300, 800, 0.4),
            ("💎 pickpocketed a tourist", 100, 400, 0.6),
        ]
        
        crime_name, min_r, max_r, success_rate = random.choice(crimes)
        
        if random.random() < success_rate:
            earnings = random.randint(min_r, max_r)
            self.change_balance(interaction.user.id, interaction.guild.id, earnings)
            await interaction.response.send_message(f"✅ You {crime_name} and got **${earnings:,}**!")
        else:
            fine = random.randint(100, 500)
            self.change_balance(interaction.user.id, interaction.guild.id, -fine)
            await interaction.response.send_message(f"🚔 You failed and paid **${fine:,}** in fines.")
        
        self.set_cooldown(interaction.user.id, interaction.guild.id, "crime")

    # --- Jobs & Work ---
    
    @app_commands.command(name="jobs", description="List available jobs")
    async def jobs_cmd(self, interaction: discord.Interaction):
        conn = self.get_db()
        cur = conn.execute("SELECT name, min_pay, max_pay, required_level FROM jobs ORDER BY required_level ASC")
        jobs = cur.fetchall()
        
        cur.execute("SELECT level FROM reputation WHERE user_id = ? AND guild_id = ?", (interaction.user.id, interaction.guild.id))
        row = cur.fetchone()
        user_level = row[0] if row else 1
        conn.close()
        
        embed = discord.Embed(title="🏢 Available Jobs", color=discord.Color.blue())
        for name, min_p, max_p, req_lvl in jobs:
            status = "✅" if user_level >= req_lvl else f"🔒 Lvl {req_lvl}"
            embed.add_field(name=f"{status} {name}", value=f"${min_p:,} - ${max_p:,}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Work at your job")
    async def work(self, interaction: discord.Interaction):
        # Check cooldown (30 seconds)
        can_use, remaining = self.check_cooldown(interaction.user.id, interaction.guild.id, "work", 30)
        if not can_use:
            await interaction.response.send_message(f"⏰ You can work again in **{remaining}s**.", ephemeral=True)
            return
        
        conn = self.get_db()
        cur = conn.execute("SELECT level FROM reputation WHERE user_id = ? AND guild_id = ?", (interaction.user.id, interaction.guild.id))
        row = cur.fetchone()
        user_level = row[0] if row else 1
        
        cur.execute("SELECT name, min_pay, max_pay FROM jobs WHERE required_level <= ? ORDER BY required_level DESC LIMIT 1", (user_level,))
        job = cur.fetchone()
        conn.close()
        
        if not job:
            job_name, min_p, max_p = "Beggar", 10, 20
        else:
            job_name, min_p, max_p = job
            
        earnings = random.randint(min_p, max_p)
        new_balance = self.change_balance(interaction.user.id, interaction.guild.id, earnings)
        
        await interaction.response.send_message(f"💼 Worked as a **{job_name}** and earned **${earnings:,}**!")
        self.set_cooldown(interaction.user.id, interaction.guild.id, "work")

    @app_commands.command(name="daily", description="Claim daily reward")
    async def daily(self, interaction: discord.Interaction):
        # Check cooldown (24 hours)
        can_use, remaining = self.check_cooldown(interaction.user.id, interaction.guild.id, "daily", 86400)
        if not can_use:
            hours = remaining // 3600
            mins = (remaining % 3600) // 60
            await interaction.response.send_message(f"⏰ You can claim daily again in **{hours}h {mins}m**.", ephemeral=True)
            return
        
        base_reward = random.randint(200, 500)
        
        # Streak bonus (simplified - just give bonus)
        streak_bonus = random.randint(50, 150)
        total_reward = base_reward + streak_bonus
        
        # Also give 2% interest on bank
        bank = self.get_bank(interaction.user.id, interaction.guild.id)
        interest = int(bank * 0.02)
        if interest > 0:
            self.change_bank(interaction.user.id, interaction.guild.id, interest)
        
        new_balance = self.change_balance(interaction.user.id, interaction.guild.id, total_reward)
        
        msg = f"📅 **Daily Claimed!**\n💵 Reward: **${base_reward:,}**\n🔥 Streak Bonus: **${streak_bonus:,}**"
        if interest > 0:
            msg += f"\n🏦 Bank Interest (2%): **${interest:,}**"
        
        await interaction.response.send_message(msg)
        self.set_cooldown(interaction.user.id, interaction.guild.id, "daily")

    # --- Gambling ---
    
    @app_commands.command(name="coinflip", description="Bet on heads or tails")
    @app_commands.describe(bet="Amount to bet", choice="heads or tails")
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: str):
        choice = choice.lower()
        if choice not in ["heads", "tails"]:
            await interaction.response.send_message("❌ Choose 'heads' or 'tails'.", ephemeral=True)
            return
        
        if bet <= 0:
            await interaction.response.send_message("❌ Bet must be positive.", ephemeral=True)
            return
        
        wallet = self.get_balance(interaction.user.id, interaction.guild.id)
        if bet > wallet:
            await interaction.response.send_message(f"❌ You only have ${wallet:,}.", ephemeral=True)
            return
        
        result = random.choice(["heads", "tails"])
        
        if result == choice:
            self.change_balance(interaction.user.id, interaction.guild.id, bet)
            await interaction.response.send_message(f"🪙 **{result.upper()}**! You won **${bet:,}**! 🎉")
        else:
            self.change_balance(interaction.user.id, interaction.guild.id, -bet)
            await interaction.response.send_message(f"🪙 **{result.upper()}**! You lost **${bet:,}**. 😢")

    @app_commands.command(name="slots", description="Play the slot machine")
    @app_commands.describe(bet="Amount to bet")
    async def slots(self, interaction: discord.Interaction, bet: int):
        if bet <= 0 or bet > 10000:
            await interaction.response.send_message("❌ Bet must be between $1 and $10,000.", ephemeral=True)
            return
        
        wallet = self.get_balance(interaction.user.id, interaction.guild.id)
        if bet > wallet:
            await interaction.response.send_message(f"❌ You only have ${wallet:,}.", ephemeral=True)
            return
        
        symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣", "🍀"]
        result = [random.choice(symbols) for _ in range(3)]
        
        self.change_balance(interaction.user.id, interaction.guild.id, -bet)
        
        # Check wins
        if result[0] == result[1] == result[2]:
            if result[0] == "7️⃣":
                multiplier = 10
                msg = "🎰 **JACKPOT!!!** 🎰"
            elif result[0] == "💎":
                multiplier = 5
                msg = "💎 **BIG WIN!** 💎"
            else:
                multiplier = 3
                msg = "🎉 **You won!** 🎉"
            
            winnings = bet * multiplier
            self.change_balance(interaction.user.id, interaction.guild.id, winnings)
            await interaction.response.send_message(f"[ {' | '.join(result)} ]\n{msg}\nYou won **${winnings:,}**!")
        elif result[0] == result[1] or result[1] == result[2]:
            winnings = int(bet * 1.5)
            self.change_balance(interaction.user.id, interaction.guild.id, winnings)
            await interaction.response.send_message(f"[ {' | '.join(result)} ]\n✨ Two matching! Won **${winnings:,}**!")
        else:
            await interaction.response.send_message(f"[ {' | '.join(result)} ]\n💀 No match. Lost **${bet:,}**.")

    @app_commands.command(name="roulette", description="Gamble money on roulette")
    @app_commands.describe(amount="Amount to bet")
    async def roulette(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
             
        bal = self.get_balance(interaction.user.id, interaction.guild.id)
        if amount > bal:
            await interaction.response.send_message(f"💸 You don't have enough (${bal:,}).", ephemeral=True)
            return

        win = random.choice([True, False])
        if win:
            self.change_balance(interaction.user.id, interaction.guild.id, amount)
            await interaction.response.send_message(f"🎉 You won **${amount:,}**!")
        else:
            self.change_balance(interaction.user.id, interaction.guild.id, -amount)
            await interaction.response.send_message(f"💀 You lost **${amount:,}**...")

    # --- Shop & Inventory ---
    
    @app_commands.command(name="shop", description="View shop items")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🛒 NexusGuard Shop", description="Use `/buy <item>`", color=discord.Color.gold())
        items_info = {
            "lucky-charm": "🍀 Increases gambling luck",
            "vip-pass": "👑 VIP status perks",
            "lottery-ticket": "🎟️ Enter daily lottery",
            "padlock": "🔒 Protects from robbery (1 use)",
            "bank-note": "💵 Increases bank capacity",
        }
        for item, price in SHOP_ITEMS.items():
            desc = items_info.get(item, "")
            embed.add_field(name=f"{item} - ${price:,}", value=desc, inline=False)
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
            await interaction.response.send_message(f"💸 Need ${cost:,} but have ${bal:,}.", ephemeral=True)
            return

        self.change_balance(interaction.user.id, interaction.guild.id, -cost)
        new_qty = self.change_item(interaction.user.id, interaction.guild.id, item, quantity)
        await interaction.response.send_message(f"✅ Bought **{quantity}x {item}** for **${cost:,}**. You now have {new_qty}.")

    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        items = self.get_inventory(target.id, interaction.guild.id)
        if not items:
            await interaction.response.send_message(f"📦 {target.display_name}'s inventory is empty.")
            return

        embed = discord.Embed(title=f"🎒 {target.display_name}'s Inventory", color=discord.Color.blurple())
        for item, qty in items:
            embed.add_field(name=item, value=f"x{qty}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Pay another user")
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if user.bot or user.id == interaction.user.id:
            await interaction.response.send_message("❌ Invalid target.", ephemeral=True)
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
        await interaction.response.send_message(f"✅ Paid **${amount:,}** to {user.mention}.")

    @app_commands.command(name="quests", description="View active quests")
    async def quests(self, interaction: discord.Interaction):
        quests = [
            ("💼 Worker", "Use /work 10 times", "$500"),
            ("🎰 Gambler", "Win 5 gambling games", "$1,000"),
            ("🏦 Banker", "Deposit $5,000 total", "$750"),
        ]
        
        embed = discord.Embed(title="📜 Active Quests", color=discord.Color.green())
        for name, desc, reward in quests:
            embed.add_field(name=name, value=f"{desc}\nReward: **{reward}**", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
