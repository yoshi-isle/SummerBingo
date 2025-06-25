from bson import ObjectId
from flask import Blueprint, abort
from flask import current_app as app
from constants.coordinates import world1_tile_image_coordinates
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
    current_tile = team.get("current_tile")
    current_world_number = team.get("current_world")

    image_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world_number}/board/board_background.png')
    image_path = os.path.abspath(image_path)
    try:
        with Image.open(image_path) as base_img:
            path_img_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world_number}/path/w1path{level-1}.png')
            path_img_path = os.path.abspath(path_img_path)
            with Image.open(path_img_path) as path_img:
                # Create a blacked-out version for drop shadow
                shadow = Image.new("RGBA", path_img.size, (0, 0, 0, 128))
                # Use the alpha channel of the original as mask for the shadow
                if path_img.mode == 'RGBA':
                    shadow.putalpha(path_img.split()[-1])
                # Offset for shadow (e.g., 3px down and right)
                shadow_offset = (5, 9)
                base_img.paste(shadow, shadow_offset, shadow)
                # Paste the original path image
                base_img.paste(path_img, (0, 0), path_img if path_img.mode == 'RGBA' else None)

            # Load and paste tile image on top
            current_tile_img_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world_number}/tiles/{current_tile}.png')
            current_tile_img_path = os.path.abspath(current_tile_img_path)
            with Image.open(current_tile_img_path) as tile_img:
                # Resize tile image to exactly 90x90
                tile_img = tile_img.resize((90, 90), Image.NEAREST)
                # Get map image coordinate
                shuffled_tiles = team.get("world1_shuffled_tiles", [])
                current_tile = team.get("current_tile")
                idx = shuffled_tiles.index(current_tile)
                level = idx + 1

                map_coordinate = world1_tile_image_coordinates[level]

                # Draw black outline behind the tile image
                outline_width = 2
                x, y = map_coordinate
                mask = tile_img.split()[-1] if tile_img.mode == 'RGBA' else None
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx == 0 and dy == 0:
                            continue
                        base_img.paste((0, 0, 0), (x + dx, y + dy), mask)
                base_img.paste(tile_img, map_coordinate, mask)

                # Draw outlined text underneath the image
                draw = ImageDraw.Draw(base_img)
                font_path = os.path.join(os.path.dirname(__file__), '../assets/8bit.ttf')
                font_path = os.path.abspath(font_path)
                font = ImageFont.truetype(font_path, size=12)
                text = f"{tile_info['tile_name']}"
                text_x = x + tile_img.width // 2
                text_y = y + tile_img.height + 5
                
                # Draw outline
                outline_range = 2
                for ox in range(-outline_range, outline_range + 1):
                    for oy in range(-outline_range, outline_range + 1):
                        if ox == 0 and oy == 0:
                            continue
                        draw.text((text_x + ox, text_y + oy), text, font=font, fill="black", anchor="ma")
                # Draw main text
                draw.text((text_x, text_y), text, font=font, fill="white", anchor="ma")

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
    shuffled_tiles = team.get("world1_shuffled_tiles", [])
    idx = shuffled_tiles.index(current_tile)
    level = idx + 1  # 1-based index
    img_io = create_board_image(team, tile_info, level)
    return app.response_class(img_io, mimetype='image/png')
