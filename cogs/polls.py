import discord
from discord.ext import commands
from discord import app_commands

class PollButton(discord.ui.Button):
    def __init__(self, option: str, poll_view):
        super().__init__(style=discord.ButtonStyle.secondary, label=f"{option} (0)", custom_id=f"poll_{option}")
        self.option = option
        self.poll_view = poll_view
        self.votes = 0

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        # Remove previous vote if exists
        if user_id in self.poll_view.voters:
            old_button = self.poll_view.voters[user_id]
            old_button.votes -= 1
            old_button.label = f"{old_button.option} ({old_button.votes})"
        
        # Add new vote
        self.votes += 1
        self.label = f"{self.option} ({self.votes})"
        self.poll_view.voters[user_id] = self
        
        # Update embed with progress bars
        await self.poll_view.update_results(interaction)

class PollView(discord.ui.View):
    def __init__(self, question: str, options: list):
        super().__init__(timeout=None)
        self.question = question
        self.options = options
        self.voters = {}  # user_id -> button
        
        for option in options:
            self.add_item(PollButton(option, self))

    async def update_results(self, interaction: discord.Interaction):
        total_votes = sum(button.votes for button in self.children)
        
        embed = discord.Embed(title=f"📊 {self.question}", color=discord.Color.blue())
        
        for button in self.children:
            if total_votes > 0:
                percent = (button.votes / total_votes) * 100
                bars = int(percent / 5)
                progress = "█" * bars + "░" * (20 - bars)
                embed.add_field(
                    name=button.option,
                    value=f"`{progress}` {button.votes} votes ({percent:.1f}%)",
                    inline=False
                )
            else:
                embed.add_field(name=button.option, value="`░░░░░░░░░░░░░░░░░░░░` 0 votes", inline=False)
        
        embed.set_footer(text=f"Total Votes: {total_votes}")
        await interaction.response.edit_message(embed=embed, view=self)

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Create a poll")
    async def poll(self, interaction: discord.Interaction, 
                   question: str,
                   option1: str,
                   option2: str,
                   option3: str = None,
                   option4: str = None,
                   option5: str = None):
        
        options = [option1, option2]
        if option3: options.append(option3)
        if option4: options.append(option4)
        if option5: options.append(option5)

        view = PollView(question, options)
        
        embed = discord.Embed(title=f"📊 {question}", color=discord.Color.blue())
        for option in options:
            embed.add_field(name=option, value="`░░░░░░░░░░░░░░░░░░░░` 0 votes", inline=False)
        embed.set_footer(text="Total Votes: 0")

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Polls(bot))
