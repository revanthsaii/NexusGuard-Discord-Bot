import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_setting(self, guild_id, key):
        conn = sqlite3.connect('bot.db')
        cur = conn.execute('SELECT value FROM settings WHERE guild_id = ? AND key = ?', (guild_id, key))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None

    def save_setting(self, guild_id, key, value):
        conn = sqlite3.connect('bot.db')
        conn.execute('INSERT OR REPLACE INTO settings (guild_id, key, value) VALUES (?, ?, ?)', (guild_id, key, value))
        conn.commit()
        conn.close()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Get welcome channel
        welcome_channel_id = self.get_setting(member.guild.id, "welcome_channel_id")
        if welcome_channel_id:
            channel = member.guild.get_channel(int(welcome_channel_id))
            if channel:
                embed = discord.Embed(
                    title=f"Welcome to {member.guild.name}!",
                    description=f"Hey {member.mention}, welcome to the server! 🎉\n\nWe're glad to have you here!",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{member.guild.member_count}")
                await channel.send(embed=embed)

        # Auto-role assignment
        auto_role_id = self.get_setting(member.guild.id, "auto_role_id")
        if auto_role_id:
            role = member.guild.get_role(int(auto_role_id))
            if role:
                try:
                    await member.add_roles(role)
                except discord.Forbidden:
                    pass

    @app_commands.command(name="welcomesetup", description="Configure welcome system")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcomesetup(self, interaction: discord.Interaction, 
                           welcome_channel: discord.TextChannel = None,
                           auto_role: discord.Role = None):
        
        if not welcome_channel and not auto_role:
            # Show current settings
            wc_id = self.get_setting(interaction.guild.id, "welcome_channel_id")
            ar_id = self.get_setting(interaction.guild.id, "auto_role_id")
            
            wc = f"<#{wc_id}>" if wc_id else "Not Set"
            ar = f"<@&{ar_id}>" if ar_id else "Not Set"
            
            embed = discord.Embed(title="🖼️ Welcome System Settings", color=discord.Color.blue())
            embed.add_field(name="Welcome Channel", value=wc, inline=False)
            embed.add_field(name="Auto Role", value=ar, inline=False)
            embed.set_footer(text="Use: /welcomesetup <channel> <role> to update")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Update settings
        if welcome_channel:
            self.save_setting(interaction.guild.id, "welcome_channel_id", str(welcome_channel.id))
        
        if auto_role:
            self.save_setting(interaction.guild.id, "auto_role_id", str(auto_role.id))

        await interaction.response.send_message(f"✅ Welcome system updated!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
