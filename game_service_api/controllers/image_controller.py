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