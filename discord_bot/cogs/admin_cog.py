from typing import List
import discord
from discord.ext import commands
from discord import Embed, app_commands
import aiohttp
import os
from constants import PENDING_SUBMISSIONS_CHANNEL_ID, APPROVED_SUBMISSIONS_CHANNEL_ID

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
        self.api_url = os.getenv("GAME_API_URL", "http://game_service_api:5000")

    @app_commands.command(name="register_team", description="Registers a new team")
    @app_commands.checks.has_role("Admin")
    async def register_team(self, interaction: discord.Interaction, users: str, team_name: str):
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
        api_url = os.getenv("GAME_API_URL", "http://game_service_api:5000/teams")
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=data) as resp:
                if resp.status == 201:
                    team = await resp.json()
                    await interaction.response.send_message(f"Team '{team_name}' registered!", ephemeral=True)
                else:
                    error = await resp.text()
                    await interaction.response.send_message(f"Failed to register team: {error}", ephemeral=True)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Ignore reactions from the bot itself
        if user.bot:
            return
        
        if reaction.message.channel.id != PENDING_SUBMISSIONS_CHANNEL_ID:
            return
        
        message_id = str(reaction.message.id)
        
        submission_url = f"{self.api_url}/submission/{message_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(submission_url) as resp:
                if resp.status == 200:
                    submission = await resp.json()
                    # Approve submission if reaction is ✅
                    if str(reaction.emoji) == '✅':
                        approve_url = f"{self.api_url}/submission/approve/{submission['_id']}"
                        async with session.put(approve_url) as approve_resp:
                            if approve_resp.status == 200:

                                # Send a copy to the approved submissions channel
                                approved_channel = reaction.message.guild.get_channel(APPROVED_SUBMISSIONS_CHANNEL_ID)
                                team_channel = reaction.message.guild.get_channel(int(submission['team_channel_id']))

                                if team_channel:
                                    # Get pending embed from submission["pending_team_embed_id"]
                                    pending_message = await team_channel.fetch_message(int(submission['pending_team_embed_id']))
                                    if pending_message and pending_message.embeds:
                                        # Update the embed with approval information
                                        approved_embed = pending_message.embeds[0].copy()
                                        approved_embed.color = discord.Color.green()
                                        approved_embed.title = f"Approved by {user.display_name}"
                                        approved_embed.set_footer(text="")
                                        
                                        # Edit the original message in the team channel
                                        await pending_message.edit(embed=approved_embed)
                                        
                                if approved_channel:
                                    # Copy all embeds from the original message, updating the title
                                    if reaction.message.embeds:
                                        for embed in reaction.message.embeds:
                                            new_embed = embed.copy()
                                            new_embed.color = discord.Color.green()
                                            new_embed.title = f"Approved by {user.display_name}"
                                            new_embed.set_footer(text="")

                                            await approved_channel.send(embed=new_embed)
                                    else:
                                        await approved_channel.send(content=reaction.message.content)
                                # Delete the original message
                                await reaction.message.delete()
                            else:
                                error = await approve_resp.text()
                                await reaction.message.channel.send(f"Failed to approve submission: {error}")
                else:
                    await reaction.message.channel.send(f"Submission not found for message ID {message_id}.")

async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))