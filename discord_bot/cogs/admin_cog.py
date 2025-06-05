from typing import List
import discord
from discord.ext import commands
from discord import Embed, app_commands
import aiohttp
import os

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @app_commands.command(name="register_team", description="Registers a new team")
    @app_commands.checks.has_role("Admin")
    async def register_team(self, interaction: discord.Interaction, users: str, team_name: str):
        member_ids = [int(u.strip('<@!>')) for u in users.split() if u.startswith('<@')]
        players = []
        for uid in member_ids:
            players.append({
                "discord_id": str(uid),
                "runescape_accounts": []
            })
        data = {
            "team_name": team_name,
            "players": players,
            "discord_channel_id": str(interaction.channel.id)
        }
        api_url = os.getenv("GAME_API_URL", "http://game_service_api:5000/teams")
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=data) as resp:
                if resp.status == 201:
                    team = await resp.json()
                    await interaction.response.send_message(f"Team '{team_name}' registered!", ephemeral=True)
                else:
                    error = await resp.text()
                    await interaction.response.send_message(f"Failed to register team: {error}", ephemeral=True)

async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))