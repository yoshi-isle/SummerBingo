from flask import Blueprint, request, jsonify, abort
from models.team import Team
from models.player import Player
from dataclasses import asdict
from flask import current_app as app
from constants.tiles import world1_tiles
from utils.shuffle import shuffle_tiles

submissions_blueprint = Blueprint('submissions', __name__)

def get_db():
    return app.config['DB']

@submissions_blueprint.route("/submissions", methods=["POST"])
def create_submission():
    """
    Create a new submission for a current tile.
    """
    db = get_db()
    data = request.get_json()

    # Insert the submission into the database
    result = db.teams.insert_one(submission)
    inserted_team = db.teams.find_one({"_id": result.inserted_id})

    # Convert ObjectId to string for JSON serialization
    if "_id" in inserted_team:
        inserted_team["_id"] = str(inserted_team["_id"])
    return jsonify(inserted_team), 201
