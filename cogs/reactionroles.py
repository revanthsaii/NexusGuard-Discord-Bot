import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

class ReactionRoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role, label: str):
        super().__init__(style=discord.ButtonStyle.primary, label=label, custom_id=f"rr_{role.id}")
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        if self.role in member.roles:
            await member.remove_roles(self.role)
            await interaction.response.send_message(f"❌ Removed role: {self.role.mention}", ephemeral=True)
        else:
            await member.add_roles(self.role)
            await interaction.response.send_message(f"✅ Added role: {self.role.mention}", ephemeral=True)

class ReactionRoleView(discord.ui.View):
    def __init__(self, guild, roles_data):
        super().__init__(timeout=None)
        for role_id, label in roles_data:
            role = guild.get_role(int(role_id))
            if role:
                self.add_item(ReactionRoleButton(role, label))

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._ensure_table()

    def _ensure_table(self):
        conn = sqlite3.connect('bot.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS reaction_roles (
            message_id INTEGER,
            role_id INTEGER,
            label TEXT,
            PRIMARY KEY (message_id, role_id)
        )''')
        conn.commit()
        conn.close()

    @commands.Cog.listener()
    async def on_ready(self):
        # Re-register persistent views
        conn = sqlite3.connect('bot.db')
        cur = conn.execute("SELECT DISTINCT message_id FROM reaction_roles")
        message_ids = [row[0] for row in cur.fetchall()]
        conn.close()

        for msg_id in message_ids:
            conn = sqlite3.connect('bot.db')
            cur = conn.execute("SELECT role_id, label FROM reaction_roles WHERE message_id = ?", (msg_id,))
            roles_data = cur.fetchall()
            conn.close()
            
            # Find the message in all guilds and re-attach the view
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    try:
                        message = await channel.fetch_message(msg_id)
                        view = ReactionRoleView(guild, roles_data)
                        self.bot.add_view(view, message_id=msg_id)
                        break
                    except:
                        continue

    @app_commands.command(name="reactionrole", description="Create a reaction role panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def reactionrole(self, interaction: discord.Interaction, 
                           title: str,
                           role1: discord.Role, role1_label: str,
                           role2: discord.Role = None, role2_label: str = None,
                           role3: discord.Role = None, role3_label: str = None,
                           role4: discord.Role = None, role4_label: str = None):
        
        roles_data = [(role1.id, role1_label)]
        if role2: roles_data.append((role2.id, role2_label))
        if role3: roles_data.append((role3.id, role3_label))
        if role4: roles_data.append((role4.id, role4_label))

        embed = discord.Embed(title=title, description="Click buttons below to get roles!", color=discord.Color.purple())
        view = ReactionRoleView(interaction.guild, roles_data)

        await interaction.response.send_message("✅ Panel created below!", ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=view)

        # Save to DB
        conn = sqlite3.connect('bot.db')
        for role_id, label in roles_data:
            conn.execute("INSERT INTO reaction_roles VALUES (?, ?, ?)", (msg.id, role_id, label))
        conn.commit()
        conn.close()

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
