"""
Admin Cog for Summer Bingo Discord Bot

This cog handles administrative functions including:
- Team registration
- Submission approval/denial via reactions
- Force completing tiles
- Viewing team boards

Refactored for better maintainability:
- Extracted helper methods to reduce nesting
- Separated concerns into focused methods
- Improved error handling and code readability
- Used type hints for better code documentation
"""

import discord
import io
import aiohttp
from typing import Optional, Dict, Any
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

    # Helper methods for cleaner code
    async def _get_team_data(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team data by ID"""
        async with self.session.get(ApiUrls.TEAM_BY_ID_WITHOUT_DISCORD.format(id=team_id)) as resp:
            return await resp.json() if resp.status == 200 else None

    async def _pin_message_safely(self, message: discord.Message) -> None:
        """Pin a message, ignoring any errors"""
        try:
            await message.pin()
        except:
            pass

    async def _update_submission_embed(self, pending_message: discord.Message, user: discord.Member, 
                                     status: str, color: discord.Color) -> discord.Embed:
        """Update submission embed with approval/denial status"""
        if not (pending_message and pending_message.embeds):
            return None
        
        embed = pending_message.embeds[0].copy()
        embed.color = color
        embed.title = f"{status} by {user.display_name}"
        embed.set_footer(text="")
        embed.description = f"{'🟢' if status == 'Approved' else '🔴'} Status: {status} by {user.mention}."
        await pending_message.edit(embed=embed)
        return embed

    async def _send_storyline_and_pin(self, channel: discord.TextChannel, storyline: StoryLine) -> None:
        """Send storyline embed and pin it"""
        embed, file = build_storyline_embed(storyline)
        msg = await channel.send(embed=embed, file=file)
        await self._pin_message_safely(msg)

    async def _handle_game_state_transition(self, team_data: Dict, submission: Dict, team_channel: discord.TextChannel) -> None:
        """Handle game state transitions after tile advancement"""
        game_state = team_data["game_state"]
        current_world = team_data["current_world"]
        team_id = submission['team_id']

        # Normal overworld board
        if game_state == 0:
            await team_channel.send(embed=Embed(title="Tile complete! Posting your new board:"))
            await post_team_board(self.session, team_id, team_channel, "overworld")
            return

        # Key boards
        if game_state == 1:
            if current_world == 1:
                await self._send_storyline_and_pin(team_channel, StoryLine.W1_KEY)
                await post_team_board(self.session, team_id, team_channel, "w1_key")
            elif current_world == 2:
                await self._send_storyline_and_pin(team_channel, StoryLine.W2_KEY)
                await post_team_board(self.session, team_id, team_channel, "w2_key")
            elif current_world == 3:
                await team_channel.send(embed=Embed(
                    description=f"{Emojis.TRIAL_COMPLETE} The team discovers a frozen brazier. Maybe completing the trial will light it?",
                    color=discord.Color.blue()
                ))
                await post_team_board(self.session, team_id, team_channel, "w3_key")
            elif current_world == 4:
                await self._send_storyline_and_pin(team_channel, StoryLine.W4_KEY)
                await post_team_board(self.session, team_id, team_channel, "w4_key")
            return

        # Boss boards
        if game_state == 2:
            board_type = f"w{current_world}_boss"
            if current_world == 1:
                await post_team_board(self.session, team_id, team_channel, board_type)
            elif current_world == 2:
                await self._send_storyline_and_pin(team_channel, StoryLine.W2_BOSS)
                await post_team_board(self.session, team_id, team_channel, board_type)
            elif current_world == 3:
                await self._send_storyline_and_pin(team_channel, StoryLine.W3_BOSS)
                await post_team_board(self.session, team_id, team_channel, board_type)
            elif current_world == 4:
                await self._send_storyline_and_pin(team_channel, StoryLine.W4_BOSS)
                await post_team_board(self.session, team_id, team_channel, board_type)

    @app_commands.command(name="admin_register_team", description="(Admin) Registers a new team")
    @app_commands.checks.has_role("Admin")
    async def register_team(self, interaction: discord.Interaction, users: str, team_name: str):
        try:
            member_ids = [int(u.strip('<@!>')) for u in users.split() if u.startswith('<@')]
            players = [{"discord_id": str(uid), "runescape_accounts": []} for uid in member_ids]
            
            data = {
                "team_name": team_name,
                "players": players,
                "discord_channel_id": str(interaction.channel.id)
            }
            
            async with self.session.post(ApiUrls.TEAM, json=data) as resp:
                if resp.status == 201:
                    team = await resp.json()
                    await interaction.response.send_message(f"Team '{team_name}' registered!\n{team}", ephemeral=True)
                    
                    # Send storyline and initial board
                    await self._send_storyline_and_pin(interaction.channel, StoryLine.W1_START)
                    await post_team_board(self.session, team["_id"], interaction.channel, "overworld")
                else:
                    error = await resp.text()
                    await interaction.response.send_message(f"Failed to register team\n{error}", ephemeral=True)
                    
        except Exception as e:
            await interaction.response.send_message(f"Error creating team: {e}", ephemeral=True)
            
    async def _get_submission_by_type(self, message_id: str) -> tuple[Optional[Dict], GameState]:
        """Try to get submission by checking different types"""
        # Try regular submission first
        async with self.session.get(ApiUrls.SUBMISSION.format(id=message_id)) as resp:
            if resp.status == 200:
                return await resp.json(), GameState.OVERWORLD
        
        # Try key submission
        async with self.session.get(ApiUrls.KEY_SUBMISSION.format(id=message_id)) as resp:
            if resp.status == 200:
                return await resp.json(), GameState.KEY
        
        # Try boss submission
        async with self.session.get(ApiUrls.BOSS_SUBMISSION.format(id=message_id)) as resp:
            if resp.status == 200:
                return await resp.json(), GameState.BOSS
        
        return None, None

    async def _handle_reaction_error(self, channel: discord.TextChannel, action: str, error: Exception) -> None:
        """Handle errors during reaction processing"""
        await channel.send(f"An error occurred {action} the submission: {error}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Early returns for invalid reactions
        if (payload.user_id == self.bot.user.id or 
            payload.channel_id != DiscordIDs.PENDING_SUBMISSIONS_CHANNEL_ID):
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)
        
        # Get submission data
        submission, game_state = await self._get_submission_by_type(str(message.id))
        if not submission:
            await channel.send(f"Submission not found in database for Message ID {message.id}")
            return
        
        # Handle reactions
        try:
            if emoji == '✅':
                await self.handle_approval(submission, message, user, game_state)
            elif emoji == '❌':
                await self.handle_denial(submission, message, user, game_state)
        except Exception as e:
            action = "approving" if emoji == '✅' else "denying"
            await self._handle_reaction_error(channel, action, e)

    @app_commands.command(name="admin_clear_channel", description="(Admin) Deletes all messages in the current channel")
    @app_commands.checks.has_role("Admin")
    async def clear_channel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge()
        await interaction.followup.send("Channel cleared!", ephemeral=True)

    async def _update_embed_status(self, submission: Dict, message: discord.Message, 
                                 user: discord.Member, approved: bool) -> None:
        """Update submission embed and handle channel routing"""
        team_channel = message.guild.get_channel(int(submission['team_channel_id']))
        pending_message = await team_channel.fetch_message(int(submission['pending_team_embed_id']))
        
        status = "Approved" if approved else "Denied"
        color = discord.Color.green() if approved else discord.Color.red()
        
        embed = await self._update_submission_embed(pending_message, user, status, color)
        if not embed:
            return
            
        await message.delete()
        
        # Send to appropriate channel
        channel_id = DiscordIDs.APPROVED_SUBMISSIONS_CHANNEL_ID if approved else DiscordIDs.DENIED_SUBMISSIONS_CHANNEL_ID
        target_channel = message.guild.get_channel(channel_id)
        embed.description = f"See the submission in the team's channel here: https://discord.com/channels/{pending_message.guild.id}/{pending_message.channel.id}/{pending_message.id}"
        await target_channel.send(embed=embed)

    async def _handle_overworld_approval(self, submission: Dict, team: Dict, team_channel: discord.TextChannel) -> None:
        """Handle approval for overworld submissions"""
        async with self.session.put(ApiUrls.APPROVE_SUBMISSION.format(id=submission["_id"])) as approve_resp:
            if approve_resp.status == 200:
                if int(team['completion_counter']) <= 1:
                    await self._advance_tile_and_handle_transition(submission, team_channel)
                else:
                    await self._send_progress_update(submission, team, team_channel)
            elif approve_resp.status == 208:
                approved_channel = team_channel.guild.get_channel(DiscordIDs.APPROVED_SUBMISSIONS_CHANNEL_ID)
                await approved_channel.send(embed=Embed(title="Admin Note: Submission was outdated so system deleted it. (No harm done)"))

    async def _advance_tile_and_handle_transition(self, submission: Dict, team_channel: discord.TextChannel) -> None:
        """Advance tile and handle game state transitions"""
        async with self.session.post(ApiUrls.TEAM_ADVANCE_TILE.format(id=submission['team_id'])) as advance_resp:
            if advance_resp.status == 200:
                async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=submission['team_id'])) as resp:
                    info = await resp.json()
                    await self._handle_game_state_transition(info["team"], submission, team_channel)
            else:
                approved_channel = team_channel.guild.get_channel(DiscordIDs.APPROVED_SUBMISSIONS_CHANNEL_ID)
                await approved_channel.send(embed=Embed(title="Admin Note: Submission was outdated so system deleted it. (No harm done)"))

    async def _send_progress_update(self, submission: Dict, team: Dict, team_channel: discord.TextChannel) -> None:
        """Send progress update for incomplete tiles"""
        async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=submission['team_id'])) as team_resp:
            board_information = await team_resp.json()
        
        current_progress = team['completion_counter'] - 1
        total_required = board_information['tile']['completion_counter']
        
        embed = Embed(
            title="Tile Progress Updated!", 
            description=f"Currently at: {current_progress}/{total_required}",
            color=Color.green()
        )
        await team_channel.send(embed=embed)

    async def _handle_world1_key_approval(self, submission: Dict, team: Dict, team_channel: discord.TextChannel) -> None:
        """Handle World 1 key submission approval"""
        if count_w1_keys(team) >= 3:
            await self._send_storyline_and_pin(team_channel, StoryLine.W1_BOSS)
            async with self.session.put(ApiUrls.ADVANCE_TO_BOSS_TILE.format(id=team["_id"])):
                await post_team_board(self.session, submission['team_id'], team_channel, "w1_boss")
            return

        key_option = submission['key_option']
        current_world = team['current_world']
        
        if team[f"w{current_world}key{key_option}_completion_counter"] <= 0:
            await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!"))
            await post_team_board(self.session, submission['team_id'], team_channel, "w1_key")
        else:
            remaining = team[f'w{current_world}key{key_option}_completion_counter']
            await team_channel.send(embed=Embed(
                title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on trial # {key_option}. You still need to complete {remaining} more submissions to complete it."
            ))

    async def _handle_world2_key_approval(self, submission: Dict, team: Dict, team_channel: discord.TextChannel) -> None:
        """Handle World 2 key submission approval (pick-a-path)"""
        key_option = submission["key_option"]
        remaining = team[f'w2key{key_option}_completion_counter']
        path_chosen = team["w2_path_chosen"]
        
        trial_complete = team[f"w2key{key_option}_completion_counter"] <= 0
        
        if path_chosen in [0, -1, 1]:  # Initial, Left, Right paths
            if trial_complete:
                await self.session.put(ApiUrls.TEAM_TRAVERSE_W2_TRIAL.format(id=team["_id"], option=key_option))
                await team_channel.send(embed=Embed(
                    title=f"{Emojis.TRIAL_COMPLETE} Trial completed!\nYour team hears a click, and enters the nearby door..."
                ))
                await post_team_board(self.session, submission['team_id'], team_channel, "w2_key")
            else:
                await team_channel.send(embed=Embed(
                    title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on the trial. You still need to complete {remaining} more submissions to complete it."
                ))
        elif path_chosen == 2:  # Top of the path
            if trial_complete:
                await self._send_storyline_and_pin(team_channel, StoryLine.W2_KEY_COMPLETE)
                await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!"))
                await self.session.put(ApiUrls.TEAM_COMPLETE_W2_TRIAL.format(id=team["_id"]))
                await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
            else:
                await team_channel.send(f"progress {team[f'w2key{key_option}_completion_counter']} remaining")

    async def _handle_world3_key_approval(self, submission: Dict, team: Dict, team_channel: discord.TextChannel) -> None:
        """Handle World 3 key submission approval (light a brazier)"""
        key_option = submission["key_option"]
        
        if team[f"w3key{key_option}_completion_counter"] <= 0:
            await self.session.put(ApiUrls.TEAM_COMPLETE_W3_TRIAL.format(id=team["_id"], brazier_number=team["w3_braziers_lit"]))
            # Specialty case for final brazier
            if team["w3_braziers_lit"] == 2:
                await self._send_storyline_and_pin(team_channel, StoryLine.W3_TRANSITION_INTO_ZAROS_SANCTUM)
                await post_team_board(self.session, team["_id"], team_channel, "overworld")
                return
            await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} You light a brazier! The frozen door seems to be thawing..."))
            await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
        else:
            remaining = team[f'w3key{key_option}_completion_counter']
            await team_channel.send(embed=Embed(
                title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on trial # {key_option}. You still need to complete {remaining} more submissions to complete it."
            ))
    
    async def _handle_world4_key_approval(self, submission: Dict, team: Dict, team_channel: discord.TextChannel) -> None:
        """Handle World 4 key submission approval (light a brazier)"""
        key_option = submission["key_option"]
        # TODO
        if team[f"w4key5_completion_counter"] <= 0:
            await self.session.put(ApiUrls.TEAM_COMPLETE_W4_TRIAL.format(id=team["_id"]))
            await self._send_storyline_and_pin(team_channel, StoryLine.W4_BOSS)
            await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Trial completed!"))
            await post_team_board(self.session, submission['team_id'], team_channel, "w4_boss")
        else:
            remaining = team[f'w4key{key_option}_completion_counter']
            await team_channel.send(embed=Embed(
                title=f"{Emojis.TRIAL_INCOMPLETE} Progress updated on trial # {key_option}. You still need to complete {remaining} more submissions to complete it."
            ))

    async def _handle_key_approval(self, submission: Dict, team_channel: discord.TextChannel) -> None:
        """Handle key submission approval"""
        async with self.session.put(ApiUrls.APPROVE_KEY_SUBMISSION.format(id=submission["_id"], key_id=submission["key_option"])) as approve_resp:
            if approve_resp.status == 200:
                updated_team = await approve_resp.json()
                team = updated_team["team"]
                current_world = team["current_world"]

                if current_world == 1:
                    await self._handle_world1_key_approval(submission, team, team_channel)
                elif current_world == 2:
                    await self._handle_world2_key_approval(submission, team, team_channel)
                elif current_world == 3:
                    await self._handle_world3_key_approval(submission, team, team_channel)
                elif current_world == 4:
                    await self._handle_world4_key_approval(submission, team, team_channel)

            elif approve_resp.status == 404:
                await team_channel.send("Key submission not found.")
            else:
                error = await approve_resp.text()
                await team_channel.send(f"Failed to approve key submission: {error}")

    async def _handle_boss_approval(self, submission: Dict, team_channel: discord.TextChannel) -> None:
        """Handle boss submission approval"""
        async with self.session.put(ApiUrls.APPROVE_BOSS_SUBMISSION.format(id=submission["_id"])) as approve_resp:
            if approve_resp.status == 200:
                updated_team = await approve_resp.json()
                team = updated_team["team"]
                world = team["current_world"]
                
                if int(team[f"w{world}boss_completion_counter"]) <= 0:
                    # Win the event
                    if world == 4:
                        await team_channel.send(embed=Embed(title=f"Your team won the bingo!!!"))
                        return

                    await team_channel.send(embed=Embed(title=f"{Emojis.TRIAL_COMPLETE} Your team completed the boss tile!"))
                    await self._advance_to_next_world(team, submission, team_channel)

    async def _advance_to_next_world(self, team: Dict, submission: Dict, team_channel: discord.TextChannel) -> None:
        """Advance team to next world after boss completion"""
        async with self.session.put(ApiUrls.ADVANCE_TO_NEXT_WORLD.format(id=team["_id"])):
            current_world = team["current_world"]
            
            storylines = {
                1: StoryLine.W2_START,
                2: StoryLine.W3_START,
                3: StoryLine.W4_START
            }
            
            if current_world in storylines:
                await self._send_storyline_and_pin(team_channel, storylines[current_world])
                await post_team_board(self.session, submission['team_id'], team_channel, "overworld")
    async def handle_approval(self, submission: Dict, message: discord.Message, user: discord.Member, game_state: GameState = GameState.OVERWORLD) -> None:
        """Handle submission approval based on game state"""
        team = await self._get_team_data(submission['team_id'])
        if not team:
            return
            
        team_channel = message.guild.get_channel(int(submission['team_channel_id']))
        await self._update_embed_status(submission, message, user, approved=True)

        # Route to appropriate handler based on game state
        if game_state == GameState.OVERWORLD:
            await self._handle_overworld_approval(submission, team, team_channel)
        elif game_state == GameState.KEY:
            await self._handle_key_approval(submission, team_channel)
        elif game_state == GameState.BOSS:
            await self._handle_boss_approval(submission, team_channel)

    async def handle_denial(self, submission: Dict, message: discord.Message, user: discord.Member, game_state: GameState = GameState.OVERWORLD) -> None:
        """Handle submission denial"""
        await self._update_embed_status(submission, message, user, approved=False)


    async def _get_team_by_user_id(self, user_id: int) -> Optional[Dict]:
        """Get team data by user Discord ID"""
        async with self.session.get(ApiUrls.TEAM_BY_ID.format(id=user_id)) as resp:
            return await resp.json() if resp.status == 200 else None

    async def _handle_force_complete_transition(self, team_data: Dict, team_channel: discord.TextChannel) -> None:
        """Handle game state transitions for force complete"""
        game_state = team_data["game_state"]
        current_world = team_data["current_world"]
        team_id = team_data['_id']

        if game_state == 0:
            await post_team_board(self.session, team_id, team_channel, "overworld")
        elif game_state == 1 and current_world == 1:
            await self._send_storyline_and_pin(team_channel, StoryLine.W1_KEY)
            await post_team_board(self.session, team_id, team_channel, "w1_key")
        elif game_state == 1 and current_world == 2:
            await self._send_storyline_and_pin(team_channel, StoryLine.W2_KEY)
            await post_team_board(self.session, team_id, team_channel, "w2_key")
        elif game_state == 2 and current_world == 1:
            await post_team_board(self.session, team_id, team_channel, "w1_boss")
        elif game_state == 2 and current_world == 2:
            await self._send_storyline_and_pin(team_channel, StoryLine.W2_BOSS)
            await post_team_board(self.session, team_id, team_channel, "w2_boss")
        elif game_state == 1 and current_world == 3:
            await post_team_board(self.session, team_id, team_channel, "overworld")
        elif game_state == 2 and current_world == 3:
            await self._send_storyline_and_pin(team_channel, StoryLine.W3_BOSS)
            await post_team_board(self.session, team_id, team_channel, "w3_boss")
        elif game_state == 1 and current_world == 4:
            await self._send_storyline_and_pin(team_channel, StoryLine.W4_KEY)
            await post_team_board(self.session, team_id, team_channel, "w4_key")
        elif game_state == 2 and current_world == 4:
            await self._send_storyline_and_pin(team_channel, StoryLine.W4_BOSS)
            await post_team_board(self.session, team_id, team_channel, "w4_boss")

    @app_commands.command(name="admin_force_complete", description="(Admin) Force complete current tile and advance to next")
    @app_commands.checks.has_role("Admin")
    async def force_complete(self, interaction: discord.Interaction, user: discord.User):
        try:
            team_data = await self._get_team_by_user_id(user.id)
            if not team_data:
                await interaction.response.send_message("User is not part of a team", ephemeral=True)
                return

            team_channel = interaction.guild.get_channel(int(team_data['discord_channel_id']))
            if not team_channel:
                await interaction.response.send_message("Could not find team channel", ephemeral=True)
                return

            # Force advance the tile
            async with self.session.post(ApiUrls.TEAM_ADVANCE_TILE.format(id=team_data['_id'])) as advance_resp:
                if advance_resp.status == 200:
                    async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=team_data['_id'])) as resp:
                        info = await resp.json()
                        await self._handle_force_complete_transition(info["team"], team_channel)
                    
                    await interaction.response.send_message(
                        f"{Emojis.ADMIN} {interaction.user.mention} Force completed tile for {user.mention}'s team - posting new board..."
                    )
                else:
                    error = await advance_resp.text()
                    await interaction.response.send_message(f"Failed to advance tile: {error}", ephemeral=True)

        except Exception as e:
            print(f"Error in force_complete: {e}")
            await interaction.response.send_message(
                f"There was an unknown error. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>", 
                ephemeral=True
            )

    async def _get_embed_for_board(self, team_data: Dict, board_information: Dict) -> discord.Embed:
        """Get appropriate embed based on game state and world"""
        game_state = int(team_data["game_state"])
        current_world = int(team_data["current_world"])
        
        if game_state == 0:
            return build_team_board_embed(team_data, board_information["tile"], board_information["level_number"])
        elif game_state == 1:
            if current_world == 1:
                return build_w1_key_board_embed(team_data)
            elif current_world == 2:
                return build_w2_key_board_embed(team_data)
        elif game_state == 2:
            if current_world == 1:
                return build_w1_boss_board_embed(team_data)
            elif current_world == 2:
                return build_w2_boss_board_embed(team_data)
        
        # Default fallback
        return build_team_board_embed(team_data, board_information["tile"], board_information["level_number"])

    @app_commands.command(name="admin_view_a_board", description="(Admin) View a player's board.")
    @app_commands.checks.has_role("Admin")
    async def view_board(self, interaction: discord.Interaction, user: discord.User):
        try:
            team_data = await self._get_team_by_user_id(user.id)
            if not team_data:
                await interaction.response.send_message("It looks this user is not part of a team", ephemeral=True)
                return

            # Get board information
            async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=team_data["_id"])) as resp:
                if resp.status == 200:
                    board_information = await resp.json()
                    await self.send_team_board_to_interaction(interaction, team_data, board_information)
                else:
                    await interaction.response.send_message("There was an error getting the user's board information.", ephemeral=True)

        except Exception as e:
            print(f"Error in view_board: {e}")
            await interaction.response.send_message(f"There was an unknown error. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")

    async def send_team_board_to_interaction(self, interaction: discord.Interaction, team_data: Dict, board_information: Dict) -> None:
        """Send a team board as an interaction response"""
        try:
            async with self.session.get(ApiUrls.IMAGE_BOARD.format(id=team_data["_id"])) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                    
                    embed = await self._get_embed_for_board(team_data, board_information)
                    embed.set_image(url="attachment://team_board.png")
                    await interaction.response.send_message(embed=embed, file=file)
                else:
                    await interaction.response.send_message("There was an error getting the user's board image.")
        except Exception as e:
            print(f"Error in send_team_board_to_interaction: {e}")
            await interaction.response.send_message("There was an error displaying the board.")

async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))