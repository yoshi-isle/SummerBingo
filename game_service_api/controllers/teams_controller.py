from flask import Blueprint, request, jsonify, abort
from flask import current_app as app
from models.team import Team
from models.player import Player
from dataclasses import asdict
from constants.tiles import world1_tiles, world2_tiles, world3_tiles, world4_tiles
from constants.key_tiles import key_tiles
from utils.shuffle import shuffle_tiles
from bson import ObjectId
from datetime import datetime, timezone

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
        completion_counter=tile_info.get("completion_counter"),
        game_state=0,
        w1key1_completion_counter=1,
        w1key2_completion_counter=1,
        w1key3_completion_counter=4,
        w1key4_completion_counter=1,
        w1key5_completion_counter=10,
        w1boss_completion_counter=1,
        w2boss_completion_counter=1,
        w3boss_completion_counter=2,
        w4boss_completion_counter=5,
        last_rolled_at=datetime.now(timezone.utc),
        w2key1_completion_counter=1,
        w2key2_completion_counter=5,
        w2key3_completion_counter=1,        
        w2key4_completion_counter=3,
        w2key5_completion_counter=1,
        w2_path_chosen=0,
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

    # Reset the last rolled time
    db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": {"last_rolled_at": datetime.now(timezone.utc)}}
    )

    # World 2 - key complete
    if current_world == 2 and team.get("game_state") == 1:
        db.teams.update_one(
            {"_id": ObjectId(team_id)}, 
            {"$set": 
             {"game_state": 0,
              "current_tile": shuffled_tiles[7],
              "last_rolled_at": datetime.now(timezone.utc)}
            })
        # Convert ObjectId to string for JSON serialization
        if "_id" in team:
            team["_id"] = str(team["_id"])
        return jsonify(team), 200

    # Check if on a key tile to update gamestate
    key_tile_level_index = key_tiles[current_world]
    if idx + 1 in key_tile_level_index:
        db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": 
         {"game_state": 1,
        },
        })
        # Convert ObjectId to string for JSON serialization
        if "_id" in team:
            team["_id"] = str(team["_id"])
        return jsonify(team), 200

    # World 2 and 3 - go to boss fight
    if current_world in [2, 3] and idx + 1 == len(shuffled_tiles):
        db.teams.update_one(
            {"_id": ObjectId(team_id)}, 
            {"$set": 
             {"game_state": 2,
              "last_rolled_at": datetime.now(timezone.utc)}
            })
        # Convert ObjectId to string for JSON serialization
        if "_id" in team:
            team["_id"] = str(team["_id"])
        return jsonify(team), 200

    if idx + 1 >= len(shuffled_tiles):
        abort(400, description="Already at last tile")

    # Advance to the next tile
    next_tile = shuffled_tiles[idx + 1]
    tile_info = get_tile_info(current_world, next_tile)
    completion_counter = tile_info.get("completion_counter") if tile_info else None
    db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": 
         {"current_tile": next_tile,
          "completion_counter": completion_counter}
        })
    team["current_tile"] = next_tile
    team["completion_counter"] = completion_counter

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
    return jsonify(team), 200

@teams_blueprint.route("/teams/<team_id>/boss_tile", methods=["PUT"])
def advance_to_boss_tile(team_id):
    """
    Puts the team at the boss tile of the world.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")

    db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": 
         {"game_state": 2}
        })
        # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
    return jsonify(team), 200
    

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

    tile_info = get_tile_info(int(team['current_world']), int(team['current_tile']))
    if not tile_info:
        abort(404, description="Tile info not found")
    return jsonify(tile_info), 200

@teams_blueprint.route("/teams/<team_id>/key/<id>", methods=["GET"])
def get_key_tile(team_id, id):
    """
    Get key tile by id
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})

    if not team:
        abort(404, description="Team not found")
    
    current_world = team.get("current_world", 1)

    return jsonify({
        "key_tile": get_key_tile_info(current_world, id),
    }), 200

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

@teams_blueprint.route("/teams/id/<team_id>/board_information", methods=["GET"])
def get_board_information_by_team_id(team_id):
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description=f"Team with id: {team_id} not found")

    # Get level number
    current_tile = team.get("current_tile")
    current_world = team.get("current_world", 1)
    shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
    level_string = f"{current_world}-{shuffled_tiles.index(current_tile) + 1}"

    tile_info = get_tile_info(current_world, current_tile)

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])

    return jsonify({
        "level_number": level_string,
        "tile": tile_info,
        "team": team,
        "w1key1_completion_counter": team["w1key1_completion_counter"],
        "w1key2_completion_counter": team["w1key2_completion_counter"],
        "w1key3_completion_counter": team["w1key3_completion_counter"],
        "w1key4_completion_counter": team["w1key4_completion_counter"],
        "w1key5_completion_counter": team["w1key5_completion_counter"],
    }), 200

