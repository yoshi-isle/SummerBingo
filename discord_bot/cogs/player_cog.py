import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import io
from constants import BASE_API_URl, TANGY_DISCORD_ID, PENDING_SUBMISSIONS_CHANNEL_ID
class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot=bot

    @app_commands.command(name="board", description="View your current tile board.")
    async def view_board(self, interaction: discord.Interaction):
        api_url = f"{BASE_API_URl}/image/user/{interaction.user.id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                        await interaction.response.send_message(f"Board for user ID: {interaction.user.id}", file=file)
                    else:
                        await interaction.response.send_message(f"There was an error getting your board image. Please contact <@{TANGY_DISCORD_ID}>")

        except Exception as e:
            print(f"Error in view_board: {e}")
            await interaction.response.send_message(f"There was an error. Please contact <@{TANGY_DISCORD_ID}>")

    @app_commands.command(name="submit", description="Submits your tile completion.")
    async def submit(self, interaction: discord.Interaction, image: discord.Attachment):

        # Get the team info from the API
        team_api_url = f"{BASE_API_URl}/teams/discord/{interaction.user.id}"
        team_data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(team_api_url) as resp:
                if resp.status == 200:
                    team_data = await resp.json()
                    if not team_data or 'team_name' not in team_data:
                        await interaction.response.send_message(f"You are not part of a team. Please contact <@{TANGY_DISCORD_ID}>", ephemeral=True)
                        return
                else:
                    await interaction.response.send_message(f"Error finding team information. Please contact <@{TANGY_DISCORD_ID}>", ephemeral=True)
                    return

        # Get the current tile from the API
        api_url = f"{BASE_API_URl}/teams/discord/{interaction.user.id}/current_tile"

        current_tile = []
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    tile = await resp.json()
                    current_tile = tile.get('tile_name', 'Unknown Tile')
                else:
                    await interaction.response.send_message(f"Error finding team information. Please contact <@{TANGY_DISCORD_ID}>")
                    return
            
        # Create submission for admin channel
        pending_submissions_channel = self.bot.get_channel(PENDING_SUBMISSIONS_CHANNEL_ID)
        admin_embed = discord.Embed(
            title=f"New Tile Submission",
            description=f"{interaction.user.mention} submitted for {current_tile}.\nTeam: {team_data['team_name']}",
            color=discord.Color.orange()
        )
        admin_embed.set_image(url=image.url)
        admin_embed.set_footer(text="Approve or reject this submission.")

        embed = discord.Embed(
                        title="Tile Submitted!",
                        description=f"🟡 Status: Pending\n{interaction.user.mention} submitted for {current_tile}. Please wait for an admin to review.",
                        color=discord.Color.yellow()
                    )
        embed.set_image(url=image.url)
        embed.set_footer(text="Mistake with screenshot? Contact an admin.")
        
        team_msg = await interaction.channel.send(embed=embed)

        if pending_submissions_channel:
            admin_msg = await pending_submissions_channel.send(embed=admin_embed)
            await admin_msg.add_reaction("✅")
            await admin_msg.add_reaction("❌")
            print(team_data)
            # Create the submission in the API
            submission_api_url = f"{BASE_API_URl}/submission"
            submission_data = {
                "discord_user_id": str(interaction.user.id),
                "approved": False,
                "admin_approval_embed_id": str(admin_msg.id),
                "team_channel_id": str(interaction.channel.id),
                "pending_team_embed_id": str(team_msg.id),
                "team_id": team_data['_id'],
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(submission_api_url, json=submission_data) as sub_resp:
                    if sub_resp.status != 201:
                        error = await sub_resp.text()
                        await interaction.channel.send(f"Failed to create submission in API: {error}")
            
            await interaction.response.send_message("Submitted! Please wait for an admin to approve.", ephemeral=True)

        else:
            await interaction.response.send_message("Pending submissions channel not found. Please contact an admin.", ephemeral=True)
            return

    @app_commands.command(name="current_tile", description="Displays your current tile.")
    async def current_tile(self, interaction: discord.Interaction):
        api_url = f"{BASE_API_URl}/teams/discord/{interaction.user.id}/current_tile"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                try:
                    if resp.status == 200:
                        tile = await resp.json()
                        embed = discord.Embed(
                            title=f"Your Current Tile: {tile['tile_name']}",
                            description=tile['description'],
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Completion Counter", value=tile['completion_counter'])
                        image_url = tile['image_url']
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
                                    await interaction.response.send_message(embed=embed, file=file)
                    else:
                        await interaction.response.send_message(f"It looks like you're not part of a team. Please contact <@{TANGY_DISCORD_ID}> for technical help.")
                except Exception as e:
                    await interaction.response.send_message(f"It looks like something is wrong internally. Please contact <@{TANGY_DISCORD_ID}> for technical help.")

async def setup(bot: commands):
    await bot.add_cog(PlayerCog(bot))