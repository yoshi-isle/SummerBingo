from flask import Blueprint, request, jsonify, abort
from models.team import Team
from models.player import Player
from dataclasses import asdict
from flask import current_app as app
from constants.tiles import world1_tiles
from utils.shuffle import shuffle_tiles
from services.team_service import TeamService

team_service = TeamService()
teams_blueprint = Blueprint('teams', __name__)

def get_db():
    return app.config['DB']

@teams_blueprint.route("/teams", methods=["POST"])
def create_team():
    """
    Create a new team with the provided data.
    Shuffles world1 tiles and assigns the first tile as the current tile.
    Returns the created team document.
    """
    db = get_db()
    data = request.get_json()

    # Create Player objects from the provided player data
    players = [Player(**p) for p in data["players"]]

    # Shuffle the world1 tiles for this team
    world1_shuffled_tiles = shuffle_tiles(world1_tiles["world_tiles"])

    # Create the Team object
    team = Team(
        team_name=data["team_name"],
        players=players,
        discord_channel_id=data["discord_channel_id"],
        current_tile=world1_shuffled_tiles[0],
        current_world=1,
        world1_shuffled_tiles=world1_shuffled_tiles
    )

    # Convert the Team and Player objects to dictionaries for MongoDB
    team_dict = asdict(team)
    team_dict["players"] = [asdict(p) for p in team.players]

    # Insert the team into the database
    result = db.teams.insert_one(team_dict)
    inserted_team = db.teams.find_one({"_id": result.inserted_id})

    # Convert ObjectId to string for JSON serialization
    if "_id" in inserted_team:
        inserted_team["_id"] = str(inserted_team["_id"])
    return jsonify(inserted_team), 201

@teams_blueprint.route("/teams/<team_name>", methods=["GET"])
def get_team(team_name):
    """
    Retrieve a team by its name.
    Returns the team document if found, otherwise 404.
    """
    team = team_service.get_team_by_name(team_name)
    if not team:
        abort(404, description="Team not found")

    # Ensure players are returned as a list
    team["players"] = [p for p in team["players"]]

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
    return jsonify(team), 200

@teams_blueprint.route("/teams/discord/<discord_user_id>", methods=["GET"])
def get_team_by_discord_id(discord_user_id):
    """
    Retrieve a team by a discord user id.
    Returns the team document if found, otherwise 404.
    """
    team = team_service.get_team_by_discord_id(discord_user_id)
    if not team:
        abort(404, description="Team not found")

    # Ensure players are returned as a list
    team["players"] = [p for p in team["players"]]

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
        
    return jsonify(team), 200

@teams_blueprint.route("/teams/<team_name>/advance_tile", methods=["POST"])
def advance_tile(team_name):
    """
    Advance the team's current tile to the next one in their shuffled world1 tile list.
    Returns the updated team document, or an error if already at the last tile or tile not found.
    """
    db = get_db()
    team = db.teams.find_one({"team_name": team_name})
    if not team:
        abort(404, description="Team not found")

    # Get the shuffled tiles and current tile
    shuffled_tiles = team.get("world1_shuffled_tiles", [])
    current_tile = team.get("current_tile")
    try:
        idx = shuffled_tiles.index(current_tile)
    except ValueError:
        abort(400, description="Current tile not found in shuffled tiles")

    # Check if already at the last tile
    if idx + 1 >= len(shuffled_tiles):
        abort(400, description="Already at last tile")

    # Advance to the next tile
    next_tile = shuffled_tiles[idx + 1]
    db.teams.update_one({"team_name": team_name}, {"$set": {"current_tile": next_tile}})
    team["current_tile"] = next_tile

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
    return jsonify(team), 200

@teams_blueprint.route("/teams/discord/<discord_user_id>/current_tile", methods=["GET"])
def get_current_tile_by_discord_id(discord_user_id):
    """
    Get the current tile's full info for a team by discord user id.
    Returns the tile object from world1_tiles["world_tiles"] matching the current tile's id.
    """
    db = get_db()
    team = db.teams.find_one({"players.discord_id": discord_user_id})
    if not team:
        abort(404, description="Team not found")

    current_tile = team.get("current_tile")
    
    # Handle if current_tile is a dict or just an int (id)
    if not current_tile:
        abort(400, description="Current tile not set")
    if isinstance(current_tile, dict):
        tile_id = current_tile.get("id")
        if tile_id is None:
            abort(400, description="Current tile missing id")
    elif isinstance(current_tile, int):
        tile_id = current_tile
    else:
        abort(400, description="Current tile has unexpected type")

    # Find the tile in world1_tiles["world_tiles"] with matching id
    tile_info = next((t for t in world1_tiles["world_tiles"] if t["id"] == tile_id), None)
    if not tile_info:
        abort(404, description="Tile info not found")
    return jsonify(tile_info), 200