@teams_blueprint.route("/teams/<team_id>/<option>/w2_trial_traverse_path", methods=["PUT"])
def set_w2_trial_path_chosen(team_id, option):
    """
    Sets the W2 trial path chosen by the team.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")
    option = int(option)
    path_chosen = 0
    if option == 1:
        path_chosen = -1
    elif option == 2:
        path_chosen = 1
    elif option == 3:
        path_chosen = 2
    elif option == 4:
        path_chosen = 2

    db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": {"w2_path_chosen": path_chosen}}
    )

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
    
    return jsonify({
        "message": f"W2 trial path set to {option}",
        "team": team
    }), 200

@teams_blueprint.route("/teams/<team_id>/complete_w2_trial", methods=["PUT"])
def complete_w2_trial(team_id):
    """
    Completes the W2 trial
    Resets game_state to 0 and sets current_tile to shuffledw2tiles at index 8
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")

    # Get the shuffled tiles and current tile
    current_world = team.get("current_world", 1)
    next_world_shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])

    # Set the current tile to the 8th tile in the shuffled list
    next_tile = next_world_shuffled_tiles[7]

    # calculate completion counter from the tile index
    tile_info = get_tile_info(current_world, next_tile)
    completion_counter = tile_info.get("completion_counter") if tile_info else None

    db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": {
            "game_state": 0,
            "current_tile": next_tile,
            "completion_counter": completion_counter,
            "last_rolled_at": datetime.now(timezone.utc)
        }
    })

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
    
    return jsonify(team), 200

@teams_blueprint.route("/teams/<team_id>/<brazier_number>/complete_w3_trial", methods=["PUT"])
def complete_w3_trial(team_id, brazier_number):
    """
    Completes the W3 trial by lighting a brazier.
    Resets game_state to 0 and sets current_tile to a tile based on the brazier lit.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")

    which_tile_to_go_to_based_on_brazier = {
        0: 5,
        1: 10,
        2: 15
    }

    # Get the shuffled tiles and current tile
    current_world = team.get("current_world", 1)
    world_shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])

    next_tile = world_shuffled_tiles[which_tile_to_go_to_based_on_brazier[int(brazier_number)]]

    # calculate completion counter from the tile index
    tile_info = get_tile_info(current_world, next_tile)
    completion_counter = tile_info.get("completion_counter") if tile_info else None

    # Update the brazier lit count
    brazier_lit_count = team.get('w3_braziers_lit', 0) + 1

    db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": {
            "game_state": 0,
            "current_tile": next_tile,
            "completion_counter": completion_counter,
            "last_rolled_at": datetime.now(timezone.utc),
            "w3_braziers_lit": brazier_lit_count
        }
    })

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
    
    return jsonify(team), 200

@teams_blueprint.route("/teams/<team_id>/next_world", methods=["PUT"])
def advance_to_next_world(team_id):
    """
    Puts the team at the next world.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")

    # Get the shuffled tiles and current tile
    next_world = team.get("current_world", 1) + 1
    next_world_shuffled_tiles = team.get(f"world{next_world}_shuffled_tiles", [])
    
    tile_info = get_tile_info(next_world, next_world_shuffled_tiles[0])
    completion_counter = tile_info.get("completion_counter") if tile_info else None

    db.teams.update_one(
    {"_id": ObjectId(team_id)}, 
    {"$set": 
        {"game_state": 0,
         "current_world": next_world,
         "current_tile": next_world_shuffled_tiles[0],
         "completion_counter": completion_counter}
    })
    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])
    return jsonify(team), 200

@teams_blueprint.route("/teams/<team_id>/last_rolled", methods=["GET"])
def get_last_rolled(team_id):

    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")

    last_rolled_at = team.get('last_rolled_at')
    if not last_rolled_at:
        abort(404, description="last_rolled_at not found")

    if not isinstance(last_rolled_at, datetime):
        last_rolled_at = datetime.fromisoformat(str(last_rolled_at))

    if last_rolled_at.tzinfo is None or last_rolled_at.tzinfo.utcoffset(last_rolled_at) is None:
        last_rolled_at = last_rolled_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    minutes_ago = int((now - last_rolled_at).total_seconds() // 60)
    discord_relative = f"<t:{int(last_rolled_at.timestamp())}:R>"

    return jsonify({
        "last_rolled": last_rolled_at.isoformat(),
        "minutes_ago": minutes_ago,
        "discord_relative": discord_relative
    }), 200

@teams_blueprint.route("/game_started", methods=["GET"])
def get_game_started():

    db = get_db()
    running = db.global_game_state.find_one({"running": 1})
    return jsonify({
        "running": running != None
    }), 200

def get_tile_info(current_world: int, current_tile:int):
    world_tiles_map = {
        1: world1_tiles["world_tiles"],
        2: world2_tiles["world_tiles"],
        3: world3_tiles["world_tiles"],
        4: world4_tiles["world_tiles"],
    }

    return next((t for t in world_tiles_map.get(current_world, []) if t["id"] == current_tile), None)

def get_key_tile_info(current_world: int, tile):
    key_tiles_map = {
        1: world1_tiles["key_tiles"],
        2: world2_tiles["key_tiles"],
        3: world3_tiles["key_tiles"],
        4: world4_tiles["key_tiles"],
    }

    tile_id = int(tile)

    return next((t for t in key_tiles_map.get(current_world, []) if t["id"] == tile_id), None)
