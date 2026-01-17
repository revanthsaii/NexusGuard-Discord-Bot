import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_suggestion_channel(self, guild_id):
        conn = sqlite3.connect('bot.db')
        cursor = conn.execute('SELECT value FROM settings WHERE guild_id = ? AND key = ?', (guild_id, 'suggestions_channel'))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row else None

    @app_commands.command(name="suggest", description="Submit a suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        channel_id = self.get_suggestion_channel(interaction.guild.id)
        if not channel_id:
            await interaction.response.send_message("❌ Suggestions channel not set up.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(channel_id)
        if not channel:
             await interaction.response.send_message("❌ Suggestions channel not found.", ephemeral=True)
             return

        embed = discord.Embed(title="New Suggestion", description=suggestion, color=discord.Color.blue())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Status: Pending | User ID: {interaction.user.id}")
        
        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        
        conn = sqlite3.connect('bot.db')
        conn.execute('INSERT INTO suggestions (guild_id, user_id, message_id, content) VALUES (?, ?, ?, ?)',
                     (interaction.guild.id, interaction.user.id, msg.id, suggestion))
        conn.commit()
        conn.close()

        await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)

    @app_commands.command(name="approve", description="Approve a suggestion")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def approve(self, interaction: discord.Interaction, message_id: str, reason: str = "No reason provided"):
        try:
            msg_id = int(message_id)
        except:
             await interaction.response.send_message("❌ Invalid ID.", ephemeral=True)
             return

        await self.update_suggestion(interaction, msg_id, "Approved", discord.Color.green(), reason)

    @app_commands.command(name="deny", description="Deny a suggestion")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def deny(self, interaction: discord.Interaction, message_id: str, reason: str = "No reason provided"):
        try:
            msg_id = int(message_id)
        except:
             await interaction.response.send_message("❌ Invalid ID.", ephemeral=True)
             return

        await self.update_suggestion(interaction, msg_id, "Denied", discord.Color.red(), reason)

    async def update_suggestion(self, interaction, message_id, status, color, reason):
        channel_id = self.get_suggestion_channel(interaction.guild.id)
        if not channel_id:
             await interaction.response.send_message("❌ Suggestions channel not configured.", ephemeral=True)
             return

        channel = interaction.guild.get_channel(channel_id)
        try:
            msg = await channel.fetch_message(message_id)
        except:
            await interaction.response.send_message("❌ Suggestion message not found.", ephemeral=True)
            return

        embed = msg.embeds[0]
        embed.color = color
        embed.clear_fields()
        embed.add_field(name=f"{status} by {interaction.user.display_name}", value=reason)
        embed.set_footer(text=f"Status: {status} | User ID: {embed.footer.text.split('|')[-1].strip().replace('User ID: ', '')}")
        
        await msg.edit(embed=embed)
        
        # Update DB
        conn = sqlite3.connect('bot.db')
        conn.execute('UPDATE suggestions SET status = ? WHERE message_id = ?', (status, message_id))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"✅ Suggestion {status.lower()}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
