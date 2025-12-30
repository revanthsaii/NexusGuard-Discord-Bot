import discord
from discord.ext import commands


class NexusHelp(commands.MinimalHelpCommand):
    """Custom help command that shows commands in embeds."""

    def get_command_signature(self, command: commands.Command) -> str:
        # Use context.clean_prefix so it works on v2.x. [web:181][web:190][web:288]
        prefix = self.context.clean_prefix if self.context else "!"
        return f"{prefix}{command.qualified_name} {command.signature}".strip()

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="📚 NexusGuard Help",
            description=(
                "Use `!help <command>` for more details.\n"
                "Use `!help <category>` to see commands in a cog."
            ),
            color=discord.Color.blurple(),
        )

        for cog, commands_list in mapping.items():
            filtered = await self.filter_commands(commands_list, sort=True)
            if not filtered:
                continue

            cog_name = cog.qualified_name if cog else "Other"
            value_lines = []
            for command in filtered:
                if command.hidden:
                    continue
                value_lines.append(
                    f"`{self.get_command_signature(command)}` – "
                    f"{command.short_doc or 'No description'}"
                )

            if value_lines:
                embed.add_field(
                    name=cog_name,
                    value="\n".join(value_lines),
                    inline=False,
                )

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        commands_list = await self.filter_commands(cog.get_commands(), sort=True)
        if not commands_list:
            return await self.get_destination().send("No commands in this category.")

        embed = discord.Embed(
            title=f"📂 {cog.qualified_name} Commands",
            color=discord.Color.blurple(),
        )

        for command in commands_list:
            if command.hidden:
                continue
            embed.add_field(
                name=self.get_command_signature(command),
                value=command.help or "No description.",
                inline=False,
            )

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            title=f"❓ Help: {self.context.clean_prefix}{command.qualified_name}",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Description",
            value=command.help or "No description.",
            inline=False,
        )
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(command.aliases),
                inline=False,
            )
        embed.add_field(
            name="Usage",
            value=self.get_command_signature(command),
            inline=False,
        )

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error: str):
        embed = discord.Embed(
            title="❌ Help Error",
            description=error,
            color=discord.Color.red(),
        )
        await self.get_destination().send(embed=embed)


class HelpCog(commands.Cog, name="Help"):
    """Help command and categories for NexusGuard."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        help_cmd = NexusHelp()
        help_cmd.cog = self
        bot.help_command = help_cmd


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
