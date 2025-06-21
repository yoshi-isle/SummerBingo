from bson import ObjectId
from flask import Blueprint, abort
from flask import current_app as app
from constants.tiles import world1_tiles
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

image_blueprint = Blueprint('image', __name__)

def get_db():
    return app.config['DB']

def create_board_image(team, tile_info, level=None):
    """
    Generates the board image for a team and returns a BytesIO object.
    """
    image_path = os.path.join(os.path.dirname(__file__), '../images/world1/board/board_background.png')
    image_path = os.path.abspath(image_path)
    try:
        with Image.open(image_path) as base_img:
            path_img_path = os.path.join(os.path.dirname(__file__), '../images/world1/path/w1path0.png')
            path_img_path = os.path.abspath(path_img_path)
            with Image.open(path_img_path) as path_img:
                base_img.paste(path_img, (0, 0), path_img if path_img.mode == 'RGBA' else None)

            # Load and paste tile image on top
            current_tile = team.get("current_tile")
            current_tile_img_path = os.path.join(os.path.dirname(__file__), f'../images/world1/tiles/{current_tile}.png')
            current_tile_img_path = os.path.abspath(current_tile_img_path)
            with Image.open(current_tile_img_path) as tile_img:
                # Resize tile image to max 90x90 (as in discord_id version)
                tile_img.thumbnail((90, 90), Image.LANCZOS)
                # Get map_coordinate from tile_info, default to (0,0) if missing
                map_coordinate = tile_info.get('map_coordinate', (0, 0))
                # Paste tile image at map_coordinate
                base_img.paste(tile_img, map_coordinate, tile_img if tile_img.mode == 'RGBA' else None)

            draw = ImageDraw.Draw(base_img)
            font_path = os.path.join(os.path.dirname(__file__), '../assets/8bit.ttf')
            font_path = os.path.abspath(font_path)
            font = ImageFont.truetype(font_path, size=24)

            team_name = team['team_name']
            text_color = (255, 255, 255)
            text_position = (base_img.width - 20, 20)
            text_position_tile = (0 + 20, 20)

            draw.text(text_position, f"Team\n{team_name}", fill=text_color, font=font, anchor="ra")  # Right alignment

            # If level is provided, use it (discord_id version), else use team['current_tile'] (team_id version)
            tile_label = f"Level {team['current_world']}-{level}\n{tile_info['tile_name']}" if level is not None else f"{team['current_world']}-{team['current_tile']}-{tile_info['tile_name']}"
            draw.text(text_position_tile, tile_label, fill=text_color, font=font, anchor="la")

            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
    except FileNotFoundError:
        abort(404, description="Image not found")
    except Exception as e:
        print(f"Error generating board: {e}")
        abort(500, description=f"Failed to generate board: {e}")

@image_blueprint.route("/image/user/<discord_id>", methods=["GET"])
def generate_board(discord_id):
    """
    Creates a board image for the given Discord user ID.
    """
    db = get_db()
    team = db.teams.find_one({"players.discord_id": discord_id})
    if not team:
        abort(404, "Team not found")
    current_tile = team.get("current_tile")
    tile_info = next((t for t in world1_tiles["world_tiles"] if t["id"] == current_tile), None)
    shuffled_tiles = team.get("world1_shuffled_tiles", [])
    idx = shuffled_tiles.index(current_tile)
    level = idx + 1  # 1-based index
    img_io = create_board_image(team, tile_info, level)
    return app.response_class(img_io, mimetype='image/png')

@image_blueprint.route("/image/team/<team_id>", methods=["GET"])
def generate_board_by_team_id(team_id):
    """
    Creates a board image for the given team ID.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, "Team not found")
    current_tile = team.get("current_tile")
    tile_info = next((t for t in world1_tiles["world_tiles"] if t["id"] == current_tile), None)
    img_io = create_board_image(team, tile_info)
    return app.response_class(img_io, mimetype='image/png')
