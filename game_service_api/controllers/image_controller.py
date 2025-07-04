from bson import ObjectId
from flask import Blueprint, abort
from flask import current_app as app
from constants.coordinates import world1_tile_image_coordinates, world2_tile_image_coordinates, world3_tile_image_coordinates, world4_tile_image_coordinates
from constants.tiles import world1_tiles, world2_tiles, world3_tiles, world4_tiles
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

from constants.world_tiles_map import world_tiles_map

image_blueprint = Blueprint('image', __name__)

def get_db():
    return app.config['DB']

@image_blueprint.route("/image/team/<team_id>", methods=["GET"])
def generate_board(team_id):
    """
    Creates a board image for the given team ID.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, "Team not found")

    current_tile = team.get("current_tile")
    current_world = team.get("current_world", 1)
    game_state = team.get("game_state", 0)

    tile_info = next((t for t in world_tiles_map.get(current_world, []) if t["id"] == current_tile), None)
    current_world = team.get("current_world", 1)
    shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
    idx = shuffled_tiles.index(current_tile)
    level = idx + 1  # 1-based index
    if game_state == 0:
        img_io = create_board_image(team, tile_info, level)
        return app.response_class(img_io, mimetype='image/png')

    elif game_state == 1:
        img_io = create_key_image(team, tile_info, level)
        return app.response_class(img_io, mimetype='image/png')
    
    elif game_state == 2:
        img_io = create_boss_image(team)
        return app.response_class(img_io, mimetype='image/png')

def create_boss_image(team):
    current_world = team.get("current_world")
    image_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/board/boss_background.png')
    image_path = os.path.abspath(image_path)
    with Image.open(image_path) as base_img:
        base_img = base_img.convert("RGBA")  # Ensure base image is RGBA for proper alpha compositing
        img_io = BytesIO()
        base_img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io

def create_key_image(team, tile_info, level=None):
    current_world = team.get("current_world")
    image_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/board/key_background.png')
    image_path = os.path.abspath(image_path)
    with Image.open(image_path) as base_img:
        base_img = base_img.convert("RGBA")  # Ensure base image is RGBA for proper alpha compositing
        for idx, tile in enumerate(world1_tiles["key_tiles"]):
            key_tile_img_path = os.path.join(os.path.dirname(__file__), f'../images/{tile["image_url"]}')
            key_tile_img_path = os.path.abspath(key_tile_img_path)
            with Image.open(key_tile_img_path) as tile_img:
                max_size = (90, 90)
                tile_img.thumbnail(max_size, Image.NEAREST)
                tile_img = tile_img.convert("RGBA")  # Ensure tile image is RGBA
                base_img.paste(tile_img, (120 + idx*320, 500), tile_img)
                # Draw text below the image
                draw = ImageDraw.Draw(base_img)
                font_path = os.path.join(os.path.dirname(__file__), '../assets/8bit.ttf')
                font_path = os.path.abspath(font_path)
                font = ImageFont.truetype(font_path, size=16)
                text = tile["tile_name"]
                text_x = 120+idx * 350 + tile_img.width // 2
                text_y = 500 + tile_img.height + 10
                # Draw outline for tile name
                outline_range = 2
                for ox in range(-outline_range, outline_range + 1):
                    for oy in range(-outline_range, outline_range + 1):
                        if ox == 0 and oy == 0:
                            continue
                        draw.text((text_x + ox, text_y + oy), text, font=font, fill="black", anchor="ma")
                # Draw main tile name text
                draw.text((text_x, text_y), text, font=font, fill="white", anchor="ma")

                # Draw index below the tile name
                index_text = f"/key {str(idx + 1)}"
                index_text_y = text_y + 38  # 5px below previous text
                for ox in range(-outline_range, outline_range + 1):
                    for oy in range(-outline_range, outline_range + 1):
                        if ox == 0 and oy == 0:
                            continue
                        draw.text((text_x + ox, index_text_y + oy), index_text, font=font, fill="black", anchor="ma")
                draw.text((text_x, index_text_y), index_text, font=font, fill="yellow", anchor="ma")

        img_io = BytesIO()
        base_img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io
    

def create_board_image(team, tile_info, level=None):
    """
    Generates the board image for a team and returns a BytesIO object.
    """
    current_tile = team.get("current_tile")
    current_world = team.get("current_world")

    image_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/board/board_background.png')
    image_path = os.path.abspath(image_path)
    try:
        with Image.open(image_path) as base_img:
            path_img_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/path/w1path{level-1}.png')
            path_img_path = os.path.abspath(path_img_path)
            with Image.open(path_img_path) as path_img:
                # Create a blacked-out version for drop shadow
                shadow = Image.new("RGBA", path_img.size, (0, 0, 0, 128))
                # Use the alpha channel of the original as mask for the shadow
                if path_img.mode == 'RGBA':
                    shadow.putalpha(path_img.split()[-1])
                # Offset for shadow (e.g., 3px down and right)
                shadow_offset = (3, 3)
                base_img.paste(shadow, shadow_offset, shadow)
                # Paste the original path image
                base_img.paste(path_img, (0, 0), path_img if path_img.mode == 'RGBA' else None)

            # Load and paste tile image on top
            current_tile_img_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/tiles/{current_tile}.png')
            current_tile_img_path = os.path.abspath(current_tile_img_path)
            with Image.open(current_tile_img_path) as tile_img:
                # Resize tile image to exactly 90x90
                # Resize tile image to fit within 90x90 while keeping aspect ratio
                max_size = (90, 90)
                tile_img.thumbnail(max_size, Image.NEAREST)
                # Get map image coordinate
                shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
                current_tile = team.get("current_tile")
                current_world = team.get("current_world")

                idx = shuffled_tiles.index(current_tile)
                level = idx + 1

                map_coordinate = tile_image_coordinates.get(current_world, {}).get(level)

                # Draw black outline behind the tile image
                outline_width = 1
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
                font = ImageFont.truetype(font_path, size=16)
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
            tile_label = f"Level {team['current_world']}-{level}\n{tile_info['tile_name']}" if level is not None else f"{current_world}-{current_tile}-{tile_info['tile_name']}"
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



tile_image_coordinates = {
    1: world1_tile_image_coordinates,
    2: world2_tile_image_coordinates,
    3: world3_tile_image_coordinates,
    4: world4_tile_image_coordinates,
}