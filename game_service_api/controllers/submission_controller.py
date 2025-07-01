from flask import Blueprint, request, jsonify, abort
from flask import current_app as app
from bson.objectid import ObjectId

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

@submissions_blueprint.route("/key_submission", methods=["POST"])
def create_key_tile_submission():
    """
    Create a new submission for a key tile.
    """
    db = get_db()
    data = request.get_json()

    # Insert the submission into the database directly
    result = db.key_submissions.insert_one(data)

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

@submissions_blueprint.route("/key_submission/<message_id>", methods=["GET"])
def get_key_submission_by_message_id(message_id):
    """
    Retrieve a submission by its admin_approval_embed_id or pending_team_embed_id.
    """
    db = get_db()
    submission = db.key_submissions.find_one({
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

@submissions_blueprint.route("/submission/approve/<submission_id>", methods=["PUT"])
def approve_submission(submission_id):
    """
    Approve a submission by its ID.
    """
    db = get_db()
    try:
        submission = db.submissions.find_one({"_id": ObjectId(submission_id)})
    except Exception:
        abort(400, description="Invalid submission ID format")
    if not submission:
        abort(404, description="Submission not found")

    # Find the team associated with the submission
    team_id = submission.get("team_id")
    if not team_id:
        abort(400, description="Submission does not have a team_id")

    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description=f"Team not found, {team_id}")
    
    # Update the submission status to approved
    db.submissions.update_one({"_id": ObjectId(submission_id)}, {"$set": {"approved": True}})

    if team["current_world"] != submission["current_world"] or team["current_tile"] != submission["current_tile"]:
        return jsonify({
            "message": "Submission ignored: team's position has changed since submission.",
        }), 208  # 208 Already Reported

    # Decrement the team's completion counter by 1
    db.teams.update_one(
        {"_id": ObjectId(team_id)},
        {"$inc": {"completion_counter": -1}}
    )

    return jsonify({"message": "Submission approved successfully"}), 200

@submissions_blueprint.route("/submission/approve_key/<key_id>/<submission_id>", methods=["PUT"])
def approve_key_submission(key_id, submission_id):
    """
    Approve a submission by its ID.
    """
    db = get_db()
    try:
        submission = db.key_submissions.find_one({"_id": ObjectId(submission_id)})
    except Exception:
        abort(400, description="Invalid submission ID format")
    if not submission:
        abort(404, description="Submission not found")

    # Find the team associated with the submission
    team_id = submission.get("team_id")
    if not team_id:
        abort(400, description="Submission does not have a team_id")

    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description=f"Team not found, {team_id}")
    
    # Update the submission status to approved
    db.key_submissions.update_one({"_id": ObjectId(submission_id)}, {"$set": {"approved": True}})

    # Decrement the team's completion counter by 1
    db.teams.update_one(
        {"_id": ObjectId(team_id)},
        {"$inc": {f"w1key{int(key_id)}_completion_counter": -1}}
    )

    return jsonify({"message": "Key submission approved successfully"}), 200

@submissions_blueprint.route("/submission/deny/<submission_id>", methods=["PUT"])
def deny_submission(submission_id):
    """
    Deny a submission by its ID.
    """
    db = get_db()
    try:
        submission = db.submissions.find_one({"_id": ObjectId(submission_id)})
    except Exception:
        abort(400, description="Invalid submission ID format")
    if not submission:
        abort(404, description="Submission not found")

    # Update the submission status to approved
    db.submissions.update_one({"_id": ObjectId(submission_id)}, {"$set": {"approved": False}})

    return jsonify({"message": "Submission approved successfully"}), 200