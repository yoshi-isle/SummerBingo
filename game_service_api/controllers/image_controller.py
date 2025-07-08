from flask import Blueprint, abort, jsonify
from flask import current_app as app
from services.image_service import ImageService
import traceback

image_blueprint = Blueprint('image', __name__)

def get_db():
    return app.config['DB']

@image_blueprint.route("/image/team/<team_id>", methods=["GET"])
def generate_board(team_id):
    try:
        image_service = ImageService()
        board_image = image_service.generate_board_image(team_id)
        return app.response_class(board_image, mimetype='image/png')
    except Exception as e:
        tb_str = traceback.format_exc()
        return jsonify({
            "error": str(e),
            "trace": tb_str
        }), 500

# @image_blueprint.route("/image/team/<team_id>", methods=["GET"])
# def generate_board(team_id):
#     try:
#         image_service = ImageService()
#         board_image = image_service.generate_board_image(team_id)
#         return app.response_class(board_image, mimetype='image/png')
#     except Exception as e:
#         tb_str = traceback.format_exc()  # Full traceback as string
#         app.logger.error(f"Error generating board for team {team_id}:\n{tb_str}")
#         abort(500, description=f"Internal Server Error:\n{str(e)}\nSee logs for details.")

# def create_w1_boss_image(team):
#     current_world = team.get("current_world")
#     image_path = os.path.join(os.path.dirname(__file__), f'../images/world{current_world}/board/boss_background.png')
#     image_path = os.path.abspath(image_path)
#     font_path = os.path.join(os.path.dirname(__file__), ImageSettings.FONT)
#     font_path = os.path.abspath(font_path)
#     with Image.open(image_path) as base_img:
#         draw = ImageDraw.Draw(base_img)
#         draw_ui_panel(base_img)
#         draw_team_text(draw, team["team_name"])
        
#         # Top left - Team Name and Level
#         font = ImageFont.truetype(font_path, size=ImageSettings.TEAM_TEXT_FONT_SIZE)
#         text_color = (255, 255, 255)
#         tile_label="Mystic Cove Summit"
#         world_map_image = os.path.join(os.path.dirname(__file__), '../images/world_map.png')
#         world_map_image = os.path.abspath(world_map_image)
#         with Image.open(world_map_image) as world_map_img:
#             world_map_img = world_map_img.convert("RGBA")
#             base_img.paste(world_map_img, (20,16), world_map_img if world_map_img.mode == 'RGBA' else None)

#         draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
#         draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill=text_color, font=font, anchor="la", align="left")
            
#         # Tile image graphic
#         current_tile_img_path = os.path.join(os.path.dirname(__file__), f'../images/world1/boss/0.png')
#         current_tile_img_path = os.path.abspath(current_tile_img_path)
#         with Image.open(current_tile_img_path) as tile_img:
#             tile_img = tile_img.convert("RGBA")
#             tile_img = tile_img.resize(ImageSettings.TILE_IMAGE_SCALE, Image.NEAREST)
#             # Draw black outline behind the tile image
#             outline_width = 2
#             x, y = ImageSettings.TILE_IMAGE_COORDINATES
#             mask = tile_img.split()[-1] if tile_img.mode == 'RGBA' else None
#             black_img = Image.new("RGBA", tile_img.size, (0, 0, 0, 255))
#             for dx in range(-outline_width, outline_width + 1):
#                 for dy in range(-outline_width, outline_width + 1):
#                     if dx == 0 and dy == 0:
#                         continue
#                     base_img.paste(black_img, (x + dx, y + dy), mask)
#             base_img.paste(tile_img, ImageSettings.TILE_IMAGE_COORDINATES, mask)
#             tile_info = world1_tiles["boss_tile"]
#             draw_outlined_wrapped_text(
#                 draw=draw,
#                 text=tile_info['tile_name'],
#                 font=ImageFont.truetype(font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE),
#                 position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES,
#                 max_width=330,
#                 fill="yellow",
#                 outline_fill="black",
#                 outline_range=2,
#                 line_spacing=2,
#                 align="center"
#             )
#             draw_outlined_wrapped_text(
#                 draw=draw,
#                 text=tile_info['description'],
#                 font=ImageFont.truetype(font_path, size=ImageSettings.TILE_DESCRIPTION_FONT_SIZE),
#                 position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION,
#                 max_width=330,
#                 fill="white",
#                 outline_fill="black",
#                 outline_range=2,
#                 line_spacing=2,
#                 align="center"
#             )
#         base_img = base_img.convert("RGBA")  # Ensure base image is RGBA for proper alpha compositing
#         img_io = BytesIO()
#         base_img.save(img_io, 'PNG')
#         img_io.seek(0)
#         return img_io