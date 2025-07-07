from bson import ObjectId
from flask import Blueprint, abort
from flask import current_app as app
from constants.coordinates import world1_tile_image_coordinates, world2_tile_image_coordinates, world3_tile_image_coordinates, world4_tile_image_coordinates
from constants.tiles import world1_tiles, world2_tiles, world3_tiles, world4_tiles
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

from constants.world_tiles_map import world_tiles_map
from constants.world_names import WORLD_NAMES
from constants.image_settings import ImageSettings
from controllers.image_utils.draw_ui_panel import draw_ui_panel
from controllers.image_utils.draw_olm_dialogue_1 import draw_olm_dialogue_1
from controllers.image_utils.draw_team_text import draw_team_text

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
    level = idx + 1
    if game_state == 0:
        img_io = create_board_image(team, tile_info, level)
        return app.response_class(img_io, mimetype='image/png')

    elif game_state == 1 and current_world == 1:
        img_io = create_w1_key_image(team)
        return app.response_class(img_io, mimetype='image/png')
    
    elif game_state == 2 and current_world == 1:
        img_io = create_w1_boss_image(team)
        return app.response_class(img_io, mimetype='image/png')

def create_w1_boss_image(team):
    current_world = team.get("current_world")
    image_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/board/boss_background.png')
    image_path = os.path.abspath(image_path)
    font_path = os.path.join(os.path.dirname(__file__), ImageSettings.FONT)
    font_path = os.path.abspath(font_path)
    with Image.open(image_path) as base_img:
        draw = ImageDraw.Draw(base_img)
        draw_ui_panel(base_img)
        draw_team_text(draw, team["team_name"])
        
        # Top left - Team Name and Level
        font = ImageFont.truetype(font_path, size=ImageSettings.TEAM_TEXT_FONT_SIZE)
        text_color = (255, 255, 255)
        tile_label="Mystic Cove Summit"
        world_map_image = os.path.join(os.path.dirname(__file__), '../images/world_map.png')
        world_map_image = os.path.abspath(world_map_image)
        with Image.open(world_map_image) as world_map_img:
            world_map_img = world_map_img.convert("RGBA")
            base_img.paste(world_map_img, (20,16), world_map_img if world_map_img.mode == 'RGBA' else None)

        draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
        draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill=text_color, font=font, anchor="la", align="left")
            
        # Tile image graphic
        current_tile_img_path = os.path.join(os.path.dirname(__file__), f'../images/world1/boss/0.png')
        current_tile_img_path = os.path.abspath(current_tile_img_path)
        with Image.open(current_tile_img_path) as tile_img:
            tile_img = tile_img.convert("RGBA")
            tile_img = tile_img.resize(ImageSettings.TILE_IMAGE_SCALE, Image.NEAREST)
            # Draw black outline behind the tile image
            outline_width = 2
            x, y = ImageSettings.TILE_IMAGE_COORDINATES
            mask = tile_img.split()[-1] if tile_img.mode == 'RGBA' else None
            black_img = Image.new("RGBA", tile_img.size, (0, 0, 0, 255))
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx == 0 and dy == 0:
                        continue
                    base_img.paste(black_img, (x + dx, y + dy), mask)
            base_img.paste(tile_img, ImageSettings.TILE_IMAGE_COORDINATES, mask)
            tile_info = world1_tiles["boss_tile"]
            draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['tile_name'],
                font=ImageFont.truetype(font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES,
                max_width=330,
                fill="yellow",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )
            draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['description'],
                font=ImageFont.truetype(font_path, size=ImageSettings.TILE_DESCRIPTION_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION,
                max_width=330,
                fill="white",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )
        base_img = base_img.convert("RGBA")  # Ensure base image is RGBA for proper alpha compositing
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
    team_name = team.get("team_name", "Unknown Team")
    tile_label = f"{WORLD_NAMES[current_world]} {current_world}-{level}" if level is not None else f"{current_world}-{current_tile}-{tile_info['tile_name']}"

    img_background = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/board/board_background.png')
    img_background = os.path.abspath(img_background)
    font_path = os.path.join(os.path.dirname(__file__), ImageSettings.FONT)
    font_path = os.path.abspath(font_path)

    try:
        with Image.open(img_background) as base_img:
            draw = ImageDraw.Draw(base_img)
            draw_ui_panel(base_img)
            # Path Image
            path_img_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/path/w1path{level-1}.png')
            path_img_path = os.path.abspath(path_img_path)
            with Image.open(path_img_path) as path_img:
                base_img.paste(path_img, (0, 0), path_img if path_img.mode == 'RGBA' else None)
            # World Map Image
            world_map_image = os.path.join(os.path.dirname(__file__), '../images/world_map.png')
            world_map_image = os.path.abspath(world_map_image)
            with Image.open(world_map_image) as world_map_img:
                world_map_img = world_map_img.convert("RGBA")
                base_img.paste(world_map_img, (20,16), world_map_img if world_map_img.mode == 'RGBA' else None)
            # Team Bubble Image
            team_image_path = os.path.join(os.path.dirname(__file__), f'../images/teams/{team.get("team_image_path", "1.png")}')
            team_image_path = os.path.abspath(team_image_path)
            with Image.open(team_image_path) as team_img:
                base_img.paste(team_img, world1_tile_image_coordinates[level], team_img if team_img.mode == 'RGBA' else None)
            # Tile image graphic
            current_tile_img_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/tiles/{current_tile}.png')
            current_tile_img_path = os.path.abspath(current_tile_img_path)
            with Image.open(current_tile_img_path) as tile_img:
                tile_img = tile_img.convert("RGBA")
                tile_img = tile_img.resize(ImageSettings.TILE_IMAGE_SCALE, Image.NEAREST)
                # Draw black outline behind the tile image
                outline_width = 2
                x, y = ImageSettings.TILE_IMAGE_COORDINATES
                mask = tile_img.split()[-1] if tile_img.mode == 'RGBA' else None
                black_img = Image.new("RGBA", tile_img.size, (0, 0, 0, 255))
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx == 0 and dy == 0:
                            continue
                        base_img.paste(black_img, (x + dx, y + dy), mask)
                base_img.paste(tile_img, ImageSettings.TILE_IMAGE_COORDINATES, mask)

            font = ImageFont.truetype(font_path, size=ImageSettings.TEAM_TEXT_FONT_SIZE)
            text_color = (255, 255, 255)

            # Top left - Team Name and Level
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill=text_color, font=font, anchor="la", align="left")
            
            # Top right - Tile info
            draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['tile_name'],
                font=ImageFont.truetype(font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES,
                max_width=330,
                fill="yellow",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )
            draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['description'],
                font=ImageFont.truetype(font_path, size=ImageSettings.TILE_DESCRIPTION_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION,
                max_width=330,
                fill="white",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )

            draw_team_text(draw, team["team_name"])
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
    except FileNotFoundError:
        abort(404, description="Image not found")
    except Exception as e:
        print(f"Error generating board: {e}")
        abort(500, description=f"Failed to generate board: {e}")

