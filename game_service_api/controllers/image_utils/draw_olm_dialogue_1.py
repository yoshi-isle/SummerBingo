import os
from PIL import Image

def draw_olm_dialogue_1(base_img):
    olm_dialogue_1_image_path = os.path.join(os.path.dirname(__file__), f'../../images/world1/olm_dialogue_1.png')
    olm_dialogue_1_image_path = os.path.abspath(olm_dialogue_1_image_path)
    with Image.open(olm_dialogue_1_image_path) as olm_dialogue_1_image:
        base_img.paste(olm_dialogue_1_image, (0, 0), olm_dialogue_1_image if olm_dialogue_1_image.mode == 'RGBA' else None)