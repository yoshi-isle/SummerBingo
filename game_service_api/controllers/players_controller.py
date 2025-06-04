from flask import Blueprint, request, jsonify, abort
from models.player import Player
from dataclasses import asdict
from flask import current_app as app

plyr_bp = Blueprint('players', __name__)

def get_db():
    return app.config['DB']

@plyr_bp.route("/players", methods=["POST"])
def create_player():
    db = get_db()
    data = request.get_json()
    player = Player(**data)
    db.players.insert_one(asdict(player))
    return jsonify(asdict(player)), 201

@plyr_bp.route("/players/<discord_id>", methods=["GET"])
def get_player(discord_id):
    db = get_db()
    player = db.players.find_one({"discord_id": discord_id})
    if not player:
        abort(404, description="Player not found")
    return jsonify(player), 200
