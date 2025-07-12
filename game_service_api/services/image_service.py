from io import BytesIO
import os
from bson import ObjectId
from flask import current_app

from constants.image_settings import ImageSettings
from utils.count_w1_keys import count_w1_keys
from utils.tile_info_from_team import tile_info_from_team
from utils.level_number_from_team import level_number_from_team
from utils.level_name_from_team import level_name_from_team
from constants.tiles import world1_tiles, world2_tiles, world3_tiles, world4_tiles

from constants.team_bubble_coordinates import TeamBubbleCoordinates
from PIL import Image, ImageDraw, ImageFont

class ImageService:

    def __init__(self):
        self.db = current_app.config['DB']
        self.font_path = os.path.join(os.path.dirname(__file__), ImageSettings.FONT)
        self.font_path = os.path.abspath(self.font_path)
    
    def generate_board_image(self, team_id):
        team = self.db.teams.find_one({"_id": ObjectId(team_id)})

        game_state = team.get("game_state")
        world = team.get("current_world")
        
        if game_state == 0:
            return self.generate_overworld_image(team)
        
        # World 1
        elif game_state == 1 and world == 1:
            return self.generate_w1_key_image(team)
        elif game_state == 2 and world == 1:
            return self.generate_w1_boss_image(team)
        
        # World 2
        elif game_state == 1 and world == 2:
            return self.generate_w2_key_image(team)
        elif game_state == 2 and world == 2:
            return self.generate_w2_boss_image(team)
        
        # World 3 
        elif game_state == 1 and world == 3:
            return self.generate_w3_key_image(team)
        elif game_state == 2 and world == 3:
            return self.generate_w3_boss_image(team)

        
        # World 4
        elif game_state == 1 and world == 4:
            return self.generate_w4_key_image(team)
        elif game_state == 2 and world == 4:
            return self.generate_w4_boss_image(team)

    def generate_overworld_image(self, team):
        level_name = level_name_from_team(team)
        tile_info = tile_info_from_team(team)
        board_background_to_use = f'../images/world{team.get('current_world')}/board/board_background.png'
        
        # World 2 specific - fog or no fog
        if team.get('current_world') == 2:
            if level_number_from_team(team) >= 8:
                board_background_to_use = f'../images/world{team.get('current_world')}/board/board_background_no_fog.png'
            else:
                board_background_to_use = f'../images/world{team.get('current_world')}/board/board_background_fog.png'
            
         # World 3 specific - braziers
        if team.get('current_world') == 3:
            if team.get('w3_braziers_lit', 0) == 0:
                board_background_to_use = f'../images/world{team.get('current_world')}/board/board_background_1.png'
            if team.get('w3_braziers_lit', 0) == 1:
                board_background_to_use = f'../images/world{team.get('current_world')}/board/board_background_2.png'
            if team.get('w3_braziers_lit', 0) == 2:
                board_background_to_use = f'../images/world{team.get('current_world')}/board/board_background_3.png'
            if team.get('w3_braziers_lit', 0) == 3:
                board_background_to_use = f'../images/world{team.get('current_world')}/board/board_background_4.png'

        background_filepath = os.path.join(os.path.dirname(__file__), board_background_to_use)
        background_filepath = os.path.abspath(background_filepath)
        team_bubble_coordinates = TeamBubbleCoordinates.coordinate_map[team.get('current_world')]
        with Image.open(background_filepath) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            # Path
            self.paste_image(base_img, f'../images/world{team.get('current_world')}/path/w{team.get('current_world')}path{level_number_from_team(team)-1}.png')
            # World Map Icon

            # Caves
            if team.get('current_world') == 3 and team.get('w3_braziers_lit', 0) == 3:
                self.paste_image(base_img, '../images/dungeon.png', (20, 16))
            else:
                self.paste_image(base_img, '../images/world_map.png', (20, 16))
            # Team bubble
            self.paste_image(base_img, f'../images/teams/{team.get("team_image_path")}', team_bubble_coordinates[level_number_from_team(team)])
            self.draw_tile_image(base_img, f'../images/world{team.get('current_world')}/tiles/{team.get('current_tile')}.png')
            self.draw_level_text(draw, level_name)
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['tile_name'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES,
                max_width=330,
                fill="yellow",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['description'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.TILE_DESCRIPTION_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION,
                max_width=330,
                fill="white",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="left"
            )

            self.draw_team_text(draw, team["team_name"])
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
        
    def generate_w1_key_image(self, team):
        keys = count_w1_keys(team)
        which_key_background = {
            0: '../images/world1/keys/key_board_1.png',
            1: '../images/world1/keys/key_board_2.png',
            2: '../images/world1/keys/key_board_3.png',
        }

        image_path = os.path.join(os.path.dirname(__file__), which_key_background[keys])
        image_path = os.path.abspath(image_path)
        with Image.open(image_path) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            if keys == 0:
                self.paste_image(base_img, f'../images/world1/olm_dialogue_1.png')
            elif keys == 1:
                self.paste_image(base_img, f'../images/world1/olm_dialogue_2.png')
            elif keys == 2:
                self.paste_image(base_img, f'../images/world1/olm_dialogue_3.png')
            self.draw_team_text(draw, team["team_name"])
            self.paste_image(base_img, '../images/key_tile.png', (20,16))
            self.paste_image(base_img, '../images/world1/key_tiles.png')
            tile_label = "Mystic Cove Trial"
            font = ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
    
    # Great olm boss
    def generate_w1_boss_image(self, team):
        image_path = os.path.join(os.path.dirname(__file__), '../images/world1/board/boss_background.png')
        image_path = os.path.abspath(image_path)
        tile_info = world1_tiles['boss_tile']
        with Image.open(image_path) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            self.draw_team_text(draw, team["team_name"])
            tile_label = "Mystic Cove Summit"
            self.paste_image(base_img, '../images/key_tile.png', (20,16))
            self.draw_tile_image(base_img, f'../images/world1/boss/0.png')
            self.paste_image(base_img, f'../images/world1/olm_dialogue_4.png')
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['tile_name'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES,
                max_width=330,
                fill="yellow",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['description'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.TILE_DESCRIPTION_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION,
                max_width=330,
                fill="white",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="left"
            )
            font = ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
        
    def generate_w2_key_image(self, team):
        current_path = team.get('w2_path_chosen', 0)
        where = {
            0: 'bottom',
            -1: 'left',
            1: 'right',
            2: 'top'
        }
        if current_path in where:
            image_path = os.path.join(os.path.dirname(__file__), f'../images/world2/keys/key_path_{where[current_path]}.png')
            image_path = os.path.abspath(image_path)

        with Image.open(image_path) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            self.draw_team_text(draw, team["team_name"])
            tile_label = "Tumeken's Trial"
            self.paste_image(base_img, '../images/key_tile.png', (20,16))
            font = ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
    
    def generate_w2_boss_image(self, team):
        image_path = os.path.join(os.path.dirname(__file__), '../images/world2/board/boss_background.png')
        image_path = os.path.abspath(image_path)
        tile_info = world2_tiles['boss_tile']
        with Image.open(image_path) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            self.draw_team_text(draw, team["team_name"])
            self.paste_image(base_img, '../images/key_tile.png', (20,16))
            tile_label = "Eclipse of the Sun"
            self.draw_tile_image(base_img, f'../images/world2/boss/0.png')
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['tile_name'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES,
                max_width=330,
                fill="yellow",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['description'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.TILE_DESCRIPTION_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION,
                max_width=330,
                fill="white",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="left"
            )
            font = ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
        
    def generate_w3_key_image(self, team):
        which_background = {
            0: '../images/world3/board/brazier_1.png',
            1: '../images/world3/board/brazier_2.png',
            2: '../images/world3/board/brazier_3.png',
            3: '../images/world3/board/brazier_3.png',
        }
        image_path = os.path.join(os.path.dirname(__file__), which_background[team.get('w3_braziers_lit', 0)])
        image_path = os.path.abspath(image_path)

        with Image.open(image_path) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            self.draw_team_text(draw, team["team_name"])
            tile_label = f"Withering Frostlands 1-T-{team.get('w3_braziers_lit', 0) + 1}"
            self.paste_image(base_img, '../images/w3_brazier.png', (20,16))
            font = ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io

    def generate_w3_boss_image(self, team):
        image_path = os.path.join(os.path.dirname(__file__), '../images/world3/board/boss_background.png')
        image_path = os.path.abspath(image_path)
        tile_info = world3_tiles['boss_tile']
        with Image.open(image_path) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            self.draw_team_text(draw, team["team_name"])
            self.paste_image(base_img, '../images/key_tile.png', (20,16))
            tile_label = "Zaros Sanctum"
            self.draw_tile_image(base_img, f'../images/world3/boss/0.png')
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['tile_name'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES,
                max_width=330,
                fill="yellow",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['description'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.TILE_DESCRIPTION_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION,
                max_width=330,
                fill="white",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="left"
            )
            font = ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
        
    def generate_w4_key_image(self, team):
        image_path = os.path.join(os.path.dirname(__file__), f'../images/world4/keys/trial_background.png')
        image_path = os.path.abspath(image_path)

        with Image.open(image_path) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            self.draw_team_text(draw, team["team_name"])
            tile_label = "Drakan's Trial"
            self.paste_image(base_img, '../images/key_tile.png', (20,16))
            font = ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
        
    def generate_w4_boss_image(self, team):
        image_path = os.path.join(os.path.dirname(__file__), '../images/world4/board/boss_background.png')
        image_path = os.path.abspath(image_path)
        tile_info = world4_tiles['boss_tile']
        with Image.open(image_path) as base_img:
            draw = ImageDraw.Draw(base_img)
            self.draw_ui_panel(base_img)
            self.draw_team_text(draw, team["team_name"])
            self.paste_image(base_img, '../images/key_tile.png', (20,16))
            tile_label = "It's not over til..."
            self.draw_tile_image(base_img, f'../images/world4/boss/0.png')
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['tile_name'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES,
                max_width=330,
                fill="yellow",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="center"
            )
            self.draw_outlined_wrapped_text(
                draw=draw,
                text=tile_info['description'],
                font=ImageFont.truetype(self.font_path, size=ImageSettings.TILE_DESCRIPTION_FONT_SIZE),
                position=ImageSettings.TILE_IMAGE_TEXT_COORDINATES_DESCRIPTION,
                max_width=330,
                fill="white",
                outline_fill="black",
                outline_range=2,
                line_spacing=2,
                align="left"
            )
            font = ImageFont.truetype(self.font_path, size=ImageSettings.LEVEL_TEXT_FONT_SIZE)
            draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), tile_label, fill="black", font=font, anchor="la", align="left")
            draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, tile_label, fill="white", font=font, anchor="la", align="left")
            img_io = BytesIO()
            base_img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
    
    def paste_image(self, base_img, path, location=(0,0)):
        img_path = os.path.join(os.path.dirname(__file__), path)
        img_path = os.path.abspath(img_path)
        with Image.open(img_path) as img:
            img = img.convert("RGBA")
            base_img.paste(img, location, img if img.mode == 'RGBA' else None)

    def draw_ui_panel(self, base_img):
        ui_img_path = os.path.join(os.path.dirname(__file__), f'../images/user_interface.png')
        ui_img_path = os.path.abspath(ui_img_path)
        with Image.open(ui_img_path) as ui_image:
            base_img.paste(ui_image, (0, 0), ui_image if ui_image.mode == 'RGBA' else None)

    def draw_tile_image(self, base_img, path, location=(0,0)):
        img_path = os.path.join(os.path.dirname(__file__), path)
        img_path = os.path.abspath(img_path)
        with Image.open(img_path) as img:
            img = img.convert("RGBA")
            img = img.resize(ImageSettings.TILE_IMAGE_SCALE, Image.NEAREST)
            outline_width = 2
            x, y = ImageSettings.TILE_IMAGE_COORDINATES
            mask = img.split()[-1] if img.mode == 'RGBA' else None
            black_img = Image.new("RGBA", img.size, (0, 0, 0, 255))
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx == 0 and dy == 0:
                        continue
                    base_img.paste(black_img, (x + dx, y + dy), mask)
            base_img.paste(img, ImageSettings.TILE_IMAGE_COORDINATES, mask)

    def draw_level_text(self, draw, level_name):
        font = ImageFont.truetype(self.font_path, size=ImageSettings.TEAM_TEXT_FONT_SIZE)
        text_color = (255, 255, 255)
        draw.text((ImageSettings.LEVEL_TEXT_COORDINATES[0]+4, ImageSettings.LEVEL_TEXT_COORDINATES[1] + 4), level_name, fill="black", font=font, anchor="la", align="left")
        draw.text(ImageSettings.LEVEL_TEXT_COORDINATES, level_name, fill=text_color, font=font, anchor="la", align="left")
    
    def draw_team_text(self, draw, team_name):
        font = ImageFont.truetype(self.font_path, size=ImageSettings.TEAM_TEXT_FONT_SIZE)
        draw.text((1904, 1004), text=team_name, font=font, fill="black", anchor="ra", align="right")
        draw.text((1900, 1000), text=team_name, font=font, fill="white", anchor="ra", align="right")

    def draw_outlined_wrapped_text(self, draw, text, font, position, max_width, fill="white", outline_fill="black", outline_range=2, line_spacing=4, align="left"):
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