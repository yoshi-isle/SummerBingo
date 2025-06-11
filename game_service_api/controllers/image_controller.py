from flask import Blueprint, request, jsonify, abort
from services.team_service import TeamService
from models.team import Team
from models.player import Player
from dataclasses import asdict
from flask import current_app as app
from constants.tiles import world1_tiles
from utils.shuffle import shuffle_tiles
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

team_service = TeamService()
image_blueprint = Blueprint('image', __name__)

@image_blueprint.route("/image/user/<discord_id>", methods=["GET"])
def generate_image(discord_id):
    """
    Creates a board image for the given Discord user ID.
    """
    team = team_service.get_team_by_discord_id(discord_id)
    image_path = os.path.join(os.path.dirname(__file__), '../images/world1/board/board_background.png')
    image_path = os.path.abspath(image_path)
    with Image.open(image_path) as base_img:
        img_io = BytesIO()
        base_img.save(img_io, 'PNG')
        img_io.seek(0)
        return app.response_class(img_io, mimetype='image/png')

