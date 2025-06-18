import discord
from discord.ext import commands
from discord import Embed, app_commands

from views.information_view import InformationView

class InformationCog(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @app_commands.command(name="post_information_embed", description="Displays information embed")
    @app_commands.checks.has_role("Admin")
    async def post_welcome_embed(self, interaction: discord.Interaction):
        await interaction.channel.send(embed=Embed(title="Information", description="Here is some information."), view=InformationView(self.bot))
        await interaction.response.send_message(f"Embed posted", ephemeral=True)

async def setup(bot: commands):
    await bot.add_cog(InformationCog(bot))