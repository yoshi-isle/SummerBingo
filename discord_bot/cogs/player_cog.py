from datetime import timedelta
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
from constants import DiscordIDs, ApiUrls, Emojis
from utils.get_team_from_id import get_team_from_id
from utils.game_hasnt_started import game_hasnt_started
from embeds import (
    build_team_board_embed,
    build_w1_key_board_embed,
    build_w1_boss_board_embed,
    build_w2_key_board_embed,
    build_w2_boss_board_embed,
    build_w3_key_board_embed,
    build_w3_boss_board_embed,
    build_w4_key_board_embed,
    build_w4_boss_board_embed
)
from dateutil import parser

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    def get_trial_option_name(self, world: int, option: int) -> str:
        """Get the trial option name based on world and option value."""
        world_trials = {
            1: {
                1: "2x Scrolls or Twisted Kits from CoX",
                2: "Crystal Tool Seed",
                3: "4x Burning Claws or Synapses",
                4: "Bryophyta's Essence OR Hill Giant Club",
                5: "10x Elite Clues",
            },
            2: {
                1: "Golden Tench",
                2: "Golden Pheasant egg",
                3: "3x Sunfire Fanatic Pieces",
                4: "3x Cerberus Crystals",
                5: "3x Weapons from CoX/ToB/ToA",
            },
            3: {
                1: "10x Vorkath Heads",
                2: "Dragon Hunter Wand",
                3: "Granite Man",
                4: "Raid Man",
                5: "Bran",
                6: "Moxi",
            },
            4: {
                1: "Any 3x Armor Pieces from ToB/CoX/ToA",
                2: "3x Oathplate Armor Pieces",
                3: "Enhanced Weapon Seed",
                4: "Nightmare Staff",
                5: "5x Holy Elixir",
            },
        }
        
        return world_trials.get(world, {}).get(option, f"Trial {option}")

    @app_commands.command(name="board", description="View your current tile board.")
    async def view_board(self, interaction: discord.Interaction):
        try:
            team_data = await get_team_from_id(self.session, interaction.user.id)
            if not team_data:
                await interaction.response.send_message(f"You are not part of a team. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>", ephemeral=True)
                return
            
            in_correct_channel = str(interaction.channel_id) == team_data['discord_channel_id']
            if not in_correct_channel:
                await interaction.response.send_message("You can only use this command in your team channel.", ephemeral=True)
                return
            
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
                        embed = build_team_board_embed(team_data, board_information["tile"], board_information["level_number"], board_information["placement"])
                    elif int(team_data["game_state"]) == 1 and int(team_data["current_world"]) == 1:
                        embed = build_w1_key_board_embed(team_data)
                    elif int(team_data["game_state"]) == 2 and int(team_data["current_world"]) == 1:
                        embed = build_w1_boss_board_embed(team_data)
                    elif int(team_data["game_state"]) == 1 and int(team_data["current_world"]) == 2:
                        embed = build_w2_key_board_embed(team_data)
                    elif int(team_data["game_state"]) == 2 and int(team_data["current_world"]) == 2:
                        embed = build_w2_boss_board_embed(team_data)
                    elif int(team_data["game_state"]) == 1 and int(team_data["current_world"]) == 3:
                        embed = build_w3_key_board_embed(team_data)
                    elif int(team_data["game_state"]) == 2 and int(team_data["current_world"]) == 3:
                        embed = build_w3_boss_board_embed(team_data)
                    elif int(team_data["game_state"]) == 1 and int(team_data["current_world"]) == 4:
                        embed = build_w4_key_board_embed(team_data)
                    elif int(team_data["game_state"]) == 2 and int(team_data["current_world"]) == 4:
                        embed = build_w4_boss_board_embed(team_data)
                    else:
                        await interaction.response.send_message(f"Error. Contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                        return
                    embed.set_image(url="attachment://team_board.png")
                    await interaction.response.send_message(embed=embed, file=file)
                else:
                    await interaction.response.send_message(f"There was an error getting your board image. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
        
        except Exception as e:
            print(f"Error in view_board: {e}")
            await interaction.response.send_message(f"There was an unknown error. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")

    async def submit_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[int]]:
        try:
            # Get the user's team data to determine their current state
            team_data = await get_team_from_id(self.session, interaction.user.id)
            if not team_data:
                return []
            
            game_state = team_data.get('game_state', 0)
            current_world = team_data.get('current_world', 1)
            
            # If on overworld tiles (game_state 0), show current tile name
            if game_state == 0:
                # Get the current tile from the API to get the tile name
                async with self.session.get(ApiUrls.TEAM_CURRENT_TILE.format(id=team_data["_id"])) as resp:
                    if resp.status == 200:
                        tile = await resp.json()
                        tile_name = tile.get('tile_name', 'Current Tile')
                        return [app_commands.Choice(name=tile_name, value=0)]
                    else:
                        return [app_commands.Choice(name="Current Tile", value=0)]
            
            # If on trial tiles (game_state 1), show trial options
            elif game_state == 1:
                # Define different trial options for each world
                world_trials = {
                    1: [
                        app_commands.Choice(name="2x Dex/Arcane Scrolls or Twisted Kits from CoX", value=1),
                        app_commands.Choice(name="Crystal Tool Seed", value=2),
                        app_commands.Choice(name="4x Burning Claws or Synapses", value=3),
                        app_commands.Choice(name="Bryophyta's Essence OR Hill Giant Club", value=4),
                        app_commands.Choice(name="10x Elite Clues", value=5),
                    ],
                    2: [
                        app_commands.Choice(name="Golden Tench", value=1),
                        app_commands.Choice(name="Golden Pheasant egg", value=2),
                        app_commands.Choice(name="3x Sunfire Fanatic Pieces", value=3),
                        app_commands.Choice(name="3x Cerberus Crystals", value=4),
                        app_commands.Choice(name="3x Weapons from CoX/ToB/ToA", value=5),
                    ],
                    3: [
                        app_commands.Choice(name="10x Vorkath Heads", value=1),
                        app_commands.Choice(name="Dragon Hunter Wand", value=2),
                        app_commands.Choice(name="Granite Man", value=3),
                        app_commands.Choice(name="Raid Man", value=4),
                        app_commands.Choice(name="Bran", value=5),
                        app_commands.Choice(name="Moxi", value=6),
                    ],
                    4: [
                        app_commands.Choice(name="Any 3x Armor Pieces from ToB/CoX/ToA", value=1),
                        app_commands.Choice(name="3x Oathplate Armor Pieces", value=2),
                        app_commands.Choice(name="Enhanced Weapon Seed", value=3),
                        app_commands.Choice(name="Nightmare Staff", value=4),
                        app_commands.Choice(name="Holy Elixir", value=5),
                    ],
                }
                
                # Get trials for the current world, default to world 1 if not found
                trials = world_trials.get(current_world, world_trials[1])

                # For world 2, filter based on the path chosen
                if current_world == 2:
                    w2_path_chosen = int(team_data.get('w2_path_chosen', 0))
                    if w2_path_chosen == 0:
                        trials = [trial for trial in trials if trial.value in [1, 2]]
                    elif w2_path_chosen == -1:
                        trials = [trial for trial in trials if trial.value in [3]]
                    elif w2_path_chosen == 1:
                        trials = [trial for trial in trials if trial.value in [4]]
                    elif w2_path_chosen == 2:
                        trials = [trial for trial in trials if trial.value in [5]]

                # For world 3, filter based on the braziers lit
                if current_world == 3:
                    braziers_lit = team_data.get('w3_braziers_lit', 0)
                    if braziers_lit == 0:
                        trials = [trial for trial in trials if trial.value in [1, 2]]
                    elif braziers_lit == 1:
                        trials = [trial for trial in trials if trial.value in [3, 4]]
                    elif braziers_lit == 2:
                        trials = [trial for trial in trials if trial.value in [5, 6]]

                # For world 4, filter based on the trial iteration
                if current_world == 4:
                    w4_trial_iteration = team_data.get('w4_trial_iteration', 0)
                    if w4_trial_iteration == 0:
                        trials = [trial for trial in trials if trial.value in [1]]
                    elif w4_trial_iteration == 1:
                        trials = [trial for trial in trials if trial.value in [2, 3, 4]]
                    elif w4_trial_iteration == 2:
                        trials = [trial for trial in trials if trial.value in [5]]

                # Filter based on current input if provided
                if current:
                    trials = [trial for trial in trials if current.lower() in trial.name.lower()]
                
                return trials
            
            # If on boss tiles (game_state 2), show boss options
            elif game_state == 2:
                world_bosses = {
                    1: [
                        app_commands.Choice(name="Any CoX Mega-rare or Dust", value=1),
                    ],
                    2: [
                        app_commands.Choice(name="Tonalztics of Ralos", value=1),
                    ],
                    3: [
                        app_commands.Choice(name="ZCB from scratch", value=1),
                    ],
                    4: [
                        app_commands.Choice(name="5 HMT Kits", value=1),
                    ],
                }
                
                bosses = world_bosses.get(current_world, world_bosses[1])
                
                # Filter based on current input if provided
                if current:
                    bosses = [boss for boss in bosses if current.lower() in boss.name.lower()]
                
                return bosses
            
            else:
                return []
            
        except Exception as e:
            print(f"Error in submit_autocomplete: {e}")
            # Return default choice if there's an error
            return [app_commands.Choice(name="Current Tile", value=0)]

    @app_commands.command(name="submit", description="Submit your current tile completion (overworld or trial)")
    @app_commands.describe(
        option="Select your current tile or trial option",
        image="Attach an image as proof"
    )
    @app_commands.autocomplete(option=submit_autocomplete)
    async def submit(
        self,
        interaction: discord.Interaction,
        option: int,
        image: discord.Attachment
    ):
        pending_submissions_channel = self.bot.get_channel(DiscordIDs.PENDING_SUBMISSIONS_CHANNEL_ID)

        if await game_hasnt_started(self.session):
            await interaction.response.send_message("Bingo hasn't started yet.")
            return
        
        team_data = await get_team_from_id(self.session, interaction.user.id)
        if not team_data:
            await interaction.response.send_message(f"You are not part of a team. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>", ephemeral=True)
            return
        
        in_correct_channel = str(interaction.channel_id) == team_data['discord_channel_id']
        if not in_correct_channel:
            await interaction.response.send_message("You can only use this command in your team channel.", ephemeral=True)
            return

        game_state = team_data["game_state"]
        
        # Boss_submission creation
        if game_state == 2:
            admin_embed = discord.Embed(
                title=f"{Emojis.TRIAL_COMPLETE} Boss Submission",
                description=f"{interaction.user.mention} submitted for world {team_data['current_world']} boss tile.\nTeam: {team_data['team_name']}",
                color=discord.Color.red()
            )
            embed = discord.Embed(
                title=f"{Emojis.TRIAL_COMPLETE} Boss Tile Submitted!",
                description=f"🟡 Status: Pending\n{interaction.user.mention} submitted the boss tile. Please wait for an admin to review.",
                color=discord.Color.yellow()
            )
            embed.set_thumbnail(url=image.url)
            embed.set_footer(text="Mistake with screenshot? Contact an admin.")

            team_msg = await interaction.response.send_message(embed=embed)
            team_msg = await interaction.original_response()

            admin_embed.set_image(url=image.url)
            admin_embed.set_footer(text="Approve or reject this submission.")

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
                "current_world": team_data['current_world']
            }
            async with self.session.post(ApiUrls.CREATE_BOSS_SUBMISSION, json=submission_data) as sub_resp:
                if sub_resp.status != 201:
                    error = await sub_resp.text()
                    await interaction.followup.send(f"Failed to create submission in API: {error}")
            return

        # Get the current tile from the API
        async with self.session.get(ApiUrls.TEAM_CURRENT_TILE.format(id=team_data["_id"])) as resp:
            if resp.status == 200:
                tile = await resp.json()
                current_tile = tile.get('tile_name', 'Unknown Tile')
            else:
                await interaction.response.send_message(f"Error finding team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                return
        
        # Handle overworld tiles (game_state 0)
        if game_state == 0:
            # Create submission for admin channel
            admin_embed = discord.Embed(
                title=f"{Emojis.WORLD_MAP} Overworld Tile Submission",
                description=f"Submission by {interaction.user.mention}.",
                color=discord.Color.yellow()
            )
            admin_embed.add_field(
                name="Team",
                value=team_data['team_name'],
            )
            admin_embed.add_field(
                name="Tile",
                value=current_tile,
            )
            # Convert last_rolled_at to Discord timestamp format
            last_rolled_dt = parser.parse(team_data["last_rolled_at"])
            discord_timestamp = f"<t:{int(last_rolled_dt.timestamp())}:F>"
            admin_embed.add_field(
                name="Tile landed on time",
                value=discord_timestamp,
            )
            admin_embed.set_image(url=image.url)
            admin_embed.set_footer(text="Approve or reject this submission.", icon_url=Emojis.SKW_LOGO)

            embed = discord.Embed(
                title=f"{Emojis.SUBMISSIONS} Tile Submitted!",
                description=f"🟡 Status: Pending\n{interaction.user.mention} submitted for {current_tile}. Please wait for an admin to review.",
                color=discord.Color.yellow()
            )
            embed.set_thumbnail(url=image.url)
            embed.set_footer(text="Mistake with screenshot? Contact an admin.", icon_url=Emojis.SKW_LOGO)

            team_msg = await interaction.response.send_message(embed=embed)
            team_msg = await interaction.original_response()

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
                        await interaction.followup.send(f"Failed to create submission in API: {error}")
            else:
                await interaction.followup.send("Pending submissions channel not found. Please contact an admin.", ephemeral=True)
                return
                
        # Handle trial tiles (game_state 1)
        elif game_state == 1:
            # World 2 path validation logic
            if team_data['current_world'] == 2:
                if team_data['w2_path_chosen'] == 0:
                    not_allowed = [3, 4, 5]
                    if option in not_allowed and team_data[f'w2key{option}_completion_counter'] != 0:
                        await interaction.response.send_message(f"You cannot submit {option} yet. Start with trial 1 or 2 instead.", ephemeral=True)
                        return
                # If going left, you complete trial 3 next.
                elif team_data['w2_path_chosen'] == -1:
                    not_allowed = [1, 2, 4, 5]
                    if option in not_allowed and team_data[f'w2key{option}_completion_counter'] != 0:
                        await interaction.response.send_message(f"You cannot submit {option}. Complete trial 3 instead.", ephemeral=True)
                        return
                # If going right, you complete trial 4 next.
                elif team_data['w2_path_chosen'] == 1:
                    not_allowed = [1, 2, 3, 5]
                    if option in not_allowed and team_data[f'w2key{option}_completion_counter'] != 0:
                        await interaction.response.send_message(f"You cannot submit {option}. Complete trial 4 instead.", ephemeral=True)
                        return
                # Both paths end up at trial 5
                elif team_data['w2_path_chosen'] == 2:
                    not_allowed = [1, 2, 3, 4]
                    if option in not_allowed and team_data[f'w2key{option}_completion_counter'] != 0:
                        await interaction.response.send_message(f"You cannot submit {option} yet. Start with trial 5 instead.", ephemeral=True)
                        return

            if team_data[f"w{team_data['current_world']}key{option}_completion_counter"] <= 0:
                await interaction.response.send_message(f"{Emojis.TRIAL_COMPLETE} You already have this trial completed. Wrong option?", ephemeral=True)
                return
            
            # Get the trial option name
            trial_option_name = self.get_trial_option_name(team_data['current_world'], option)
            
            embed = discord.Embed(
                title=f"{Emojis.TRIAL_COMPLETE} Trial Completion Submitted!",
                description=f"🟡 Status: Pending\n{interaction.user.mention} submitted for a trial. Please wait for an admin to review.",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=image.url)
            embed.set_footer(text="Mistake with screenshot? Contact an admin.")

            team_msg = await interaction.response.send_message(embed=embed)
            team_msg = await interaction.original_response()

            admin_embed = discord.Embed(
                title=f"{Emojis.TRIAL_COMPLETE} Trial Submission",
                description=f"{interaction.user.mention} submitted for a world {team_data['current_world']} trial.\nTeam: {team_data['team_name']}\nTrial: {trial_option_name}",
                color=discord.Color.orange()
            )
            admin_embed.set_image(url=image.url)
            admin_embed.set_footer(text="Approve or reject this submission.")

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
                "current_world": team_data['current_world'],
                "key_option": option
            }

            async with self.session.post(ApiUrls.CREATE_KEY_SUBMISSION, json=submission_data) as sub_resp:
                if sub_resp.status != 201:
                    error = await sub_resp.text()
                    await interaction.followup.send(f"Failed to create submission in API: {error}")

    @app_commands.command(name="skip", description="Skip the current tile.")
    async def skip(self, interaction: discord.Interaction):
        if await game_hasnt_started(self.session):
            await interaction.response.send_message("Bingo hasn't started yet.")
            return

        async with self.session.get(ApiUrls.TEAM_BY_ID.format(id=interaction.user.id)) as resp:
            if resp.status == 200:
                team_data = await resp.json()
            else:
                await interaction.response.send_message(f"Error finding team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")
                return
            
        in_correct_channel = str(interaction.channel_id) == team_data['discord_channel_id']
        if not in_correct_channel:
            await interaction.response.send_message("You can only use this command in your team channel.", ephemeral=True)
            return

        if team_data["game_state"] == 1:
            await interaction.response.send_message(f"You cannot skip a trial tile.", ephemeral=True)
            return
        if team_data["game_state"] == 2:
            await interaction.response.send_message(f"You cannot skip a boss tile.", ephemeral=True)
            return
        
        # Check the player's ranking
        skip_timer_hours = 12
        ranking = await self.session.get(ApiUrls.TEAM_PLACEMENT.format(id=team_data["_id"]))
        if ranking.status == 200:
            rank_data = await ranking.json()
            if rank_data.get('placement', 9999) == 1:
                await interaction.response.send_message(f"{Emojis.SKIP} You cannot skip tiles when your team is in 1st place.", ephemeral=True)
                return
            else:
                if rank_data.get('placement', 9999) in [2, 3, 4]:
                    skip_timer_hours = 16

        async with self.session.get(ApiUrls.TEAM_LAST_ROLLED.format(id=team_data["_id"])) as resp:
            if resp.status == 200:
                last_rolled_data = await resp.json()
                last_rolled_str = last_rolled_data.get('last_rolled')

                last_rolled_at = parser.isoparse(last_rolled_str)
                current_time = discord.utils.utcnow()

                time_difference = current_time - last_rolled_at

                if time_difference.total_seconds() < skip_timer_hours * 3600:
                    # Prefer the pre-formatted timestamp if available
                    next_allowed_time = last_rolled_at + timedelta(hours=skip_timer_hours)
                    next_allowed_epoch = int(next_allowed_time.timestamp())
                    discord_relative = f"<t:{next_allowed_epoch}:R>"
                    await interaction.response.send_message(
                        f"You can only skip a tile once every {skip_timer_hours} hours. Wait until: {discord_relative}",
                        ephemeral=True
                    )
                    return
                # Proceed to skip the tile
                async with self.session.post(ApiUrls.TEAM_ADVANCE_TILE.format(id=team_data["_id"])):
                    await interaction.response.send_message("You have skipped the current tile. Use `/board` to see your new board.")

async def setup(bot: commands):
    await bot.add_cog(PlayerCog(bot))