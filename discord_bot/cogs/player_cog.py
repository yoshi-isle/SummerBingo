import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
from constants import DiscordIDs, ApiUrls

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    @app_commands.command(name="board", description="View your current tile board.")
    async def view_board(self, interaction: discord.Interaction):
        try:
            # Guard against viewing board outside of team channel
            async with self.session.get(ApiUrls.TEAM_BY_ID.format(id=interaction.user.id)) as resp:
                if resp.status == 200:
                    team_data = await resp.json()
                    if str(interaction.channel_id) != team_data['discord_channel_id']:
                        await interaction.response.send_message("You can only use this command in your team channel.", ephemeral=True)
                        return
                else:
                    print(f"Error retrieving team: {e}")
                    await interaction.response.send_message(f"{e} It looks like you're not part of a team. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}> for support")
                    return
                
            async with self.session.get(ApiUrls.IMAGE_BOARD.format(id=interaction.user.id)) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                    await interaction.response.send_message(file=file)
                else:
                    await interaction.response.send_message(f"There was an error getting your board image. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
        
        except Exception as e:
            await interaction.response.send_message(f"There was an error. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")

    @app_commands.command(name="submit", description="Submits your tile completion.")
    async def submit(self, interaction: discord.Interaction, image: discord.Attachment):
        # Get the team info from the API
        team_data = None
        async with self.session.get(ApiUrls.TEAM_BY_ID.format(id=interaction.user.id)) as resp:
            if resp.status == 200:
                team_data = await resp.json()
                if not team_data or 'team_name' not in team_data:
                    await interaction.response.send_message(f"You are not part of a team. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>", ephemeral=True)
                    return
            else:
                await interaction.response.send_message(f"Error finding team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>", ephemeral=True)
                return

        # Get the current tile from the API
        current_tile = []
        async with self.session.get(ApiUrls.TEAM_CURRENT_TILE.format(id=interaction.user.id)) as resp:
            if resp.status == 200:
                tile = await resp.json()
                current_tile = tile.get('tile_name', 'Unknown Tile')
            else:
                await interaction.response.send_message(f"Error finding team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                return

        # Create submission for admin channel
        pending_submissions_channel = self.bot.get_channel(DiscordIDs.PENDING_SUBMISSIONS_CHANNEL_ID)
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
            # Create the submission in the API
            submission_data = {
                "discord_user_id": str(interaction.user.id),
                "approved": False,
                "admin_approval_embed_id": str(admin_msg.id),
                "team_channel_id": str(interaction.channel.id),
                "pending_team_embed_id": str(team_msg.id),
                "team_id": team_data['_id'],
            }
            async with self.session.post(ApiUrls.CREATE_SUBMISSION, json=submission_data) as sub_resp:
                if sub_resp.status != 201:
                    error = await sub_resp.text()
                    await interaction.channel.send(f"Failed to create submission in API: {error}")

            await interaction.response.send_message("Submitted! Please wait for an admin to approve.", ephemeral=True)

        else:
            await interaction.response.send_message("Pending submissions channel not found. Please contact an admin.", ephemeral=True)
            return

async def setup(bot: commands):
    await bot.add_cog(PlayerCog(bot))