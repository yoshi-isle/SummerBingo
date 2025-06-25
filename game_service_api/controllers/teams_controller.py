from flask import Blueprint, request, jsonify, abort
from flask import current_app as app
from models.team import Team
from models.player import Player
from dataclasses import asdict
from constants.tiles import world1_tiles, world2_tiles, world3_tiles, world4_tiles
from utils.shuffle import shuffle_tiles
from bson import ObjectId

teams_blueprint = Blueprint('teams', __name__)

def get_db():
    return app.config['DB']

@teams_blueprint.route("/teams", methods=["POST"])
def create_team():
    """
    Create a new team with the provided data.
    Shuffles world tiles and assigns the first tile as the current tile.
    Returns the created team document.
    """
    db = get_db()
    data = request.get_json()

    # Create Player objects from the provided player data
    players = [Player(**p) for p in data["players"]]

    # Shuffle the world tiles for this team
    world1_shuffled_tiles = shuffle_tiles(world1_tiles["world_tiles"])
    world2_shuffled_tiles = shuffle_tiles(world2_tiles["world_tiles"])
    world3_shuffled_tiles = shuffle_tiles(world3_tiles["world_tiles"])
    world4_shuffled_tiles = shuffle_tiles(world4_tiles["world_tiles"])

    # Information for the first tile
    tile_info = next((t for t in world1_tiles["world_tiles"] if t["id"] == world1_shuffled_tiles[0]), None)

    # Create the Team object
    team = Team(
        team_name=data["team_name"],
        players=players,
        discord_channel_id=data["discord_channel_id"],
        current_tile=world1_shuffled_tiles[0],
        current_world=1,
        world1_shuffled_tiles=world1_shuffled_tiles,
        world2_shuffled_tiles=world2_shuffled_tiles,
        world3_shuffled_tiles=world3_shuffled_tiles,
        world4_shuffled_tiles=world4_shuffled_tiles,
        completion_counter=tile_info.get("completion_counter")
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
    db = get_db()
    team = db.teams.find_one({"team_name": team_name})
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
    db = get_db()
    team = db.teams.find_one({"players.discord_id": discord_user_id})
    if not team:
        abort(404, description="Team not found")

    # Team is already a dictionary from the service
    team_dict = team

    # Ensure players are returned as a list
    team_dict["players"] = [p for p in team_dict["players"]]

    # Convert ObjectId to string for JSON serialization
    if "_id" in team_dict:
        team_dict["_id"] = str(team_dict["_id"])

    return jsonify(team_dict), 200

@teams_blueprint.route("/teams/id/<team_id>", methods=["GET"])
def get_team_by_id(team_id):
    """
    Retrieve a team by its MongoDB ObjectId.
    Returns the team document if found, otherwise 404.
    """
    db = get_db()
    try:
        obj_id = ObjectId(team_id)
    except Exception:
        abort(400, description="Invalid team_id format")

    team = db.teams.find_one({"_id": obj_id})
    if not team:
        abort(404, description="Team not found")

    # Ensure players are returned as a list
    team["players"] = [p for p in team["players"]]

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])

    return jsonify(team), 200

