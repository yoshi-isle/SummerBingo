import discord
import io
import aiohttp
from discord import Color, Embed, app_commands
from discord.ext import commands
from constants import ApiUrls, DiscordIDs
from embeds import build_team_board_embed

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
            else:
                await channel.send(f"Submission not found in database for Message ID {str(message.id)}")

        if str(payload.emoji) == '✅':
            try:
                await self.handle_approval(submission, message, user)
            except Exception as e:
                await channel.send(f"{e} An error occured approving the submission")

        if str(payload.emoji) == '❌':
            pass

    @app_commands.command(name="clear_channel", description="Deletes all messages in the current channel")
    @app_commands.checks.has_role("Admin")
    async def clear_channel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge()
        await interaction.followup.send("Channel cleared!", ephemeral=True)
    
    async def handle_approval(self, submission, message, user):
        async with self.session.put(ApiUrls.APPROVE_SUBMISSION.format(id=submission["_id"])) as approve_resp:
            if approve_resp.status == 200:
                # Send a copy to the approved submissions channel
                approved_channel = message.guild.get_channel(DiscordIDs.APPROVED_SUBMISSIONS_CHANNEL_ID)
                team_channel = message.guild.get_channel(int(submission['team_channel_id']))

                # Get pending embed from submission["pending_team_embed_id"]
                pending_message = await team_channel.fetch_message(int(submission['pending_team_embed_id']))
                if pending_message and pending_message.embeds:
                    # Update the embed with approval information
                    approved_embed = pending_message.embeds[0].copy()
                    approved_embed.color = discord.Color.green()
                    approved_embed.title = f"Approved by {user.display_name}"
                    approved_embed.set_footer(text="")
                    approved_embed.description = f"🟢 Status: Approved by {user.mention}."
                    # Edit the original message in the team channel
                    await pending_message.edit(embed=approved_embed)
                
                    # Copy all embeds from the original message, updating the title
                    if message.embeds:
                        for embed in message.embeds:
                            new_embed = embed.copy()
                            new_embed.color = discord.Color.green()
                            new_embed.title = f"Approved by {user.display_name}"
                            new_embed.set_footer(text="")

                            await approved_channel.send(embed=new_embed)
                
                # Delete the original message
                await message.delete()

                # Get the team object from the API
                team = []
                async with self.session.get(ApiUrls.TEAM_BY_ID_WITHOUT_DISCORD.format(id=submission['team_id'])) as team_resp:
                    if team_resp.status == 200:
                        team = await team_resp.json()
                    else:
                        await team_channel.send(f"Failed to fetch team information. Please contact <@{DiscordIDs.TANGY_DISCORD_ID}>")

                # Advance a tile if the number of submissions is complete
                if int(team['completion_counter']) <= 0:
                    async with self.session.post(ApiUrls.TEAM_ADVANCE_TILE.format(id=submission['team_id'])) as advance_resp:
                        if advance_resp.status == 200:
                            await team_channel.send(embed=Embed(title="Submission approved! Here's your new board:"))
                            # Send the new board embed with image using build_team_board_embed
                            # Fetch team data, tile info, and team level data
                            try:
                                async with self.session.get(ApiUrls.TEAM_BY_ID_WITHOUT_DISCORD.format(id=submission['team_id'])) as team_resp:
                                    if team_resp.status == 200:
                                        team_data = await team_resp.json()
                                    else:
                                        team_data = None
                                async with self.session.get(ApiUrls.TEAM_CURRENT_TILE_WITHOUT_DISCORD.format(id=submission['team_id'])) as tile_resp:
                                    if tile_resp.status == 200:
                                        tile_info = await tile_resp.json()
                                    else:
                                        tile_info = None
                                async with self.session.get(ApiUrls.TEAM_LEVEL_NUMBER_WITHOUT_DISCORD.format(id=submission['team_id'])) as level_resp:
                                    if level_resp.status == 200:
                                        team_level_data = await level_resp.json()
                                    else:
                                        team_level_data = None
                                async with self.session.get(ApiUrls.IMAGE_BOARD_BY_TEAM_ID.format(id=submission['team_id'])) as image_resp:
                                    if image_resp.status == 200:
                                        image_data = await image_resp.read()
                                        file = discord.File(io.BytesIO(image_data), filename="team_board.png")
                                        if team_data and tile_info and team_level_data:
                                            embed = build_team_board_embed(team_data, tile_info, team_level_data)
                                            embed.set_image(url="attachment://team_board.png")
                                            await team_channel.send(embed=embed, file=file)
                            except Exception as e:
                                print(f"Error sending new board embed: {e}")
                        else:
                            error = await advance_resp.text()
                            await message.channel.send(f"Failed to advance tile: {error}")
                else:
                    async with self.session.get(ApiUrls.TEAM_BOARD_INFORMATION_WITHOUT_DISCORD.format(id=submission['team_id'])) as team_resp:
                        board_information = await team_resp.json()
                    receipt = Embed(title="Tile Progress Updated!", description=f"Currently at: {team['completion_counter']}/{board_information['tile']['completion_counter']}")
                    receipt.color = Color.green()
                    await team_channel.send(embed=receipt)
            if approve_resp.status == 208:
                approved_channel = message.guild.get_channel(DiscordIDs.APPROVED_SUBMISSIONS_CHANNEL_ID)
                await approved_channel.send("This submission is outdated so nothing happened. (No harm done)")



async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))