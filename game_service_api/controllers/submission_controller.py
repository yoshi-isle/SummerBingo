from flask import Blueprint, request, jsonify, abort
from models.team import Team
from models.player import Player
from models.submission import Submission
from flask import current_app as app
from constants.tiles import world1_tiles
from utils.shuffle import shuffle_tiles

submissions_blueprint = Blueprint('submissions', __name__)

def get_db():
    return app.config['DB']

@submissions_blueprint.route("/submission", methods=["POST"])
def create_submission():
    """
    Create a new submission for a current tile.
    """
    db = get_db()
    data = request.get_json()

    # Insert the submission into the database directly
    result = db.submissions.insert_one(data)

    # Return the inserted object as a dict (with its new id)
    data['_id'] = str(result.inserted_id)

    return jsonify(data), 201
