from typing import List
import discord
from discord.ext import commands
from discord import Embed, app_commands

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @app_commands.command(name="register_team", description="Registers a new team")
    @app_commands.checks.has_role("Admin")
    async def register_team(self, interaction: discord.Interaction, users: str):
        member_ids = [int(u.strip('<@!>')) for u in users.split() if u.startswith('<@')]
        t = ', '.join(str(uid) for uid in member_ids)
        await interaction.response.send_message(f"User IDs: {t}")

async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))