@teams_blueprint.route("/teams/<team_id>/advance_tile", methods=["POST"])
def advance_tile(team_id):
    """
    Advance the team's current tile to the next one in their shuffled world1 tile list.
    Returns the updated team document, or an error if already at the last tile or tile not found.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")

    # Get the shuffled tiles and current tile
    current_tile = team.get("current_tile")
    current_world = team.get("current_world", 1)
    shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
    try:
        idx = shuffled_tiles.index(current_tile)
    except ValueError:
        abort(400, description="Current tile not found in shuffled tiles")

    # Check if already at the last tile
    if idx + 1 >= len(shuffled_tiles):
        abort(400, description="Already at last tile")

    # Advance to the next tile
    next_tile = shuffled_tiles[idx + 1]
    # Get the completion_counter for the new tile
    world_tiles_map = {
        1: world1_tiles["world_tiles"],
        2: world2_tiles["world_tiles"],
        3: world3_tiles["world_tiles"],
        4: world4_tiles["world_tiles"],
    }
    tile_info = next((t for t in world_tiles_map.get(current_world, []) if t["id"] == current_tile), None)
    completion_counter = tile_info.get("completion_counter") if tile_info else None
    db.teams.update_one({"_id": ObjectId(team_id)}, {"$set": {"current_tile": next_tile, "completion_counter": completion_counter}})
    team["current_tile"] = next_tile
    team["completion_counter"] = completion_counter

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
    current_tile = team['current_tile']
    current_world = team.get("current_world", 1)

    if isinstance(current_tile, dict):
        tile_id = current_tile['id']
        if tile_id is None:
            abort(400, description="Current tile missing id")
            
    elif isinstance(current_tile, int):
        tile_id = current_tile
    else:
        abort(400, description="Current tile has unexpected type")

    # Find the tile in world1_tiles["world_tiles"] with matching id
    world_tiles_map = {
        1: world1_tiles["world_tiles"],
        2: world2_tiles["world_tiles"],
        3: world3_tiles["world_tiles"],
        4: world4_tiles["world_tiles"],
    }
    tile_info = next((t for t in world_tiles_map.get(current_world, []) if t["id"] == current_tile), None)
    if not tile_info:
        abort(404, description="Tile info not found")
    return jsonify(tile_info), 200

@teams_blueprint.route("/teams/<id>/current_tile", methods=["GET"])
def get_current_tile_by_team_id(id):
    """
    Get the current tile's full info for a team's id.
    Returns the tile object from world1_tiles["world_tiles"] matching the current tile's id.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(id)})
    if not team:
        abort(404, description="Team not found")
    current_tile = team['current_tile']
    
    if isinstance(current_tile, dict):
        tile_id = current_tile['id']
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

@teams_blueprint.route("/teams/<discord_user_id>/world_level", methods=["GET"])
def get_world_level(discord_user_id):
    """
    Calculate the world's level based on the team's current tile position in the shuffled tile list.
    Returns the level as an integer (1-based index).
    """
    db = get_db()
    team = db.teams.find_one({"players.discord_id": discord_user_id})

    if not team:
        abort(404, description="Team not found")

    current_world = team.get("current_world", 1)

    shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
    current_tile = team.get("current_tile")
    idx = shuffled_tiles.index(current_tile)
    level = idx + 1
    return jsonify({"level": level}), 200

@teams_blueprint.route("/teams/id/<team_id>/world_level", methods=["GET"])
def get_world_level_by_team(team_id):
    """
    Calculate the world's level based on the team's current tile position in the shuffled tile list.
    Returns the level as an integer (1-based index).
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})

    if not team:
        abort(404, description="Team not found")
    
    current_world = team.get("current_world", 1)

    shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
    current_tile = team.get("current_tile")
    idx = shuffled_tiles.index(current_tile)
    level = idx + 1
    return jsonify({"level": level}), 200

@teams_blueprint.route("/teams/discord/<discord_id>/board_information", methods=["GET"])
def get_board_information(discord_id):
    db = get_db()
    team = db.teams.find_one({"players.discord_id": discord_id})
    if not team:
        abort(404, description=f"Team with id: {discord_id} not found")

    # Get level number
    shuffled_tiles = team.get("world1_shuffled_tiles", [])
    current_tile = team.get("current_tile")
    world = team.get("current_world")
    level_string = f"{world}-{shuffled_tiles.index(current_tile) + 1}"

    # Get tile information
    tile_info = next((t for t in world1_tiles["world_tiles"] if t["id"] == current_tile), None)

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])

    return jsonify({
        "level_number": level_string,
        "tile": tile_info,
        "team": team
    }), 200