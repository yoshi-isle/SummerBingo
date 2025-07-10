import discord
import io
import aiohttp
from discord import Color, Embed, app_commands
from discord.ext import commands
from constants import ApiUrls, DiscordIDs, Emojis
from storyline import StoryLine
from enums.gamestate import GameState
from utils.count_keys import count_w1_keys
from utils.post_board import post_team_board
from embeds import build_w1_boss_board_embed, build_team_board_embed, build_w1_key_board_embed, build_w2_boss_board_embed, build_w2_key_board_embed, build_storyline_embed

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    @app_commands.command(name="admin_register_team", description="(Admin) Registers a new team")
    @app_commands.checks.has_role("Admin")
    async def register_team(self, interaction: discord.Interaction, users: str, team_name: str):
        try:
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
            async with self.session.post(ApiUrls.TEAM, json=data) as resp:
                if resp.status == 201:
                    team = await resp.json()
                    await interaction.response.send_message(f"Team '{team_name}' registered!\n{team}", ephemeral=True)
                    
                    embed, file = build_storyline_embed(StoryLine.W1_START)
                    w1start_msg = await interaction.channel.send(embed=embed, file=file)

                    # Send the first team board, too
                    await post_team_board(self.session, team["_id"], interaction.channel, "overworld")

                    try:
                        await w1start_msg.pin()
                    except:
                        pass
                else:
                    error = await resp.text()
                    await interaction.response.send_message(f"Failed to register team\n{error}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error creating team")
            
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Ignore reactions from the bot itself        
        if payload.user_id == self.bot.user.id:
            return
        
        if payload.channel_id != DiscordIDs.PENDING_SUBMISSIONS_CHANNEL_ID:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = guild.get_member(payload.user_id)
        submission = None
        async with self.session.get(ApiUrls.SUBMISSION.format(id=str(message.id))) as resp:
            if resp.status == 200:
                submission = await resp.json()
                if str(payload.emoji) == '✅':
                    try:
                        await self.handle_approval(submission, message, user)
                    except Exception as e:
                        await channel.send(f"{e} An error occured approving the submission")

                if str(payload.emoji) == '❌':
                    try:
                        await self.handle_denial(submission, message, user)
                    except Exception as e:
                        await channel.send(f"{e} An error occured denying the submission")
        if submission == None:
            async with self.session.get(ApiUrls.KEY_SUBMISSION.format(id=str(message.id))) as key_resp:
                if key_resp.status == 200:
                    key_submission = await key_resp.json()
                    if str(payload.emoji) == '✅':
                        try:
                            await self.handle_approval(key_submission, message, user, GameState.KEY)
                        except Exception as e:
                            await channel.send(f"An error occured approving the submission")

                    if str(payload.emoji) == '❌':
                        try:
                            await self.handle_denial(key_submission, message, user, GameState.KEY)
                        except Exception as e:
                            await channel.send(f"An error occured denying the submission")
                else:

                    async with self.session.get(ApiUrls.BOSS_SUBMISSION.format(id=str(message.id))) as boss_resp:
                        if boss_resp.status == 200:
                            boss_submission = await boss_resp.json()
                            if str(payload.emoji) == '✅':
                                try:
                                    await self.handle_approval(boss_submission, message, user, GameState.BOSS)
                                except Exception as e:
                                    await channel.send(f"{e} An error occured approving the submission")

                            if str(payload.emoji) == '❌':
                                try:
                                    await self.handle_denial(boss_submission, message, user, GameState.BOSS)
                                except Exception as e:
                                    await channel.send(f"{e} An error occured denying the submission")
                        else:
                            await channel.send(f"Submission not found in database for Message ID {str(message.id)}")
                            return

    @app_commands.command(name="admin_clear_channel", description="(Admin) Deletes all messages in the current channel")
    @app_commands.checks.has_role("Admin")
    async def clear_channel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge()
        await interaction.followup.send("Channel cleared!", ephemeral=True)

    async def handle_approval(self, submission, message, user, GameState=GameState.OVERWORLD):
        async with self.session.get(ApiUrls.TEAM_BY_ID_WITHOUT_DISCORD.format(id=submission['team_id'])) as team_resp:
            team = await team_resp.json()
        current_world = team['current_world']
        approved_channel = message.guild.get_channel(DiscordIDs.APPROVED_SUBMISSIONS_CHANNEL_ID)
        team_channel = message.guild.get_channel(int(submission['team_channel_id']))
        
        pending_message = await team_channel.fetch_message(int(submission['pending_team_embed_id']))
        if pending_message and pending_message.embeds:
            approved_embed = pending_message.embeds[0].copy()
            approved_embed.color = discord.Color.green()
            approved_embed.title = f"Approved by {user.display_name}"
            approved_embed.set_footer(text="")
            approved_embed.description = f"🟢 Status: Approved by {user.mention}."
            await pending_message.edit(embed=approved_embed)
            await message.delete()
            approved_embed.description = f"See the submission in the team's channel here: https://discord.com/channels/{pending_message.guild.id}/{pending_message.channel.id}/{pending_message.id}"
            await approved_channel.send(embed=approved_embed)

        if GameState == GameState.OVERWORLD:
            async with self.session.put(ApiUrls.APPROVE_SUBMISSION.format(id=submission["_id"])) as approve_resp:
                if approve_resp.status == 200:
                    # Advance a tile if the number of submissions is complete
                    if int(team['completion_counter']) <= 1:
                        async with self.session.post(ApiUrls.TEAM_ADVANCE_TILE.format(id=submission['team_id'])) as advance_resp:
                            if advance_resp.status == 200:
                                async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=submission['team_id'])) as resp:
                                    info = await resp.json()
                                    team_data = info["team"]
                                    tile_info = info["tile"]
                                    level_number = info["level_number"]
                                
                                # 0 - Normal Board
                                if info["team"]["game_state"] == 0:
                                    await team_channel.send(embed=Embed(title="Tile complete! Posting your new board:"))
                                    await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
                                # 1 - Key Board (world 1)
                                elif info["team"]["game_state"] == 1 and info["team"]["current_world"] == 1:
                                    embed, file = build_storyline_embed(StoryLine.W1_KEY)
                                    w1_key_msg = await team_channel.send(embed=embed, file=file)
                                    try:
                                        await w1_key_msg.pin()
                                    except:
                                        pass

                                    await post_team_board(self.session, submission['team_id'], team_channel, "w1_key")
                                
                                # 2 - Boss Tile (world 1)
                                elif info["team"]["game_state"] == 2 and info["team"]["current_world"] == 1:
                                    await post_team_board(self.session, submission['team_id'], team_channel, "w1_boss")
                                # Boss Tile (World 2)
                                elif info["team"]["game_state"] == 2 and info["team"]["current_world"] == 2:
                                    embed, file = build_storyline_embed(StoryLine.W2_BOSS)
                                    w2_boss_msg = await team_channel.send(embed=embed, file=file)
                                    try:
                                        await w2_boss_msg.pin()
                                    except:
                                        pass
                                    await post_team_board(self.session, submission['team_id'], team_channel, "w2_boss")
                                # Boss Tile (World 3)
                                elif info["team"]["game_state"] == 2 and info["team"]["current_world"] == 3:
                                    embed, file = build_storyline_embed(StoryLine.W3_BOSS)
                                    w3_boss_msg = await team_channel.send(embed=embed, file=file)
                                    try:
                                        await w3_boss_msg.pin()
                                    except:
                                        pass
                                    await post_team_board(self.session, submission['team_id'], team_channel, "w3_boss")
                                # Key Board (world 3)
                                elif info["team"]["game_state"] == 1 and info["team"]["current_world"] == 3:
                                    w3_key_msg = await team_channel.send(embed=Embed(description=f"{Emojis.TRIAL_COMPLETE} The team come across a frozen brazier. Maybe completing the trial will light it..."))
                                    await post_team_board(self.session, submission['team_id'], team_channel, "w3_key")

                            else:
                                error = await advance_resp.text()
                                await message.channel.send(f"Failed to advance tile: {error}")
                    else:
                        async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=submission['team_id'])) as team_resp:
                            board_information = await team_resp.json()
                        receipt = Embed(title="Tile Progress Updated!", description=f"Currently at: {team['completion_counter']-1}/{board_information['tile']['completion_counter']}")
                        receipt.color = Color.green()
                        await team_channel.send(embed=receipt)
                if approve_resp.status == 208:
                    await approved_channel.send(embed=Embed(title="Admin Note: Submission was outdated so system deleted it. (No harm done)"))
        elif GameState == GameState.KEY:
            async with self.session.put(ApiUrls.APPROVE_KEY_SUBMISSION.format(id=submission["_id"], key_id=submission["key_option"])) as approve_resp:
                if approve_resp.status == 200:
                    updated_team = await approve_resp.json()
                    team = updated_team["team"]

                    # World 1 - 3 keys complete, so advance
                    if team["current_world"] == 1:
                        if count_w1_keys(team) >= 3:
                            embed, file = build_storyline_embed(StoryLine.W1_BOSS)
                            w1_boss_msg = await team_channel.send(embed=embed, file=file)
                            try:
                                await w1_boss_msg.pin()
                            except:
                                pass
                            async with self.session.put(ApiUrls.ADVANCE_TO_BOSS_TILE.format(id=team["_id"])) as approve_resp:
                                await post_team_board(self.session, submission['team_id'], team_channel, "w1_boss")
                                return
                        if team[f"w{current_world}key{submission['key_option']}_completion_counter"] <= 0:
                            await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!"))
                            await post_team_board(self.session, submission['team_id'], team_channel, "w1_key")
                        else:
                            key_option = submission['key_option']
                            remaining = team[f'w{current_world}key{key_option}_completion_counter']
                            await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on trial # {key_option}. You still need to complete {remaining} more submissions to complete it."))
                    
                    # World 2 - Pick-a-path
                    key_option = submission["key_option"]
                    if team["current_world"] == 2:
                        # Initial trial selection
                        remaining = team[f'w2key{key_option}_completion_counter']
                        if team["w2_path_chosen"] == 0:
                            if team[f"w2key{key_option}_completion_counter"] <= 0:
                                await self.session.put(ApiUrls.TEAM_TRAVERSE_W2_TRIAL.format(id=team["_id"], option=key_option))
                                await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!\nYour team hears a click, and enters the nearby door..."))
                                await post_team_board(self.session, submission['team_id'], team_channel, "w2_key")
                            else:
                                await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on the trial. You still need to complete {remaining} more submissions to complete it."))
                        # Left path
                        elif team["w2_path_chosen"] == -1:
                            if team[f"w2key{key_option}_completion_counter"] <= 0:
                                await self.session.put(ApiUrls.TEAM_TRAVERSE_W2_TRIAL.format(id=team["_id"], option=key_option))
                                await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!\nYour team hears a click, and enters the nearby door..."))
                                await post_team_board(self.session, submission['team_id'], team_channel, "w2_key")
                            else:
                                await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on the trial. You still need to complete {remaining} more submissions to complete it."))
                        # Right path
                        elif team["w2_path_chosen"] == 1:
                            if team[f"w2key{key_option}_completion_counter"] <= 0:
                                await self.session.put(ApiUrls.TEAM_TRAVERSE_W2_TRIAL.format(id=team["_id"], option=key_option))
                                await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!\nYour team hears a click, and enters the nearby door..."))
                                await post_team_board(self.session, submission['team_id'], team_channel, "w2_key")
                            else:
                                await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on the trial. You still need to complete {remaining} more submissions to complete it."))
                        # Top of the path
                        elif team["w2_path_chosen"] == 2:
                            if team[f"w2key{key_option}_completion_counter"] <= 0:
                                embed, file = build_storyline_embed(StoryLine.W2_KEY_COMPLETE)
                                w2_trial_completed = await team_channel.send(embed=embed, file=file)
                                try:
                                    await w2_trial_completed.pin()
                                except:
                                    pass
                                await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!"))
                                await self.session.put(ApiUrls.TEAM_COMPLETE_W2_TRIAL.format(id=team["_id"]))
                                await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
                            else:
                                await team_channel.send(f"progress {team[f'w2key{key_option}_completion_counter']} remaining")
                    # World 3 - Light a brazier
                    elif team["current_world"] == 3:
                        if team[f"w3key{key_option}_completion_counter"] <= 0:
                            await self.session.put(ApiUrls.TEAM_COMPLETE_W3_TRIAL.format(id=team["_id"], brazier_number=team["w3_braziers_lit"]))
                            await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!"))
                            await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
                        else:
                            remaining = team[f'w3key{key_option}_completion_counter']
                            await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on trial # {key_option}. You still need to complete {remaining} more submissions to complete it."))

                elif approve_resp.status == 404:
                    await team_channel.send("Key submission not found.")
                else:
                    error = await approve_resp.text()
                    await team_channel.send(f"Failed to approve key submission: {error}")
        elif GameState == GameState.BOSS:
            async with self.session.put(ApiUrls.APPROVE_BOSS_SUBMISSION.format(id=submission["_id"])) as approve_resp:
                if approve_resp.status == 200:
                    updated_team = await approve_resp.json()
                    team = updated_team["team"]
                    world = team["current_world"]
                    if int(team[f"w{world}boss_completion_counter"]) <= 0:
                        await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Your team completed the boss tile!"))
                        async with self.session.put(ApiUrls.ADVANCE_TO_NEXT_WORLD.format(id=team["_id"])) as adv_world_resp:
                            if team["current_world"] == 1:
                                embed, file = build_storyline_embed(StoryLine.W2_START)
                                w2_start_msg = await team_channel.send(embed=embed, file=file)
                                try:
                                    await w2_start_msg.pin()
                                except:
                                    pass
                                await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
                                return
                            elif team["current_world"] == 2:
                                embed, file = build_storyline_embed(StoryLine.W3_START)
                                w3_start_msg = await team_channel.send(embed=embed, file=file)
                                try:
                                    await w3_start_msg.pin()
                                except:
                                    pass
                                await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
                                return
                            elif team["current_world"] == 3:
                                embed, file = build_storyline_embed(StoryLine.W4_START)
                                w4_start_msg = await team_channel.send(embed=embed, file=file)
                                try:
                                    await w4_start_msg.pin()
                                except:
                                    pass
                                await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
                                return

    async def handle_denial(self, submission, message, user, GameState=GameState.OVERWORLD): 
        async with self.session.get(ApiUrls.TEAM_BY_ID_WITHOUT_DISCORD.format(id=submission['team_id'])) as team_resp:
            team = await team_resp.json()
        current_world = team['current_world']
        team_channel = message.guild.get_channel(int(submission['team_channel_id']))
        pending_message = await team_channel.fetch_message(int(submission['pending_team_embed_id']))
        if pending_message and pending_message.embeds:
            denied_embed = pending_message.embeds[0].copy()
            denied_embed.color = discord.Color.red()
            denied_embed.title = f"Denied by {user.display_name}"
            denied_embed.set_footer(text="")
            denied_embed.description = f"🔴 Status: Denied by {user.mention}."
            await pending_message.edit(embed=denied_embed)
            await message.delete()
            denied_embed.description = f"See the submission in the team's channel here: https://discord.com/channels/{pending_message.guild.id}/{pending_message.channel.id}/{pending_message.id}"
            denied_channel = message.guild.get_channel(DiscordIDs.DENIED_SUBMISSIONS_CHANNEL_ID)
            await denied_channel.send(embed=denied_embed)


    @app_commands.command(name="admin_force_complete", description="(Admin) Force complete current tile and advance to next")
    @app_commands.checks.has_role("Admin")
    async def force_complete(self, interaction: discord.Interaction, user: discord.User):
        try:
            # Get team data for the user
            async with self.session.get(ApiUrls.TEAM_BY_ID.format(id=user.id)) as resp:
                if resp.status == 200:
                    team_data = await resp.json()
                else:
                    await interaction.response.send_message(f"User is not part of a team", ephemeral=True)
                    return

            team_channel = interaction.guild.get_channel(int(team_data['discord_channel_id']))
            if not team_channel:
                await interaction.response.send_message(f"Could not find team channel", ephemeral=True)
                return

            # Force advance the tile
            async with self.session.post(ApiUrls.TEAM_ADVANCE_TILE.format(id=team_data['_id'])) as advance_resp:
                if advance_resp.status == 200:
                    async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=team_data['_id'])) as resp:
                        info = await resp.json()
                        team_data = info["team"]
                        tile_info = info["tile"]
                        level_number = info["level_number"]
                    
                    # 0 - Normal Board
                    if info["team"]["game_state"] == 0:
                        await post_team_board(self.session, team_data['_id'], team_channel, "overworld")
                    # Key Board (world 1)
                    elif info["team"]["game_state"] == 1 and info["team"]["current_world"] == 1:
                        embed, file = build_storyline_embed(StoryLine.W1_KEY)
                        w1_key_msg = await team_channel.send(embed=embed, file=file)
                        try:
                            await w1_key_msg.pin()
                        except:
                            pass

                        await post_team_board(self.session, team_data['_id'], team_channel, "w1_key")
                    
                    # Key Board (world 2)
                    elif info["team"]["game_state"] == 1 and info["team"]["current_world"] == 2:
                        embed, file = build_storyline_embed(StoryLine.W2_KEY)
                        w2_key_msg = await team_channel.send(embed=embed, file=file)
                        try:
                            await w2_key_msg.pin()
                        except:
                            pass

                        await post_team_board(self.session, team_data['_id'], team_channel, "w2_key")
                    
                    # Boss Tile (world 1)
                    elif info["team"]["game_state"] == 2 and info["team"]["current_world"] == 1:
                        await post_team_board(self.session, team_data['_id'], team_channel, "w1_boss")

                    # Boss Tile (world 2)
                    elif info["team"]["game_state"] == 2 and info["team"]["current_world"] == 2:
                        embed, file = build_storyline_embed(StoryLine.W2_BOSS)
                        w2_boss_msg = await team_channel.send(embed=embed, file=file)
                        try:
                            await w2_boss_msg.pin()
                        except:
                            pass
                        await post_team_board(self.session, team_data['_id'], team_channel, "w2_boss")
                    await interaction.response.send_message(f"{Emojis.ADMIN} {interaction.user.mention} Force completed tile for {user.mention}'s team - posting new board...")
                else:
                    error = await advance_resp.text()
                    await interaction.response.send_message(f"Failed to advance tile: {error}", ephemeral=True)

        except Exception as e:
            print(f"Error in force_complete: {e}")
            await interaction.response.send_message(f"There was an unknown error. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>", ephemeral=True)

    @app_commands.command(name="admin_view_a_board", description="(Admin) View a player's board.")
    @app_commands.checks.has_role("Admin")
    async def view_board(self, interaction: discord.Interaction, user: discord.User):
        try:
            # Guard against viewing board outside of team channel
            async with self.session.get(ApiUrls.TEAM_BY_ID.format(id=user.id)) as resp:
                if resp.status == 200:
                    team_data = await resp.json()
                else:
                    await interaction.response.send_message(f"It looks this user is not part of a team", ephemeral=True)
                    return

            # Grab board information
            async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=team_data["_id"])) as resp:
                if resp.status == 200:
                    board_information = await resp.json()
                    await self.send_team_board_to_interaction(interaction, team_data, board_information)
                else:
                    await interaction.response.send_message(f"There was an error getting the user's board information.", ephemeral=True)
                    return

        except Exception as e:
            print(f"Error in view_board: {e}")
            await interaction.response.send_message(f"There was an unknown error. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")

    async def send_team_board_to_interaction(self, interaction: discord.Interaction, team_data: dict, board_information: dict):
        """Send a team board as an interaction response"""
        try:
            async with self.session.get(ApiUrls.IMAGE_BOARD.format(id=team_data["_id"])) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                    
                    # Determine embed type based on game state
                    if int(team_data["game_state"]) == 0:
                        embed = build_team_board_embed(team_data, board_information["tile"], board_information["level_number"])
                    elif int(team_data["game_state"]) == 1 and int(team_data["current_world"]) == 1:
                        embed = build_w1_key_board_embed(team_data)
                    elif int(team_data["game_state"]) == 1 and int(team_data["current_world"]) == 2:
                        embed = build_w2_key_board_embed(team_data)
                    elif int(team_data["game_state"]) == 1 and int(team_data["current_world"]) == 1:
                        embed = build_w1_boss_board_embed(team_data)
                    elif int(team_data["game_state"]) == 1 and int(team_data["current_world"]) == 2:
                        embed = build_w2_boss_board_embed(team_data)
                    else:
                        embed = build_team_board_embed(team_data, board_information["tile"], board_information["level_number"])
                    
                    embed.set_image(url="attachment://team_board.png")
                    await interaction.response.send_message(embed=embed, file=file)
                else:
                    await interaction.response.send_message(f"There was an error getting the user's board image.")
        except Exception as e:
            print(f"Error in send_team_board_to_interaction: {e}")
            await interaction.response.send_message(f"There was an error displaying the board.")

async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))