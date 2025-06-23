import io
import discord
from discord.ext import commands
from discord import Embed, app_commands
import aiohttp
import os
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
                    await interaction.response.send_message(f"Team '{team_name}' registered!", ephemeral=True)
                else:
                    error = await resp.text()
                    await interaction.response.send_message(f"Failed to register team: {error}", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Error creating team {e}. Please try again")
            
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        print("Raw reaction added:", payload.emoji, "by", payload.user_id)
        # Ignore reactions from the bot itself
        if payload.user_id == self.bot.user.id:
            return

        # Only handle reactions in the pending submissions channel
        if payload.channel_id != DiscordIDs.PENDING_SUBMISSIONS_CHANNEL_ID:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception as e:
            print(f"Failed to fetch message: {e}")
            return
        user = guild.get_member(payload.user_id)
        if not user:
            try:
                user = await guild.fetch_member(payload.user_id)
            except Exception as e:
                print(f"Failed to fetch user: {e}")
                return

        message_id = str(message.id)
        async with self.session.get(ApiUrls.SUBMISSION.format(id=message_id)) as resp:
            if resp.status == 200:
                submission = await resp.json()
                # Approve submission if reaction is ✅
                if str(payload.emoji) == '✅':
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
                            
                            if approved_channel:
                                # Copy all embeds from the original message, updating the title
                                if message.embeds:
                                    for embed in message.embeds:
                                        new_embed = embed.copy()
                                        new_embed.color = discord.Color.green()
                                        new_embed.title = f"Approved by {user.display_name}"
                                        new_embed.set_footer(text="")

                                        await approved_channel.send(embed=new_embed)
                                else:
                                    await approved_channel.send(content=message.content)
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
                            error = await approve_resp.text()
                            await channel.send(f"Failed to approve submission: {error}")
                # Reject submission if reaction is ❌
                if str(payload.emoji) == '❌':
                    async with self.session.put(ApiUrls.DENY_SUBMISSION.format(id=submission["_id"])) as deny_resp:
                        if deny_resp.status == 200:
                            team_channel = message.guild.get_channel(int(submission['team_channel_id']))
                            # Get pending embed from submission["pending_team_embed_id"]
                            pending_message = await team_channel.fetch_message(int(submission['pending_team_embed_id']))
                            if pending_message and pending_message.embeds:
                                rejected_embed = pending_message.embeds[0].copy()
                                rejected_embed.color = discord.Color.red()
                                rejected_embed.title = f"Rejected by {user.display_name}"
                                rejected_embed.set_footer(text="")
                                await pending_message.edit(embed=rejected_embed)
                            await message.delete()
                        else:
                            error = await deny_resp.text()
                            await channel.send(f"Failed to reject submission: {error}")
            else:
                await channel.send(f"Submission not found for message ID {message_id}.")

    @app_commands.command(name="clear_channel", description="Deletes all messages in the current channel")
    @app_commands.checks.has_role("Admin")
    async def clear_channel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge()
        await interaction.followup.send("Channel cleared!", ephemeral=True)

async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))