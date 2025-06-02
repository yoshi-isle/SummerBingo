import discord
import os

from discord.ext import commands
from dotenv import load_dotenv

from views.information_view import InformationView

class Bot(commands.Bot):
    def __init__(self):
        # Load environmental variables
        load_dotenv()
        
        # Initialize bot
        intents=discord.Intents.all()
        intents.message_content=True
        super().__init__(command_prefix="!", intents=intents)
        
        # Setup database
        # self.db = Database()

        # Setup services
        # self.applicant_service=ApplicantService(self.db)

    async def setup_hook(self) -> None:
        # Persist views
        self.add_view(InformationView(self))

        # Load cogs
        await self.load_extension("cogs.information_cog")

    async def on_ready(self):
        await self.tree.sync()
        print(f"{self.user} has connected to Discord!")


bot=Bot()

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))