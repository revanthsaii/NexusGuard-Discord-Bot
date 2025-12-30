import discord
from discord.ext import commands
from discord import ui

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

async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
