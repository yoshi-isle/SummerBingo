import discord
import io
import aiohttp
from constants import ApiUrls
from embeds import (build_team_board_embed,
                    build_w1_key_board_embed,
                    build_w2_boss_board_embed,
                    build_w2_key_board_embed,
                    build_w1_boss_board_embed, build_w3_boss_board_embed,
                    build_w3_key_board_embed, build_w4_boss_board_embed, build_w4_key_board_embed)

async def post_team_board(session: aiohttp.ClientSession, team_id: str, team_channel: discord.TextChannel, board_type: str = "auto"):
    """
    Post a team's board to their channel.
    
    Args:
        session: aiohttp session for making API calls
        team_id: The team's ID
        team_channel: The Discord channel to post to
        board_type: Type of board to post ("auto", "overworld", "w1_key", "w2_key", "w1_boss")
                   If "auto", will determine type based on team's game state
    """
    # Get team board information
    async with session.get(ApiUrls.TEAM_BOARD_INFORMATION.format(id=team_id)) as resp:
        if resp.status != 200:
            raise Exception(f"Failed to get team board information: {resp.status}")
        info = await resp.json()
    
    # Get board image
    async with session.get(ApiUrls.IMAGE_BOARD.format(id=team_id)) as image_resp:
        if image_resp.status != 200:
            raise Exception(f"Failed to get team board image: {image_resp.status}")
        image_data = await image_resp.read()
    
    team_data = info["team"]
    tile_info = info.get("tile", {})
    level_number = info.get("level_number", "")
    
    # Create Discord file
    file = discord.File(io.BytesIO(image_data), filename="team_board.png")
    
    # Determine board type if auto
    if board_type == "auto":
        game_state = int(team_data["game_state"])
        current_world = int(team_data["current_world"])
        
        if game_state == 0:
            board_type = "overworld"
        elif game_state == 1 and current_world == 1:
            board_type = "w1_key"
        elif game_state == 1 and current_world == 2:
            board_type = "w2_key"
        elif game_state == 2 and current_world == 1:
            board_type = "w1_boss"
        else:
            board_type = "overworld"  # fallback
    
    # Build appropriate embed
    if board_type == "overworld":
        embed = build_team_board_embed(team_data, tile_info, level_number)
    elif board_type == "w1_key":
        embed = build_w1_key_board_embed(team_data)
    elif board_type == "w2_key":
        embed = build_w2_key_board_embed(team_data)
    elif board_type == "w1_boss":
        embed = build_w1_boss_board_embed(team_data)
    elif board_type == "w2_boss":
        embed = build_w2_boss_board_embed(team_data)
    elif board_type == "w3_key":
        embed = build_w3_key_board_embed(team_data)
    elif board_type == "w3_boss":
        embed = build_w3_boss_board_embed(team_data)
    elif board_type == "w4_key":
        embed = build_w4_key_board_embed(team_data)
    elif board_type == "w4_boss":
        embed = build_w4_boss_board_embed(team_data)
    else:
        # fallback to overworld
        embed = build_team_board_embed(team_data, tile_info, level_number)
    
    # Set image and send
    embed.set_image(url="attachment://team_board.png")
    await team_channel.send(embed=embed, file=file)
