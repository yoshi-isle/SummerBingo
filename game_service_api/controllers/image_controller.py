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
                
                font_path = os.path.join(os.path.dirname(__file__), ImageSettings.FONT)
                font_path = os.path.abspath(font_path)
                font = ImageFont.truetype(font_path, size=32)
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
    team_name = team.get("team_name", "Unknown Team")

    img_background = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/board/board_background.png')
    img_background = os.path.abspath(img_background)
    font_path = os.path.join(os.path.dirname(__file__), ImageSettings.FONT)
    font_path = os.path.abspath(font_path)
    tile_label = f"{WORLD_NAMES[current_world]} {current_world}-{level}" if level is not None else f"{current_world}-{current_tile}-{tile_info['tile_name']}"

    try:
        with Image.open(img_background) as base_img:

            draw = ImageDraw.Draw(base_img)

            # UI Panel
            ui_img_path = os.path.join(os.path.dirname(__file__), f'../images/user_interface.png')
            ui_img_path = os.path.abspath(ui_img_path)
            with Image.open(ui_img_path) as ui_image:
                base_img.paste(ui_image, (0, 0), ui_image if ui_image.mode == 'RGBA' else None)
            # Path Image
            path_img_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/path/w1path{level-1}.png')
            path_img_path = os.path.abspath(path_img_path)
            with Image.open(path_img_path) as path_img:
                base_img.paste(path_img, (0, 0), path_img if path_img.mode == 'RGBA' else None)
            # Team Bubble Image
            team_image_path = os.path.join(os.path.dirname(__file__), f'../images/teams/{team.get("team_image_path", "1.png")}')
            team_image_path = os.path.abspath(team_image_path)
            with Image.open(team_image_path) as team_img:
                base_img.paste(team_img, world1_tile_image_coordinates[level], team_img if team_img.mode == 'RGBA' else None)
            # Tile image graphic
            map_coordinate = ImageSettings.TILE_IMAGE_COORDINATES
            current_tile_img_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/tiles/{current_tile}.png')
            current_tile_img_path = os.path.abspath(current_tile_img_path)
            with Image.open(current_tile_img_path) as tile_img:
                tile_img = tile_img.convert("RGBA")
                tile_img = tile_img.resize(ImageSettings.TILE_IMAGE_SCALE, Image.NEAREST)
                # Draw black outline behind the tile image
                outline_width = 2
                x, y = map_coordinate
                mask = tile_img.split()[-1] if tile_img.mode == 'RGBA' else None
                # Create a black image for the outline, same size as tile_img
                black_img = Image.new("RGBA", tile_img.size, (0, 0, 0, 255))
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx == 0 and dy == 0:
                            continue
                        base_img.paste(black_img, (x + dx, y + dy), mask)
                base_img.paste(tile_img, map_coordinate, mask)

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


            # font = ImageFont.truetype(font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            # outline_range = 2
            # for ox in range(-outline_range, outline_range + 1):
            #     for oy in range(-outline_range, outline_range + 1):
            #         if ox == 0 and oy == 0:
            #             continue
            #         draw.text((ImageSettings.TILE_IMAGE_TEXT_COORDINATES[0] + ox, ImageSettings.TILE_IMAGE_TEXT_COORDINATES[1] + oy), tile_info['tile_name'], font=font, fill="black", align="center")
            # draw.text((ImageSettings.TILE_IMAGE_TEXT_COORDINATES[0], ImageSettings.TILE_IMAGE_TEXT_COORDINATES[1]), tile_info['tile_name'], fill="yellow", font=font, align="center")
            # font = ImageFont.truetype(font_path, size=18)
            # for ox in range(-outline_range, outline_range + 1):
            #     for oy in range(-outline_range, outline_range + 1):
            #         if ox == 0 and oy == 0:
            #             continue
            #         draw.text((ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION[0] + ox, ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION[1] + oy), tile_info['description'], font=font, fill="black", align="center")
            # draw.text((ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION[0], ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION[1]), tile_info['description'], fill="white", font=font, align="center")

            font = ImageFont.truetype(font_path, size=ImageSettings.TEAM_TEXT_FONT_SIZE)
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