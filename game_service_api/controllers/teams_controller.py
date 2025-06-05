from flask import Blueprint, request, jsonify, abort
from models.team import Team
from models.player import Player
from dataclasses import asdict
from flask import current_app as app
from constants.tiles import world1_tiles
from utils.shuffle import shuffle_tiles

teams_blueprint = Blueprint('teams', __name__)

def get_db():
    return app.config['DB']

@teams_blueprint.route("/teams", methods=["POST"])
def create_team():
    db = get_db()
    data = request.get_json()
    players = [Player(**p) for p in data["players"]]
    world1_shuffled_tiles = shuffle_tiles(world1_tiles["world_tiles"])
    team = Team(
        team_name=data["team_name"],
        players=players,
        discord_channel_id=data["discord_channel_id"],
        current_tile=world1_shuffled_tiles[0],
        current_world=1,
        world1_shuffled_tiles=world1_shuffled_tiles
    )
    team_dict = asdict(team)
    team_dict["players"] = [asdict(p) for p in team.players]
    result = db.teams.insert_one(team_dict)
    inserted_team = db.teams.find_one({"_id": result.inserted_id})
    if "_id" in inserted_team:
        inserted_team["_id"] = str(inserted_team["_id"])
    return jsonify(inserted_team), 201

@teams_blueprint.route("/teams/<team_name>", methods=["GET"])
def get_team(team_name):
    db = get_db()
    team = db.teams.find_one({"team_name": team_name})
    if not team:
        abort(404, description="Team not found")
    team["players"] = [p for p in team["players"]]
    if "_id" in team:
        team["_id"] = str(team["_id"])
    return jsonify(team), 200

@teams_blueprint.route("/teams/<team_name>/advance_tile", methods=["POST"])
def advance_tile(team_name):
    db = get_db()
    team = db.teams.find_one({"team_name": team_name})
    if not team:
        abort(404, description="Team not found")
    shuffled_tiles = team.get("world1_shuffled_tiles", [])
    print(shuffled_tiles)
    current_tile = team.get("current_tile")
    try:
        idx = shuffled_tiles.index(current_tile)
    except ValueError:
        abort(400, description="Current tile not found in shuffled tiles")
    if idx + 1 >= len(shuffled_tiles):
        abort(400, description="Already at last tile")
    next_tile = shuffled_tiles[idx + 1]
    db.teams.update_one({"team_name": team_name}, {"$set": {"current_tile": next_tile}})
    team["current_tile"] = next_tile
    if "_id" in team:
        team["_id"] = str(team["_id"])
    return jsonify(team), 200
