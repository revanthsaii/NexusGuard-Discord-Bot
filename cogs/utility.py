import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(time="Time in minutes", message="Reminder message")
    async def remind(self, interaction: discord.Interaction, time: int, message: str):
        if time <= 0 or time > 10080:  # Max 1 week
            await interaction.response.send_message("❌ Time must be between 1 minute and 1 week.", ephemeral=True)
            return

        await interaction.response.send_message(f"⏰ I'll remind you in **{time} minute(s)**: {message}", ephemeral=True)
        
        await asyncio.sleep(time * 60)
        
        try:
            await interaction.user.send(f"⏰ **Reminder:** {message}")
        except:
            # If DM fails, try to send in the channel
            try:
                await interaction.channel.send(f"{interaction.user.mention} ⏰ **Reminder:** {message}")
            except:
                pass

    @app_commands.command(name="avatar", description="View a user's avatar")
    async def avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        embed = discord.Embed(title=f"{target.display_name}'s Avatar", color=discord.Color.purple())
        embed.set_image(url=target.display_avatar.url)
        embed.add_field(name="Download", value=f"[Click Here]({target.display_avatar.url})")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="View detailed user information")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        # Get user level if leveling cog is loaded
        level_text = "N/A"
        leveling_cog = self.bot.get_cog("Leveling")
        if leveling_cog:
            data = leveling_cog.get_user_data(target.id, interaction.guild.id)
            if data:
                level_text = f"Level {data[1]} ({data[0]} XP)"

        # Calculate account age
        account_age = (discord.utils.utcnow() - target.created_at).days
        join_age = (discord.utils.utcnow() - target.joined_at).days if target.joined_at else 0

        embed = discord.Embed(title=f"User Info: {target.display_name}", color=target.color)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(name="ID", value=target.id, inline=True)
        embed.add_field(name="Nickname", value=target.nick or "None", inline=True)
        embed.add_field(name="Level", value=level_text, inline=True)
        
        embed.add_field(name="Account Created", value=f"{account_age} days ago", inline=True)
        embed.add_field(name="Joined Server", value=f"{join_age} days ago", inline=True)
        embed.add_field(name="Roles", value=f"{len(target.roles)-1}", inline=True)
        
        # Top roles (max 3)
        top_roles = [r.mention for r in target.roles[1:][::-1][:3]]
        if top_roles:
            embed.add_field(name="Top Roles", value=", ".join(top_roles), inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
