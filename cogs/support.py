import discord
from discord.ext import commands
from discord import ui
import asyncio

class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, emoji="📩", custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user already has a ticket
        guild = interaction.guild
        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        
        if existing_channel:
             await interaction.response.send_message(f"❌ You already have a ticket open: {existing_channel.mention}", ephemeral=True)
             return

        # Create Overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        # Try to add Mod role if exists
        # In a real deployed bot, you'd likely config this id
        mod_role = discord.utils.get(guild.roles, name="Moderator")
        if mod_role:
             overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title="Support Ticket",
            description=f"Welcome {interaction.user.mention}! Support staff will be with you shortly.\nClick the button below to close this ticket.",
            color=discord.Color.blue()
        )
        
        await channel.send(embed=embed, view=CloseTicketView())


class CloseTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()


class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Register persistent views so buttons work after restart
        self.bot.add_view(TicketView())
        self.bot.add_view(CloseTicketView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx):
        """Spawns the ticket creation panel"""
        embed = discord.Embed(
            title="Support Panel",
            description="Click the button below to open a support ticket.",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=TicketView())

async def setup(bot):
    await bot.add_cog(Support(bot))
