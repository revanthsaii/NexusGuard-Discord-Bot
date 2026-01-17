import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

class ConfigView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.select(
        placeholder="Select Mod Log Channel",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text]
    )
    async def select_mod_log(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        self._save_setting(interaction.guild_id, "mod_log_channel", str(channel.id))
        await interaction.response.send_message(f"✅ Mod Log channel set to {channel.mention}", ephemeral=True)

    @discord.ui.select(
        placeholder="Select Ticket Category",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.category]
    )
    async def select_ticket_cat(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        category = select.values[0]
        self._save_setting(interaction.guild_id, "ticket_category", str(category.id))
        await interaction.response.send_message(f"✅ Ticket Category set to {category.name}", ephemeral=True)

    @discord.ui.select(
        placeholder="Automod Level",
        options=[
            discord.SelectOption(label="Low", description="Only basic spam filter"),
            discord.SelectOption(label="Medium", description="Spam + Common bad words"),
            discord.SelectOption(label="High", description="Strict filtering")
        ]
    )
    async def select_automod(self, interaction: discord.Interaction, select: discord.ui.Select):
        level = select.values[0]
        self._save_setting(interaction.guild_id, "automod_level", level)
        await interaction.response.send_message(f"✅ Automod level set to **{level}**", ephemeral=True)

    @discord.ui.select(
        placeholder="Select Starboard Channel",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text]
    )
    async def select_starboard(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        self._save_setting(interaction.guild_id, "starboard_channel", str(channel.id))
        await interaction.response.send_message(f"✅ Starboard channel set to {channel.mention}", ephemeral=True)

    @discord.ui.select(
        placeholder="Select Suggestions Channel",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text]
    )
    async def select_suggestions(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        self._save_setting(interaction.guild_id, "suggestions_channel", str(channel.id))
        await interaction.response.send_message(f"✅ Suggestions channel set to {channel.mention}", ephemeral=True)

    def _save_setting(self, guild_id, key, value):
        conn = sqlite3.connect('bot.db')
        conn.execute(
            'INSERT OR REPLACE INTO settings (guild_id, key, value) VALUES (?, ?, ?)',
            (guild_id, key, value)
        )
        conn.commit()
        conn.close()

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_setting(self, guild_id, key):
        conn = sqlite3.connect('bot.db')
        cur = conn.execute('SELECT value FROM settings WHERE guild_id = ? AND key = ?', (guild_id, key))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else "Not Set"

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_tree(self, ctx, spec: str = None):
        if spec == "global":
            fmt = await ctx.bot.tree.sync()
            await ctx.send(f"Synced {len(fmt)} commands globally (may take up to 1 hour).")
        else:
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            fmt = await ctx.bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"Synced {len(fmt)} commands to the current guild (Instant).")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Onboarding: Send message to system channel or owner
        channel = guild.system_channel
        if not channel:
            # Try to find first text channel
            channel = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            
        if channel:
            embed = discord.Embed(
                title="👋 Thanks for adding NexusGuard!",
                description="I'm here to help with moderation, games, and support tickets.\n\n"
                            "**Get Started:**\n"
                            "1️⃣ Run `/config` to set up logs and tickets.\n"
                            "2️⃣ Run `/help` to see all commands.\n"
                            "3️⃣ Ensure I have `Administrator` or proper permissions.",
                color=discord.Color.brand_green()
            )
            try:
                await channel.send(embed=embed)
            except:
                pass # Can't send message, oh well

    @app_commands.command(name="config", description="Configure bot settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction):
        # Fetch current settings
        log_channel_id = self.get_setting(interaction.guild_id, "mod_log_channel")
        ticket_cat_id = self.get_setting(interaction.guild_id, "ticket_category")
        ticket_cat_id = self.get_setting(interaction.guild_id, "ticket_category")
        automod_lvl = self.get_setting(interaction.guild_id, "automod_level")
        starboard_id = self.get_setting(interaction.guild_id, "starboard_channel")
        suggestions_id = self.get_setting(interaction.guild_id, "suggestions_channel")

        # Resolve IDs to names/mentions
        log_channel = f"<#{log_channel_id}>" if log_channel_id.isdigit() else log_channel_id
        
        ticket_cat = "Not Set"
        if ticket_cat_id.isdigit():
            cat = interaction.guild.get_channel(int(ticket_cat_id))
            ticket_cat = cat.name if cat else "Unknown"

        embed = discord.Embed(title="⚙️ Server Configuration", color=discord.Color.dark_grey())
        embed.add_field(name="📜 Mod Log Channel", value=log_channel, inline=False)
        embed.add_field(name="🎫 Ticket Category", value=ticket_cat, inline=False)
        embed.add_field(name="🛡️ Automod Level", value=automod_lvl, inline=False)
        
        starboard = f"<#{starboard_id}>" if starboard_id.isdigit() else starboard_id
        suggestions = f"<#{suggestions_id}>" if suggestions_id.isdigit() else suggestions_id
        
        embed.add_field(name="⭐ Starboard Channel", value=starboard, inline=False)
        embed.add_field(name="💡 Suggestions Channel", value=suggestions, inline=False)
        embed.set_footer(text="Use the dropdowns below to edit settings")

        view = ConfigView(self.bot, interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Config(bot))
