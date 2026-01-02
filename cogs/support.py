import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio

class TicketTypeSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", emoji="🛠️", description="Ask a question or get help"),
            discord.SelectOption(label="Bug Report", emoji="🐞", description="Report a bot or server issue"),
            discord.SelectOption(label="Ban Appeal", emoji="🔨", description="Appeal a punishment")
        ]
        super().__init__(placeholder="Select Ticket Type", min_values=1, max_values=1, options=options, custom_id="ticket_type_select")

    async def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0]
        category_name = "Tickets" # Could map types to different categories if needed
        channel_name_prefix = {
            "General Support": "ticket",
            "Bug Report": "bug",
            "Ban Appeal": "appeal"
        }.get(ticket_type, "ticket")


        guild = interaction.guild
        existing = discord.utils.get(guild.text_channels, name=f"{channel_name_prefix}-{interaction.user.name.lower()}")
        
        if existing:
             await interaction.response.send_message(f"❌ You already have a ticket: {existing.mention}", ephemeral=True)
             return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        mod_role = discord.utils.get(guild.roles, name="Moderator")
        if mod_role:
             overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                category = await guild.create_category(category_name)

            channel = await guild.create_text_channel(
                name=f"{channel_name_prefix}-{interaction.user.name}",
                category=category,
                overwrites=overwrites
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ I need 'Manage Channels' permission!", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Created **{ticket_type}**: {channel.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title=f"{ticket_type}",
            description=f"Welcome {interaction.user.mention}!\n\n**Category:** {ticket_type}\nPlease state your issue below.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=CloseTicketView())

class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

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
        self.bot.add_view(TicketView())
        self.bot.add_view(CloseTicketView())

    @app_commands.command(name="ticketpanel", description="Spawn the ticket creation panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticketpanel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Support Panel",
            description="Click the button below to open a support ticket.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message("Panel created below!", ephemeral=True)
        await interaction.channel.send(embed=embed, view=TicketView())

    @app_commands.command(name="ticket_stats", description="View ticket statistics")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Count channels starting with prefixes
        tickets = 0
        bugs = 0
        appeals = 0
        
        for channel in guild.text_channels:
            if channel.name.startswith("ticket-"):
                tickets += 1
            elif channel.name.startswith("bug-"):
                bugs += 1
            elif channel.name.startswith("appeal-"):
                appeals += 1
                
        total = tickets + bugs + appeals
        
        embed = discord.Embed(title="🎫 Ticket Statistics", color=discord.Color.teal())
        embed.add_field(name="Open Tickets", value=str(tickets), inline=True)
        embed.add_field(name="Bug Reports", value=str(bugs), inline=True)
        embed.add_field(name="Ban Appeals", value=str(appeals), inline=True)
        embed.add_field(name="Total Open", value=str(total), inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Support(bot))
