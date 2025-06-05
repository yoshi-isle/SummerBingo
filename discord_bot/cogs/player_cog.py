from typing import List
import discord
from discord.ext import commands
from discord import Embed, app_commands
import aiohttp
import os
import io
from constants import BASE_API_URl
class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @app_commands.command(name="current_tile", description="Displays your current tile.")
    async def current_tile(self, interaction: discord.Interaction):
        api_url = f"{BASE_API_URl}/teams/discord/{interaction.user.id}/current_tile"
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
                    file = None
                    if image_url:
                        image_api_url = f"{BASE_API_URl}/images/{image_url}"
                        async with session.get(image_api_url) as img_resp:
                            if img_resp.status == 200:
                                img_bytes = await img_resp.read()
                                filename = os.path.basename(image_url)
                                file = discord.File(fp=discord.File(io.BytesIO(img_bytes), filename=filename).fp, filename=filename)
                                embed.set_image(url=f"attachment://{filename}")
                    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                    if file:
                        await interaction.response.send_message(embed=embed, file=file)
                    else:
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