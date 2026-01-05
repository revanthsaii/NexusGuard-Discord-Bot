import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import os

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            print("⚠️ GEMINI_API_KEY not found in environment!")
            self.model = None

    async def get_ai_response(self, prompt, user):
        if not self.model:
            return "❌ AI is not configured. Please contact the admin."

        try:
            # Add some persona context
            context = f"You are NexusGuard, a helpful and witty Discord bot. You are chatting with {user}. Keep responses concise and formatted for Discord."
            response = await self.model.generate_content_async(f"{context}\n\nUser: {prompt}\nNexusGuard:")
            return response.text
        except Exception as e:
            return f"❌ AI Error: {str(e)}"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Respond if the bot is mentioned
        if self.bot.user in message.mentions:
            # Remove mention from content to get the clean prompt
            prompt = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            
            if not prompt:
                await message.reply("Hello! 👋 How can I help you today?")
                return

            async with message.channel.typing():
                response = await self.get_ai_response(prompt, message.author.name)
                # Split if too long (Discord limit 2000 chars)
                if len(response) > 2000:
                    for i in range(0, len(response), 2000):
                        await message.reply(response[i:i+2000])
                else:
                    await message.reply(response)

    @app_commands.command(name="ask", description="Ask NexusGuard anything (AI Powered)")
    @app_commands.describe(question="What do you want to ask?")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer() # AI might take a second
        
        response = await self.get_ai_response(question, interaction.user.name)
        
        embed = discord.Embed(title="🤖 NexusGuard AI", description=response, color=discord.Color.purple())
        embed.set_footer(text=f"Asked by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AI(bot))
