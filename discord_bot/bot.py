import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from views.information_view import InformationView

class Bot(commands.Bot):
    def __init__(self):
        load_dotenv()
        intents=discord.Intents.all()
        intents.message_content=True
        super().__init__(command_prefix="!", intents=intents)
        
    async def setup_hook(self) -> None:
        self.add_view(InformationView(self))

        cogs = ["cogs.information_cog", "cogs.admin_cog", "cogs.player_cog"]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"{cog} loaded successfully.")
            except Exception as e:
                print(f"Failed to load {cog}: {e}")

    async def on_ready(self):
        await self.tree.sync()
        print(f"{self.user} has connected to Discord!")


bot=Bot()

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))