def create_w1_key_image(team):
    keys = count_w1_keys(team)
    which_key_background = {
        0: '../images/world1/keys/key_board_1.png',
        1: '../images/world1/keys/key_board_2.png',
        2: '../images/world1/keys/key_board_3.png',
    }
    font_path = os.path.join(os.path.dirname(__file__), ImageSettings.FONT)
    font_path = os.path.abspath(font_path)
    font=ImageFont.truetype(font_path, size=ImageSettings.TEAM_TEXT_FONT_SIZE)

    image_path = os.path.join(os.path.dirname(__file__), which_key_background[keys])
    image_path = os.path.abspath(image_path)
    with Image.open(image_path) as base_img:
        draw = ImageDraw.Draw(base_img)
        draw_ui_panel(base_img)
        draw_olm_dialogue_1(base_img)
        draw_team_text(draw, team["team_name"])
         # Top left - Level
         # World Map Image
        key_tile_path = os.path.join(os.path.dirname(__file__), '../images/key_tile.png')
        key_tile_path = os.path.abspath(key_tile_path)
        with Image.open(key_tile_path) as key_tile_image:
            key_tile_image = key_tile_image.convert("RGBA")
            base_img.paste(key_tile_image, (20,16), key_tile_image if key_tile_image.mode == 'RGBA' else None)
        
        # key tile image graphic
        key_tile_graphic = os.path.join(os.path.dirname(__file__), '../images/world1/key_tiles.png')
        key_tile_graphic = os.path.abspath(key_tile_graphic)
        with Image.open(key_tile_graphic) as key_graphic:
            key_graphic = key_graphic.convert("RGBA")
            base_img.paste(key_graphic, (20,16), key_graphic if key_graphic.mode == 'RGBA' else None)
        
        tile_label = "Mystic Cove Trial"
        draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
        draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
        img_io = BytesIO()
        base_img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io


tile_image_coordinates = {
    1: world1_tile_image_coordinates,
    2: world2_tile_image_coordinates,
    3: world3_tile_image_coordinates,
    4: world4_tile_image_coordinates,
}

def draw_outlined_wrapped_text(draw, text, font, position, max_width, fill="white", outline_fill="black", outline_range=2, line_spacing=4, align="left"):
    """
    Draw wrapped and outlined text using Pillow with proper word wrapping and alignment.

    Args:
        draw: ImageDraw.Draw object.
        text: Text to draw.
        font: ImageFont.FreeTypeFont object.
        position: (x, y) top-left start position.
        max_width: Max width for text wrapping.
        fill: Fill color for main text.
        outline_fill: Fill color for the outline.
        outline_range: Outline thickness in pixels.
        line_spacing: Pixels between lines.
        align: One of "left", "center", "right".
    """
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width <= max_width:
                line = test_line
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    x, y = position
    lines = wrap_text(text, font, max_width)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        if align == "center":
            tx = x + (max_width - w) // 2
        elif align == "right":
            tx = x + (max_width - w)
        else:  # default to left
            tx = x

        # Outline
        for ox in range(-outline_range, outline_range + 1):
            for oy in range(-outline_range, outline_range + 1):
                if ox == 0 and oy == 0:
                    continue
                draw.text((tx + ox, y + oy), line, font=font, fill=outline_fill)

        # Main text
        draw.text((tx, y), line, font=font, fill=fill)
        y += h + line_spacing

def count_w1_keys(team):
    return sum(int(key) == 0 for key in [
        team["w1key1_completion_counter"],
        team["w1key2_completion_counter"],
        team["w1key3_completion_counter"],
        team["w1key4_completion_counter"],
        team["w1key5_completion_counter"]
    ])