import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
from constants import DiscordIDs, ApiUrls, Emojis
from embeds import build_team_board_embed, build_key_board_embed, build_boss_board_embed

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
                    await interaction.response.send_message(f"It looks like you're not part of a team. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}> for support")
                    return
            
            # Grab board information
            async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=team_data["_id"])) as resp:
                if resp.status == 200:
                    board_information = await resp.json()
                else:
                    await interaction.response.send_message(f"There was an error getting your board information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                    return
                
            async with self.session.get(ApiUrls.IMAGE_BOARD.format(id=team_data["_id"])) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                    if int(team_data["game_state"]) == 0:
                        embed = build_team_board_embed(team_data, board_information["tile"], board_information["level_number"])
                    elif int(team_data["game_state"]) == 1:
                        embed = build_key_board_embed(team_data)
                    elif int(team_data["game_state"]) == 2:
                        embed = build_boss_board_embed(team_data)
                    embed.set_image(url="attachment://team_board.png")
                    await interaction.response.send_message(embed=embed, file=file)
                else:
                    await interaction.response.send_message(f"There was an error getting your board image. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
        
        except Exception as e:
            print(f"Error in view_board: {e}")
            await interaction.response.send_message(f"There was an unknown error. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")

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

        if team_data["game_state"] == 1:
            await interaction.response.send_message(f"You are on a key tile. Use `/key` instead.", ephemeral=True)
            return
        if team_data["game_state"] == 2:
            await interaction.response.send_message(f"You are on the boss tile. Use `/boss` instead.", ephemeral=True)
            return

        # Get the current tile from the API
        async with self.session.get(ApiUrls.TEAM_CURRENT_TILE.format(id=team_data["_id"])) as resp:
            if resp.status == 200:
                tile = await resp.json()
                current_tile = tile.get('tile_name', 'Unknown Tile')
            else:
                await interaction.response.send_message(f"Error finding team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                return

        # Create submission for admin channel
        pending_submissions_channel = self.bot.get_channel(DiscordIDs.PENDING_SUBMISSIONS_CHANNEL_ID)
        admin_embed = discord.Embed(
            title="🗺️ Board Tile Submission",
            description=f"{interaction.user.mention} submitted for {current_tile}.\nTeam: {team_data['team_name']}",
            color=discord.Color.yellow()
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
                "current_tile": team_data['current_tile'],
                "current_world": team_data['current_world']
            }
            async with self.session.post(ApiUrls.CREATE_SUBMISSION, json=submission_data) as sub_resp:
                if sub_resp.status != 201:
                    error = await sub_resp.text()
                    await interaction.channel.send(f"Failed to create submission in API: {error}")

            await interaction.response.send_message("Submitted! Please wait for an admin to approve.", ephemeral=True)

        else:
            await interaction.response.send_message("Pending submissions channel not found. Please contact an admin.", ephemeral=True)
            return

    @app_commands.command(name="key", description="Submit a key tile!")
    @app_commands.describe(
        option="Choose a key option: 1, 2, 3, 4, or 5",
        image="Attach an image as proof"
    )
    @app_commands.choices(option=[
        app_commands.Choice(name="Key #1", value=1),
        app_commands.Choice(name="Key #2", value=2),
        app_commands.Choice(name="Key #3", value=3),
        app_commands.Choice(name="Key #4", value=4),
        app_commands.Choice(name="Key #5", value=5),
    ])
    async def submit_key(
        self,
        interaction: discord.Interaction,
        option: app_commands.Choice[int],
        image: discord.Attachment
    ):
        async with self.session.get(ApiUrls.TEAM_BY_ID.format(id=interaction.user.id)) as resp:
            if resp.status == 200:
                team_data = await resp.json()
            else:
                await interaction.response.send_message(f"Error finding team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                return
          
        if team_data["game_state"] == 0:
            await interaction.response.send_message("You are on an overworld tile. Please use `submit` instead.", ephemeral=True)
            return
        
        if team_data["game_state"] == 2:
            await interaction.response.send_message("You are on the boss tile. Please use `/boss` instead.", ephemeral=True)
            return
        
        if team_data[f"w1key{option.value}_completion_counter"] <= 0:
            await interaction.response.send_message(f"{Emojis.KEY} You already have this key!", ephemeral=True)
            return
        
        async with self.session.get(ApiUrls.TEAM_CURRENT_TILE.format(id=team_data["_id"])) as resp:
            if resp.status == 200:
                tile = await resp.json()
                current_tile = tile.get('tile_name', 'Unknown Tile')
            else:
                await interaction.response.send_message(f"Error finding team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                return
        
        embed = discord.Embed(
            title="Key Tile Submitted!",
            description=f"🟡 Status: Pending\n{interaction.user.mention} submitted for key tile {option.value}. Please wait for an admin to review.",
            color=discord.Color.orange()
        )
        embed.set_image(url=image.url)
        embed.set_footer(text="Mistake with screenshot? Contact an admin.")

        team_msg = await interaction.response.send_message(embed=embed)
        team_msg = await interaction.original_response()

        admin_embed = discord.Embed(
            title=f"{Emojis.KEY} Key Tile Submission",
            description=f"{interaction.user.mention} submitted for world {team_data['current_world']} key {option.value}.\nTeam: {team_data['team_name']}",
            color=discord.Color.orange()
        )
        admin_embed.set_image(url=image.url)
        admin_embed.set_footer(text="Approve or reject this submission.")

        pending_submissions_channel = self.bot.get_channel(DiscordIDs.PENDING_SUBMISSIONS_CHANNEL_ID)
        admin_msg = await pending_submissions_channel.send(embed=admin_embed)
        await admin_msg.add_reaction("✅")
        await admin_msg.add_reaction("❌")
        
        submission_data = {
            "discord_user_id": str(interaction.user.id),
            "approved": False,
            "admin_approval_embed_id": str(admin_msg.id),
            "team_channel_id": str(interaction.channel.id),
            "pending_team_embed_id": str(team_msg.id),
            "team_id": team_data['_id'],
            "current_tile": team_data['current_tile'],
            "current_world": team_data['current_world'],
            "key_option": option.value
        }

        async with self.session.post(ApiUrls.CREATE_KEY_SUBMISSION, json=submission_data) as sub_resp:
            if sub_resp.status != 201:
                error = await sub_resp.text()
                await interaction.channel.send(f"Failed to create submission in API: {error}")

        # await interaction.response.send_message("Submitted! Please wait for an admin to approve.", ephemeral=True)

    @app_commands.command(name="boss", description="Submits your boss tile completion.")
    async def boss(self, interaction: discord.Interaction, image: discord.Attachment):
        async with self.session.get(ApiUrls.TEAM_BY_ID.format(id=interaction.user.id)) as resp:
            if resp.status == 200:
                team_data = await resp.json()
            else:
                await interaction.response.send_message(f"Error finding team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                return
        if team_data["game_state"] == 0:
            await interaction.response.send_message(f"You are on an overworld tile. Use `/submit` instead.", ephemeral=True)
            return
        if team_data["game_state"] == 1:
            await interaction.response.send_message(f"You are on a key tile. Use `/key` instead.", ephemeral=True)
            return
        
        await interaction.response.send_message("not yet implemented hi")

        
async def setup(bot: commands):
    await bot.add_cog(PlayerCog(bot))