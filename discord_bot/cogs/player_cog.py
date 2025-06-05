from typing import List
import discord
from discord.ext import commands
from discord import Embed, app_commands
import aiohttp
import os

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @app_commands.command(name="current_tile", description="Displays your current tile.")
    async def current_tile(self, interaction: discord.Interaction):
        api_url = os.getenv("GAME_API_URL", f"http://game_service_api:5000/teams/discord/{interaction.user.id}/current_tile")
        api_base_url = api_url.split('/teams/')[0]
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    tile = await resp.json()
                    embed = discord.Embed(
                        title=f"Your Current Tile: {tile.get('tile_name', 'Unknown')}",
                        description=tile.get('description', ''),
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Completion Counter", value=tile.get('completion_counter', 'N/A'))
                    image_url = tile.get('image_url')
                    if image_url:
                        # Compose the full image URL

                        print("http://game_service_api:5000/images/{image_url}")
                        embed.set_image(url=f"http://game_service_api:5000/images/{image_url}")
                    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                    await interaction.response.send_message(embed=embed)
                else:
                    error = await resp.text()
                    embed = discord.Embed(
                        title="Error",
                        description=f"Failed to look up team: {error}",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed)

async def setup(bot: commands):
    await bot.add_cog(PlayerCog(bot))