import discord
from discord.ext import commands


class ErrorHandler(commands.Cog, name="Errors"):
    """Global error handler for NexusGuard."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # Let local handlers (like work_error, daily_error) run first. [web:295][web:302]
        if hasattr(ctx.command, "on_error"):
            return

        # Unwrap original error
        error = getattr(error, "original", error)

        # Ignore unknown commands
        if isinstance(error, commands.CommandNotFound):
            return

        # Missing required args / bad args
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                f"❌ Missing argument: **{error.param.name}**.\n"
                f"Use `!help {ctx.command.qualified_name}` for usage."
            )

        if isinstance(error, commands.BadArgument):
            return await ctx.send(
                f"❌ Invalid argument for `{ctx.command.qualified_name}`.\n"
                f"Use `!help {ctx.command.qualified_name}` for correct usage."
            )

        # Permission errors
        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            return await ctx.send(
                f"🚫 You are missing permissions to use this command: **{perms}**."
            )

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            return await ctx.send(
                f"🤖 I am missing permissions to do that: **{perms}**."
            )

        # Cooldowns not handled locally
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f"⏳ That command is on cooldown. Try again in "
                f"**{int(error.retry_after)} seconds**."
            )

        # Fallback: unknown error
        # Log full traceback to console, send generic message. [web:304]
        print(f"Ignoring exception in command {ctx.command}:", flush=True)
        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)

        await ctx.send(
            "⚠️ An unexpected error occurred while running this command."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))
