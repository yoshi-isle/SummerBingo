import os
from PIL import Image

def draw_ui_panel(base_img):
    ui_img_path = os.path.join(os.path.dirname(__file__), f'../../images/user_interface.png')
    ui_img_path = os.path.abspath(ui_img_path)
    with Image.open(ui_img_path) as ui_image:
        base_img.paste(ui_image, (0, 0), ui_image if ui_image.mode == 'RGBA' else None)