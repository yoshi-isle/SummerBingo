import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from constants import ApiUrls, DiscordIDs

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
            await interaction.response.send_message("Error creating team. Please try again")
            
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Ignore reactions from the bot itself
        if user.bot:
            return
        
        if reaction.message.channel.id != DiscordIDs.PENDING_SUBMISSIONS_CHANNEL_ID:
            return
        
        message_id = str(reaction.message.id)
        
        async with self.session.get(ApiUrls.SUBMISSION.format(id=message_id)) as resp:
            if resp.status == 200:
                submission = await resp.json()
                # Approve submission if reaction is ✅
                if str(reaction.emoji) == '✅':
                    async with self.session.put(ApiUrls.APPROVE_SUBMISSION.format(id=submission["_id"])) as approve_resp:
                        if approve_resp.status == 200:

                            # Send a copy to the approved submissions channel
                            approved_channel = reaction.message.guild.get_channel(DiscordIDs.APPROVED_SUBMISSIONS_CHANNEL_ID)
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
                            async with self.session.post(ApiUrls.TEAM_ADVANCE_TILE.format(id=submission['team_id'])) as advance_resp:
                                if advance_resp.status == 200:
                                    await reaction.message.channel.send("Tile advanced successfully!")
                                else:
                                    error = await advance_resp.text()
                                    await reaction.message.channel.send(f"Failed to advance tile: {error}")

                        else:
                            error = await approve_resp.text()
                            await reaction.message.channel.send(f"Failed to approve submission: {error}")
            else:
                await reaction.message.channel.send(f"Submission not found for message ID {message_id}.")

    @app_commands.command(name="clear_channel", description="Deletes all messages in the current channel")
    @app_commands.checks.has_role("Admin")
    async def clear_channel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge()
        await interaction.followup.send("Channel cleared!", ephemeral=True)

async def setup(bot: commands):
    await bot.add_cog(AdminCog(bot))