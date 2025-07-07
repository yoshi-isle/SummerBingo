import os
from PIL import ImageFont

from constants.image_settings import ImageSettings

def draw_team_text(draw, team_name):
    font_path = os.path.join(os.path.dirname(__file__), f"../{ImageSettings.FONT}")
    font_path = os.path.abspath(font_path)

    font = ImageFont.truetype(font_path, size=ImageSettings.TEAM_TEXT_FONT_SIZE)
    draw.text((1904, 1004), text=team_name, font=font, fill="black", anchor="ra", align="right")
    draw.text((1900, 1000), text=team_name, font=font, fill="white", anchor="ra", align="right")