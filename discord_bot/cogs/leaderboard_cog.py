import discord
import asyncio
import aiohttp
from discord.ext import commands, tasks
from discord import Embed
from constants import ApiUrls, DiscordIDs, WORLD_NAMES, Emojis
import logging

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard_message = None
        self.leaderboard_channel_id = None
        self.update_leaderboard.start()

    def cog_unload(self):
        self.update_leaderboard.cancel()

    @tasks.loop(minutes=3)
    async def update_leaderboard(self):
        """Update the leaderboard every 3 minutes"""
        if self.leaderboard_message is None:
            # TODO
            self.leaderboard_message = await self.bot.get_channel(1379166550451294268).fetch_message(1392910933394722948)
            return

        try:
            teams = await self.fetch_all_teams()
            if teams:
                embed = self.create_leaderboard_embed(teams)
                await self.leaderboard_message.edit(embed=embed)
                logging.info("Leaderboard updated successfully")
        except Exception as e:
            logging.error(f"Error updating leaderboard: {e}")

    @update_leaderboard.before_loop
    async def before_update_leaderboard(self):
        """Wait until the bot is ready before starting the loop"""
        await self.bot.wait_until_ready()

    async def fetch_all_teams(self):
        """Fetch all teams from the API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ApiUrls.TEAM_ALL) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logging.error(f"Failed to fetch teams: {response.status}")
                        return []
        except Exception as e:
            logging.error(f"Error fetching teams: {e}")
            return []

    def create_leaderboard_embed(self, teams):
        """Create the leaderboard embed"""
        embed = Embed(
            title="🏆 Top Teams",
            color=0x00ff00,
            description=""
        )
        
        if not teams:
            embed.add_field(
                name="No Teams Found", 
                value="No teams are currently participating.", 
                inline=False
            )
            return embed

        leaderboard_text = ""
        position_emojis = ["🥇", "🥈", "🥉"]
        
        current_rank = 1
        previous_world = None
        previous_level = None
        
        for i, team in enumerate(teams):
            team_name = team.get("team_name", "Unknown Team")
            world_number = team.get("world_number", 1)
            level_number = team.get("level_number", 1)
            
            # Check if this team has the same world/level as the previous team (tie)
            if i > 0 and world_number == previous_world and level_number == previous_level:
                # This is a tie, use the same rank as previous team
                position = current_rank
            else:
                # New rank - set it to current index + 1
                current_rank = i + 1
                position = current_rank
            
            # Get position emoji or number
            if position <= 3:
                position_icon = position_emojis[position - 1]
            else:
                position_icon = ""
            
            leaderboard_text += f"{position_icon} {team_name}\n"
            
            # Update previous values for next iteration
            previous_world = world_number
            previous_level = level_number
            
        embed.add_field(
            name="", 
            value=leaderboard_text if leaderboard_text else "No teams found", 
            inline=False
        )
        
        embed.set_footer(text="Updates every 3 minutes", icon_url=Emojis.SKW_LOGO)
        return embed

    @discord.app_commands.command(name="admin_create_leaderboard", description="Create a new leaderboard message")
    @discord.app_commands.checks.has_role("Admin")
    async def create_leaderboard(self, interaction: discord.Interaction):
        """Create a new leaderboard message in the current channel"""
        teams = await self.fetch_all_teams()
        embed = self.create_leaderboard_embed(teams)
        
        message = await interaction.channel.send(embed=embed)
        self.leaderboard_message = message
        self.leaderboard_channel_id = interaction.channel.id
        
        await interaction.response.send_message(
            "✅ Leaderboard created! It will update automatically every 3 minutes.", 
            ephemeral=True
        )

    @discord.app_commands.command(name="admin_update_leaderboard_now", description="Manually update the leaderboard")
    @discord.app_commands.checks.has_role("Admin")
    async def update_leaderboard_now(self, interaction: discord.Interaction):
        """Manually trigger a leaderboard update"""
        if self.leaderboard_message is None:
            await interaction.response.send_message(
                "❌ No leaderboard message found. Use `/create_leaderboard` first.", 
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        
        try:
            teams = await self.fetch_all_teams()
            if teams:
                embed = self.create_leaderboard_embed(teams)
                await self.leaderboard_message.edit(embed=embed)
                await interaction.followup.send("✅ Leaderboard updated successfully!", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to fetch team data.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error updating leaderboard: {e}", ephemeral=True)

    @discord.app_commands.command(name="admin_set_leaderboard_message", description="Set an existing message as the leaderboard")
    @discord.app_commands.checks.has_role("Admin")
    async def set_leaderboard_message(self, interaction: discord.Interaction, message_id: str):
        """Set an existing message as the leaderboard message"""
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            self.leaderboard_message = message
            self.leaderboard_channel_id = interaction.channel.id
            
            # Update the message immediately
            teams = await self.fetch_all_teams()
            embed = self.create_leaderboard_embed(teams)
            await message.edit(embed=embed)
            
            await interaction.response.send_message(
                f"✅ Leaderboard message set to message ID: {message_id}. Updated immediately!", 
                ephemeral=True
            )
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Message not found. Make sure the message ID is correct and in this channel.", 
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid message ID format.", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting leaderboard message: {e}", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
