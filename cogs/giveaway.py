import discord
from discord import app_commands
from discord.ext import commands, tasks
import sqlite3
import datetime
import asyncio
import random
import re

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    def parse_duration(self, duration_str):
        match = re.match(r"(\d+)([dhms])", duration_str.lower())
        if not match:
            return None
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 's':
            return datetime.timedelta(seconds=amount)
        elif unit == 'm':
            return datetime.timedelta(minutes=amount)
        elif unit == 'h':
            return datetime.timedelta(hours=amount)
        elif unit == 'd':
            return datetime.timedelta(days=amount)
        return None

    @app_commands.command(name="gstart", description="Start a giveaway")
    @app_commands.describe(duration="Duration (e.g., 10s, 1m, 1h, 1d)", winners="Number of winners", prize="The prize")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def gstart(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        delta = self.parse_duration(duration)
        if not delta:
            await interaction.response.send_message("❌ Invalid duration format. Use 10s, 1m, 1h, 1d.", ephemeral=True)
            return
        
        end_time = datetime.datetime.now() + delta
        end_timestamp = end_time.timestamp()

        embed = discord.Embed(title="🎉 Giveaway! 🎉", description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(end_timestamp)}:R>", color=discord.Color.gold())
        embed.set_footer(text=f"Hosted by {interaction.user.display_name}")
        
        await interaction.response.send_message("✅ Giveaway created!", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("🎉")

        conn = sqlite3.connect('bot.db')
        conn.execute('INSERT INTO giveaways (message_id, channel_id, guild_id, host_id, winner_count, prize, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (message.id, interaction.channel.id, interaction.guild.id, interaction.user.id, winners, prize, end_timestamp))
        conn.commit()
        conn.close()

    @app_commands.command(name="gend", description="End a giveaway early")
    @app_commands.describe(message_id="Message ID of the giveaway")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def gend(self, interaction: discord.Interaction, message_id: str):
        # Allow string input for IDs as they are large
        try:
            msg_id = int(message_id)
        except ValueError:
             await interaction.response.send_message("❌ Invalid ID.", ephemeral=True)
             return

        await self.end_giveaway(msg_id)
        await interaction.response.send_message(f"✅ Ended giveaway {msg_id}.", ephemeral=True)

    @app_commands.command(name="reroll", description="Reroll a giveaway winner")
    @app_commands.describe(message_id="Message ID of the giveaway")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def reroll(self, interaction: discord.Interaction, message_id: str):
         try:
            msg_id = int(message_id)
         except ValueError:
             await interaction.response.send_message("❌ Invalid ID.", ephemeral=True)
             return
         
         conn = sqlite3.connect('bot.db')
         cursor = conn.execute('SELECT channel_id, prize FROM giveaways WHERE message_id = ? AND ended = 1', (msg_id,))
         row = cursor.fetchone()
         conn.close()

         if not row:
             await interaction.response.send_message("❌ Giveaway not found or not ended.", ephemeral=True)
             return

         channel_id, prize = row
         channel = self.bot.get_channel(channel_id)
         if not channel:
              await interaction.response.send_message("❌ Channel not found.", ephemeral=True)
              return

         try:
             message = await channel.fetch_message(msg_id)
         except:
             await interaction.response.send_message("❌ Message not found.", ephemeral=True)
             return

         users = []
         async for user in message.reactions[0].users(): # Assuming first reaction is 🎉
             if not user.bot:
                 users.append(user)

         if not users:
             await interaction.channel.send(f"❌ No valid entries for reroll of **{prize}**.")
             return

         winner = random.choice(users)
         await channel.send(f"🎉 **Reroll!** The new winner of **{prize}** is {winner.mention}!")
         await interaction.response.send_message("✅ Rerolled.", ephemeral=True)

    async def end_giveaway(self, message_id):
        conn = sqlite3.connect('bot.db')
        cursor = conn.execute('SELECT channel_id, winner_count, prize, host_id FROM giveaways WHERE message_id = ? AND ended = 0', (message_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return

        channel_id, winners_count, prize, host_id = row
        
        # Mark as ended
        conn.execute('UPDATE giveaways SET ended = 1 WHERE message_id = ?', (message_id,))
        conn.commit()
        conn.close()

        channel = self.bot.get_channel(channel_id)
        if not channel: return
        
        try:
            message = await channel.fetch_message(message_id)
        except:
            return 
        
        users = []
        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if reaction:
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
        
        if not users:
            await channel.send(f"❌ Giveaway for **{prize}** ended with no entries.")
            embed = message.embeds[0]
            embed.description = f"**Prize:** {prize}\n**Winner:** None\n**Ended:** <t:{int(datetime.datetime.now().timestamp())}:R>"
            await message.edit(embed=embed)
            return

        winners = random.sample(users, k=min(len(users), winners_count))
        winner_mentions = ", ".join([w.mention for w in winners])
        
        await channel.send(f"🎉 Congratulations {winner_mentions}! You won **{prize}**!")
        
        embed = message.embeds[0]
        embed.description = f"**Prize:** {prize}\n**Winner:** {winner_mentions}\n**Ended:** <t:{int(datetime.datetime.now().timestamp())}:R>"
        await message.edit(embed=embed)

    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        conn = sqlite3.connect('bot.db')
        now = datetime.datetime.now().timestamp()
        cursor = conn.execute('SELECT message_id FROM giveaways WHERE end_time <= ? AND ended = 0', (now,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            await self.end_giveaway(row[0])

    @check_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
