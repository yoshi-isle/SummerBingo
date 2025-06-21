from flask import Blueprint, abort
from services.team_service import TeamService
from flask import current_app as app
from constants.tiles import world1_tiles
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

team_service = TeamService()
image_blueprint = Blueprint('image', __name__)

@image_blueprint.route("/image/user/<discord_id>", methods=["GET"])
def generate_board(discord_id):
    """
    Creates a board image for the given Discord user ID.
    """
    team = team_service.get_team_by_discord_id(discord_id)
    if not team:
        abort(404, "Team not found")
    
    current_tile = team.get("current_tile")
    tile_info = next((t for t in world1_tiles["world_tiles"] if t["id"] == current_tile), None)
    
    # Get the current world number
    shuffled_tiles = team.get("world1_shuffled_tiles", [])
    idx = shuffled_tiles.index(current_tile)
    level = idx + 1  # 1-based index



    image_path = os.path.join(os.path.dirname(__file__), '../images/world1/board/board_background.png')
    image_path = os.path.abspath(image_path)
    try:
        with Image.open(image_path) as base_img:
            path_img_path = os.path.join(os.path.dirname(__file__), '../images/world1/path/w1path0.png')
            path_img_path = os.path.abspath(path_img_path)
            with Image.open(path_img_path) as path_img:
                base_img.paste(path_img, (0, 0), path_img if path_img.mode == 'RGBA' else None)

            # Load and paste boss image (0.png) on top
            boss_img_path = os.path.join(os.path.dirname(__file__), f'../images/world1/tiles/{current_tile}.png')
            boss_img_path = os.path.abspath(boss_img_path)
            with Image.open(boss_img_path) as boss_img:
                # Resize boss image to max 64x64
                boss_img.thumbnail((64, 64), Image.LANCZOS)
                # Get map_coordinate from tile_info, default to (0,0) if missing
                map_coordinate = tile_info.get('map_coordinate', (0, 0))
                # Paste boss image at map_coordinate
                base_img.paste(boss_img, map_coordinate, boss_img if boss_img.mode == 'RGBA' else None)

            draw = ImageDraw.Draw(base_img)
            
            font_path = os.path.join(os.path.dirname(__file__), '../assets/8bit.ttf')
            font_path = os.path.abspath(font_path)

            font = ImageFont.truetype(font_path, size=32)

            team_name = team['team_name']
            text_color = (255, 255, 255)
            text_position = (base_img.width - 20, 20)
            text_position_tile = (0 + 20, 20)

            draw.text(text_position, f"Team\n{team_name}", fill=text_color, font=font, anchor="ra")  # Right alignment

            draw.text(text_position_tile, f"{team['current_world']}-{level}-{tile_info['tile_name']}", fill=text_color, font=font, anchor="la")


            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return app.response_class(img_io, mimetype='image/png')
    except FileNotFoundError:
        abort(404, description="Image not found")
    except Exception as e:
        print(f"Error generating board: {e}")
        abort(500, description=f"Failed to generate board: {e}")

@image_blueprint.route("/image/team/<team_id>", methods=["GET"])
def generate_board_by_team_id(team_id):
    """
    Creates a board image for the given team ID.
    """
    team = team_service.get_team_by_id(team_id)
    if not team:
        abort(404, "Team not found")
    
    current_tile = team.get("current_tile")
    tile_info = next((t for t in world1_tiles["world_tiles"] if t["id"] == current_tile), None)

    image_path = os.path.join(os.path.dirname(__file__), '../images/world1/board/board_background.png')
    image_path = os.path.abspath(image_path)
    try:
        with Image.open(image_path) as base_img:
            path_img_path = os.path.join(os.path.dirname(__file__), '../images/world1/path/w1path0.png')
            path_img_path = os.path.abspath(path_img_path)
            with Image.open(path_img_path) as path_img:
                base_img.paste(path_img, (0, 0), path_img if path_img.mode == 'RGBA' else None)

            # Load and paste boss image (0.png) on top
            boss_img_path = os.path.join(os.path.dirname(__file__), f'../images/world1/tiles/{current_tile}.png')
            boss_img_path = os.path.abspath(boss_img_path)
            with Image.open(boss_img_path) as boss_img:
                # Resize boss image to max 64x64
                boss_img.thumbnail((64, 64), Image.LANCZOS)
                # Get map_coordinate from tile_info, default to (0,0) if missing
                map_coordinate = tile_info.get('map_coordinate', (0, 0))
                # Paste boss image at map_coordinate
                base_img.paste(boss_img, map_coordinate, boss_img if boss_img.mode == 'RGBA' else None)

            draw = ImageDraw.Draw(base_img)
            
            font_path = os.path.join(os.path.dirname(__file__), '../assets/8bit.ttf')
            font_path = os.path.abspath(font_path)

            font = ImageFont.truetype(font_path, size=32)

            team_name = team['team_name']
            text_color = (255, 255, 255)
            text_position = (base_img.width - 20, 20)
            text_position_tile = (0 + 20, 20)

            draw.text(text_position, f"Team\n{team_name}", fill=text_color, font=font, anchor="ra")  # Right alignment

            draw.text(text_position_tile, f"{team['current_world']}-{team['current_tile']}-{tile_info['tile_name']}", fill=text_color, font=font, anchor="la")


            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return app.response_class(img_io, mimetype='image/png')
    except FileNotFoundError:
        abort(404, description="Image not found")
    except Exception as e:
        print(f"Error generating board: {e}")
        abort(500, description=f"Failed to generate board: {e}")
