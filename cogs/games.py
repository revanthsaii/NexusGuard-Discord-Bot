import discord
from discord.ext import commands
from discord import ui
import random
import asyncio

# --- Tic Tac Toe Classes ---

class TicTacToeButton(ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: "TicTacToe" = self.view  # type: ignore

        if interaction.user != view.current_player:
            await interaction.response.send_message(
                "It is not your turn.", ephemeral=True
            )
            return

        if view.winner is not None:
            await interaction.response.send_message(
                "The game is already over.", ephemeral=True
            )
            return

        if self.label != "\u200b":
            await interaction.response.send_message(
                "You cannot move there.", ephemeral=True
            )
            return

        mark = "X" if view.current_player == view.player_x else "O"
        self.label = mark
        self.style = (
            discord.ButtonStyle.success if mark == "X" else discord.ButtonStyle.danger
        )
        self.disabled = True
        await interaction.response.edit_message(view=view)

        if view.check_winner():
            view.winner = view.current_player
            for child in view.children:
                child.disabled = True
            await interaction.followup.send(f"🎉 {view.current_player.mention} wins!")
            await interaction.edit_original_response(view=view)
            return

        if view.is_full():
            view.winner = None
            for child in view.children:
                child.disabled = True
            await interaction.followup.send("It's a tie!")
            await interaction.edit_original_response(view=view)
            return

        view.current_player = (
            view.player_o if view.current_player == view.player_x else view.player_x
        )
        await interaction.followup.send(
            f"It is now {view.current_player.mention}'s turn.", ephemeral=False
        )


class TicTacToe(ui.View):
    def __init__(self, player_x: discord.Member, player_o: discord.Member):
        super().__init__(timeout=120)
        self.player_x = player_x
        self.player_o = player_o
        self.current_player: discord.Member = player_x
        self.winner: discord.Member | None = None

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self) -> bool:
        board = [["" for _ in range(3)] for _ in range(3)]
        for child in self.children:
            if isinstance(child, TicTacToeButton):
                board[child.y][child.x] = child.label

        lines = []
        lines.extend(board)
        lines.extend([[board[y][x] for y in range(3)] for x in range(3)])
        lines.append([board[i][i] for i in range(3)])
        lines.append([board[i][2 - i] for i in range(3)])

        for line in lines:
            if line[0] not in ("\u200b", "", None) and all(c == line[0] for c in line):
                return True
        return False

    def is_full(self) -> bool:
        for child in self.children:
            if isinstance(child, TicTacToeButton) and child.label in ("\u200b", "", None):
                return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

# --- Rock Paper Scissors Classes ---

class RPSView(ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bot_choice = random.choice(["rock", "paper", "scissors"])

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.primary, emoji="🪨")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_turn(interaction, "rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.primary, emoji="📄")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_turn(interaction, "paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.primary, emoji="✂️")
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_turn(interaction, "scissors")

    async def process_turn(self, interaction: discord.Interaction, user_choice: str):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
            
        result = ""
        win_msg = f"I chose **{self.bot_choice}**."
        
        if user_choice == self.bot_choice:
            result = "It's a tie! 🤝"
        elif (user_choice == "rock" and self.bot_choice == "scissors") or \
             (user_choice == "paper" and self.bot_choice == "rock") or \
             (user_choice == "scissors" and self.bot_choice == "paper"):
            result = "You won! 🎉"
        else:
            result = "You lost! 😢"

        await interaction.response.edit_message(content=f"{win_msg}\n{result}", view=self)
        self.stop()

# --- Main Games Cog ---

class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="tictactoe")
    async def tictactoe(self, ctx: commands.Context, opponent: discord.Member):
        """Start a Tic-Tac-Toe game: !tictactoe @user"""
        if opponent.bot:
            await ctx.send("You cannot play against bots.")
            return
        if opponent == ctx.author:
            await ctx.send("You must choose a different opponent.")
            return

        view = TicTacToe(player_x=ctx.author, player_o=opponent)
        await ctx.send(
            f"🎮 Tic-Tac-Toe: {ctx.author.mention} (X) vs {opponent.mention} (O)\n"
            f"{ctx.author.mention} goes first!",
            view=view,
        )

    @commands.command(name="rps")
    async def rps(self, ctx):
        """Play Rock Paper Scissors against the bot"""
        view = RPSView(ctx)
        await ctx.send("Choose your move!", view=view)

    @commands.command(name="coinflip")
    async def coinflip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙"
        await ctx.send(f"{emoji} It's **{result}**!")

    @commands.command(name="trivia")
    async def trivia(self, ctx):
        """Answer a random trivia question"""
        # Simple local trivia database
        questions = [
            {"q": "What is the capital of France?", "a": "Paris", "o": ["London", "Berlin", "Madrid"]},
            {"q": "Which planet is known as the Red Planet?", "a": "Mars", "o": ["Venus", "Jupiter", "Saturn"]},
            {"q": "What is the largest mammal?", "a": "Blue Whale", "o": ["Elephant", "Giraffe", "Shark"]},
            {"q": "Who wrote 'Romeo and Juliet'?", "a": "Shakespeare", "o": ["Hemingway", "Dickens", "Twain"]},
            {"q": "What is the chemical symbol for Gold?", "a": "Au", "o": ["Ag", "Fe", "Cu"]},
        ]
        
        q_data = random.choice(questions)
        options = q_data["o"] + [q_data["a"]]
        random.shuffle(options)
        
        correct_index = options.index(q_data["a"])
        
        desc = q_data["q"] + "\n\n"
        for i, opt in enumerate(options):
            desc += f"{i+1}. {opt}\n"
            
        embed = discord.Embed(title="🧠 Trivia Time", description=desc, color=discord.Color.blue())
        embed.set_footer(text="Type the number of your answer (1-4)!")
        
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
            
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=15.0)
            ans = int(msg.content)
            
            if 1 <= ans <= 4:
                if options[ans-1] == q_data["a"]:
                    await ctx.send(f"✅ Correct! The answer was **{q_data['a']}**.")
                else:
                    await ctx.send(f"❌ Wrong! The correct answer was **{q_data['a']}**.")
            else:
                 await ctx.send("❌ Invalid number.")
                 
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! The answer was **{q_data['a']}**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
