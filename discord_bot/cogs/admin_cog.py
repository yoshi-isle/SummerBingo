import discord
import io
import aiohttp
from discord import Color, Embed, app_commands
from discord.ext import commands
from constants import ApiUrls, DiscordIDs, Emojis
from enums.gamestate import GameState
from utils.count_keys import count_w1_keys
from embeds import build_team_board_embed, build_key_board_embed

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    @app_commands.command(name="register_team", description="Registers a new team")
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
                else:
                    error = await resp.text()
                    await interaction.response.send_message(f"Failed to register team\n{error}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error creating team {e}. Please try again")
            
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
                    pass
        if submission == None:
            async with self.session.get(ApiUrls.KEY_SUBMISSION.format(id=str(message.id))) as key_resp:
                if key_resp.status == 200:
                    key_submission = await key_resp.json()
                    if str(payload.emoji) == '✅':
                        try:
                            await self.handle_approval(key_submission, message, user, GameState.KEY)
                        except Exception as e:
                            await channel.send(f"{e} An error occured approving the submission")

                    if str(payload.emoji) == '❌':
                        pass
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
                                pass
                        else:
                            await channel.send(f"Submission not found in database for Message ID {str(message.id)}")
                            return

    @app_commands.command(name="clear_channel", description="Deletes all messages in the current channel")
    @app_commands.checks.has_role("Admin")
    async def clear_channel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge()
        await interaction.followup.send("Channel cleared!", ephemeral=True)

    async def handle_approval(self, submission, message, user, GameState=GameState.OVERWORLD):
        async with self.session.get(ApiUrls.TEAM_BY_ID_WITHOUT_DISCORD.format(id=submission['team_id'])) as team_resp:
            team = await team_resp.json()

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
                                    await team_channel.send(embed=Embed(title="Submission approved! Here's your new board:"))
                                    async with self.session.get(ApiUrls.IMAGE_BOARD.format(id=submission['team_id'])) as image_resp:
                                        image_data = await image_resp.read()
                                        file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                                        embed = build_team_board_embed(team_data, tile_info, level_number)
                                        embed.set_image(url="attachment://team_board.png")
                                        await team_channel.send(embed=embed, file=file)
                                    
                                # 1 - Key Board
                                elif info["team"]["game_state"] == 1:
                                    await team_channel.send(embed=Embed(title=f"{Emojis.DUNGEON} Your team enters into a dungeon..."))
                                    async with self.session.get(ApiUrls.IMAGE_BOARD.format(id=submission['team_id'])) as image_resp:
                                        image_data = await image_resp.read()
                                        file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                                        embed = build_key_board_embed(team_data)
                                        embed.set_image(url="attachment://team_board.png")
                                        await team_channel.send(embed=embed, file=file)
                                
                                # 2 - Boss Tile
                                elif info["team"]["game_state"] == 2:
                                    await team_channel.send(embed=Embed(title=f"{Emojis.DUNGEON} Your team enters into the boss lair..."))
                                    async with self.session.get(ApiUrls.IMAGE_BOARD.format(id=submission['team_id'])) as image_resp:
                                        image_data = await image_resp.read()
                                        file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                                        embed = build_key_board_embed(team_data)
                                        embed.set_image(url="attachment://team_board.png")
                                        await team_channel.send(embed=embed, file=file)
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
                    await approved_channel.send(embed=Embed(title="Submission was outdated so nothing happened. (No harm done)"))
        elif GameState == GameState.KEY:
            async with self.session.put(ApiUrls.APPROVE_KEY_SUBMISSION.format(id=submission["_id"], key_id=submission["key_option"])) as approve_resp:
                if approve_resp.status == 200:
                    updated_team = await approve_resp.json()
                    team = updated_team["team"]
                    if count_w1_keys(team) >= 3:
                        await team_channel.send(embed=Embed(title=f"Your team arrives at the boss..."))
                        async with self.session.put(ApiUrls.ADVANCE_TO_BOSS_TILE.format(id=team["_id"])) as approve_resp:
                            return
                    if team[f"w1key{submission['key_option']}_completion_counter"] <= 0:
                        await team_channel.send(embed=Embed(title=f"{Emojis.KEY} Key acquired!"))
                    else:
                        key_option = submission['key_option']
                        remaining = team[f'w1key{key_option}_completion_counter']
                        await team_channel.send(embed=Embed(title=f"{Emojis.KEY_NOT_OBTAINED} Progress updated on key tile {key_option}. You still need to complete {remaining} more submissions to obtain this key."))
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
                        async with self.session.put(ApiUrls.ADVANCE_TO_NEXT_WORLD.format(id=team["_id"])) as approve_resp:
                            await team_channel.send(embed=Embed(title=f"Your team completed world {world}!"))

async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))