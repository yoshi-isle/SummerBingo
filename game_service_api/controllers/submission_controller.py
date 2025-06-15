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

@submissions_blueprint.route("/submission/<message_id>", methods=["GET"])
def get_submission_by_message_id(message_id):
    """
    Retrieve a submission by its admin_approval_embed_id or pending_team_embed_id.
    """
    db = get_db()
    submission = db.submissions.find_one({
        "$or": [
            {"admin_approval_embed_id": message_id},
            {"pending_team_embed_id": message_id}
        ]
    })
    if not submission:
        abort(404, description="Submission not found")
        
    # Convert ObjectId to string for JSON serialization
    submission["_id"] = str(submission["_id"])
    return jsonify(submission)

