import discord
from discord.ext import commands
import sqlite3
import datetime

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.star_emoji = "⭐"
        self.threshold = 3 

    def get_starboard_channel(self, guild_id):
        conn = sqlite3.connect('bot.db')
        cursor = conn.execute('SELECT value FROM settings WHERE guild_id = ? AND key = ?', (guild_id, 'starboard_channel'))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row else None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) != self.star_emoji:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        # Don't star bot messages or own messages (optional preference)
        if message.author.bot or message.author.id == payload.user_id:
             return

        starboard_channel_id = self.get_starboard_channel(payload.guild_id)
        if not starboard_channel_id:
            return
        
        starboard_channel = self.bot.get_channel(starboard_channel_id)
        if not starboard_channel: return

        # Check count
        reaction = discord.utils.get(message.reactions, emoji=self.star_emoji)
        if not reaction or reaction.count < self.threshold:
            return

        # Check if exists
        conn = sqlite3.connect('bot.db')
        cursor = conn.execute('SELECT starboard_message_id FROM starboard_entries WHERE original_message_id = ?', (message.id,))
        row = cursor.fetchone()
        
        embed = discord.Embed(description=message.content, color=discord.Color.gold())
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Original", value=f"[Jump to Message]({message.jump_url})")
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        embed.set_footer(text=f"⭐ {reaction.count} | {message.id}")

        if row:
            # Update existing
            try:
                star_msg = await starboard_channel.fetch_message(row[0])
                await star_msg.edit(content=f"⭐ **{reaction.count}** <#{channel.id}>", embed=embed)
            except:
                pass # Message might be deleted
        else:
            # Create new
            star_msg = await starboard_channel.send(content=f"⭐ **{reaction.count}** <#{channel.id}>", embed=embed)
            conn.execute('INSERT INTO starboard_entries (original_message_id, starboard_message_id, channel_id, guild_id) VALUES (?, ?, ?, ?)',
                         (message.id, star_msg.id, channel.id, payload.guild_id))
            conn.commit()
        
        conn.close()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if str(payload.emoji) != self.star_emoji:
            return

        conn = sqlite3.connect('bot.db')
        cursor = conn.execute('SELECT starboard_message_id FROM starboard_entries WHERE original_message_id = ?', (payload.message_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return
            
        starboard_channel_id = self.get_starboard_channel(payload.guild_id)
        if not starboard_channel_id:
            conn.close()
            return

        starboard_channel = self.bot.get_channel(starboard_channel_id)
        
        try:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            reaction = discord.utils.get(message.reactions, emoji=self.star_emoji)
            
            count = reaction.count if reaction else 0
            
            star_msg = await starboard_channel.fetch_message(row[0])
            
            if count < self.threshold:
                await star_msg.delete()
                conn.execute('DELETE FROM starboard_entries WHERE original_message_id = ?', (payload.message_id,))
                conn.commit()
            else:
                 await star_msg.edit(content=f"⭐ **{count}** <#{channel.id}>")
                 
        except:
            pass # Handle errors gracefully
            
        conn.close()

async def setup(bot):
    await bot.add_cog(Starboard(bot))
