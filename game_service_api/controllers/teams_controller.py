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
        last_rolled_at=datetime.now(timezone.utc),
        w2_path_chosen=0,
        team_image_path=data.get("team_image_path", "1.png"),
        thumbnail_url=data.get("thumbnail_url", ""),

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

def get_teams_in_first_place(teams):
    """
    Get all team IDs that are currently in 1st place (tied for first).
    Returns a set of team ID strings.
    """
    if not teams:
        return set()
    
    # Calculate levels for all teams and find the best position
    best_world = 0
    best_level = 0
    best_game_state = 0
    
    for team in teams:
        current_world = team.get("current_world", 1)
        current_tile = team.get("current_tile")
        shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
        try:
            tile_index = shuffled_tiles.index(current_tile)
            level = tile_index + 1
        except ValueError:
            level = 1
        
        game_state = team.get("game_state", 0)
        effective_game_state = get_effective_game_state(game_state, current_world)
        
        # Check if this team has a better position
        if (current_world > best_world or 
            (current_world == best_world and level > best_level) or
            (current_world == best_world and level == best_level and effective_game_state > best_game_state)):
            best_world = current_world
            best_level = level
            best_game_state = effective_game_state
    
    # Find all teams that match the best position
    first_place_teams = set()
    for team in teams:
        current_world = team.get("current_world", 1)
        current_tile = team.get("current_tile")
        shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
        try:
            tile_index = shuffled_tiles.index(current_tile)
            level = tile_index + 1
        except ValueError:
            level = 1
        
        game_state = team.get("game_state", 0)
        effective_game_state = get_effective_game_state(game_state, current_world)
        
        if (current_world == best_world and level == best_level and effective_game_state == best_game_state):
            first_place_teams.add(str(team["_id"]))
    
    return first_place_teams

def handle_dethronement_check(db, teams_in_first_before):
    """
    Check for teams that were dethroned and reset their last_rolled_at timer.
    """
    # Get updated team rankings after the advancement
    all_teams_after = list(db.teams.find({}))
    teams_in_first_after = get_teams_in_first_place(all_teams_after)
    
    # Find teams that were in first before but not after (dethroned teams)
    dethroned_teams = teams_in_first_before - teams_in_first_after
    
    # Reset last_rolled_at for dethroned teams
    if dethroned_teams:
        dethroned_object_ids = [ObjectId(team_id_str) for team_id_str in dethroned_teams]
        db.teams.update_many(
            {"_id": {"$in": dethroned_object_ids}},
            {"$set": {"last_rolled_at": datetime.now(timezone.utc)}}
        )

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

    # Get all teams and determine who is currently in 1st place BEFORE advancement
    all_teams = list(db.teams.find({}))
    teams_in_first_before = get_teams_in_first_place(all_teams)

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
        
        # Check for dethronement after advancement
        handle_dethronement_check(db, teams_in_first_before)
        
        # Convert ObjectId to string for JSON serialization
        if "_id" in team:
            team["_id"] = str(team["_id"])
        return jsonify(team), 200

    # # World 4 - go to key
    # if current_world == 4 and team.get("game_state") == 0:
    #     db.teams.update_one(
    #         {"_id": ObjectId(team_id)}, 
    #         {"$set": 
    #          {"game_state": 1,
    #           "last_rolled_at": datetime.now(timezone.utc)}
    #         })
    #     # Convert ObjectId to string for JSON serialization
    #     if "_id" in team:
    #         team["_id"] = str(team["_id"])
    #     return jsonify(team), 200

    # Check if on a key tile to update gamestate
    key_tile_level_index = key_tiles[current_world]
    if idx + 1 in key_tile_level_index:
        db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": 
         {"game_state": 1,
        },
        })
        
        # Check for dethronement after advancement
        handle_dethronement_check(db, teams_in_first_before)
        
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
        
        # Check for dethronement after advancement
        handle_dethronement_check(db, teams_in_first_before)
        
        # Convert ObjectId to string for JSON serialization
        if "_id" in team:
            team["_id"] = str(team["_id"])
        return jsonify(team), 200

    if idx + 1 >= len(shuffled_tiles):
        if current_world == 4:
            db.teams.update_one(
                {"_id": ObjectId(team_id)}, 
                {"$set": 
                 {"game_state": 1,
                  "last_rolled_at": datetime.now(timezone.utc)}
                })
            
            # Check for dethronement after advancement
            handle_dethronement_check(db, teams_in_first_before)
            
            # Convert ObjectId to string for JSON serialization
            if "_id" in team:
                team["_id"] = str(team["_id"])
            return jsonify(team), 200
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

    # Check for dethronement after advancement
    handle_dethronement_check(db, teams_in_first_before)

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

    # Get team placement
    teams = list(db.teams.find({}))
    placement = calculate_team_placement(team_id, teams)

    # Convert ObjectId to string for JSON serialization
    if "_id" in team:
        team["_id"] = str(team["_id"])

    return jsonify({
        "level_number": level_string,
        "tile": tile_info,
        "team": team,
        "placement": placement,
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

@teams_blueprint.route("/teams/<team_id>/complete_w4_trial", methods=["PUT"])
def complete_w4_trial(team_id):
    """
    Completes the W4 trial and advances to the final boss
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")

    # Get the shuffled tiles and current tile
    current_world = team.get("current_world", 1)
    world_shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])

    next_tile = world_shuffled_tiles[0]

    # calculate completion counter from the tile index
    tile_info = get_tile_info(current_world, next_tile)
    completion_counter = tile_info.get("completion_counter") if tile_info else None

    db.teams.update_one(
        {"_id": ObjectId(team_id)}, 
        {"$set": {
            "game_state": 2,
            "last_rolled_at": datetime.now(timezone.utc)
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

@teams_blueprint.route("/teams/<team_id>/placement", methods=["GET"])
def get_team_placement(team_id):
    """
    Get the placement/ranking of a specific team in the leaderboard.
    Returns the team's position (1st, 2nd, 3rd, etc.) based on world, level progress, and tie breakers.
    Tie breakers: world (desc), level (desc), game_state (desc with world 3 adjustments).
    """
    db = get_db()
    
    # Get the specific team first
    target_team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not target_team:
        abort(404, description="Team not found")
    
    # Get all teams and calculate placement
    teams = list(db.teams.find({}))
    placement = calculate_team_placement(team_id, teams)
    
    if placement is None:
        abort(404, description="Team not found in placement calculation")
    
    return jsonify({
        "placement": placement,
    })


@teams_blueprint.route("/teams", methods=["GET"])
def get_all_teams():
    """
    Retrieve all teams for leaderboard purposes.
    Returns all team documents with calculated level information.
    """
    db = get_db()
    teams = list(db.teams.find({}))
    
    for team in teams:
        # Calculate current level for each team
        current_world = team.get("current_world", 1)
        current_tile = team.get("current_tile")
        shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
        
        try:
            tile_index = shuffled_tiles.index(current_tile)
            level = tile_index + 1
            team["current_level"] = f"{current_world}-{level}"
            team["world_number"] = current_world
            team["level_number"] = level
        except ValueError:
            # If current_tile not found in shuffled_tiles, default to level 1
            team["current_level"] = f"{current_world}-1"
            team["world_number"] = current_world
            team["level_number"] = 1
        
        # Convert ObjectId to string for JSON serialization
        if "_id" in team:
            team["_id"] = str(team["_id"])
    
    # Sort teams by world (descending) then by level (descending) for leaderboard order
    teams.sort(key=lambda x: (x["world_number"], x["level_number"]), reverse=True)
    
    return jsonify(teams)

@teams_blueprint.route("/teams/<team_id>/update_w4_trial_iteration", methods=["PUT"])
def update_w4_trial_iteration(team_id):
    """
    Updates the W4 trial iteration for the team.
    Returns the updated iteration number.
    """
    db = get_db()
    team = db.teams.find_one({"_id": ObjectId(team_id)})
    if not team:
        abort(404, description="Team not found")

    # Increment the W4 trial iteration
    current_iteration = team.get("w4_trial_iteration", 0)
    new_iteration = current_iteration + 1
    db.teams.update_one(
        {"_id": ObjectId(team_id)},
        {"$set": {"w4_trial_iteration": new_iteration}}
    )

    return jsonify({
        "w4_trial_iteration": new_iteration
    })

@teams_blueprint.route("/sync_reroll_timers", methods=["PUT"])
def sync_reroll_timers():
    """
    Synchronizes all teams' last_rolled_at field to the current time.
    Useful for resetting timers when the event starts.
    """
    db = get_db()
    
    # Update all teams' last_rolled_at to current time
    result = db.teams.update_many(
        {},  # Empty filter to match all teams
        {"$set": {"last_rolled_at": datetime.now(timezone.utc)}}
    )
    
    return jsonify({
        "message": f"Successfully synchronized reroll timers for {result.modified_count} teams",
        "teams_updated": result.modified_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200

def get_effective_game_state(game_state, world):
    """
    Adjust game state for world 3 (exclude game state 1 checks)
    For world 3, treat game state 1 as 0, but keep game state 2 as 2
    """
    if world == 3 and game_state == 1:
        return 0  # Treat game state 1 as 0 for world 3
    return game_state

def calculate_team_placement(target_team_id, teams):
    """
    Calculate the placement/ranking of a specific team in the leaderboard.
    Returns the team's position (1st, 2nd, 3rd, etc.) based on world, level progress, and tie breakers.
    Tie breakers: world (desc), level (desc), game_state (desc with world 3 adjustments).
    """
    
    # Find the target team
    target_team = None
    for team in teams:
        if str(team["_id"]) == target_team_id:
            target_team = team
            break
    
    if not target_team:
        return None
    
    # Calculate levels for all teams
    for team in teams:
        current_world = team.get("current_world", 1)
        current_tile = team.get("current_tile")
        shuffled_tiles = team.get(f"world{current_world}_shuffled_tiles", [])
        try:
            tile_index = shuffled_tiles.index(current_tile)
            level = tile_index + 1
            team["world_number"] = current_world
            team["level_number"] = level
        except ValueError:
            team["world_number"] = current_world
            team["level_number"] = 1
    
    # Get target team info
    target_world = target_team.get("current_world", 1)
    target_tile = target_team.get("current_tile")
    target_shuffled_tiles = target_team.get(f"world{target_world}_shuffled_tiles", [])
    try:
        target_tile_index = target_shuffled_tiles.index(target_tile)
        target_level = target_tile_index + 1
    except ValueError:
        target_level = 1
    target_world_number = target_world
    target_level_number = target_level
    target_game_state = target_team.get("game_state", 0)
    target_effective_game_state = get_effective_game_state(target_game_state, target_world_number)
    
    # Count how many teams are ahead of the target team
    teams_ahead = 0
    for team in teams:
        team_world = team["world_number"]
        team_level = team["level_number"]
        team_game_state = team.get("game_state", 0)
        team_effective_game_state = get_effective_game_state(team_game_state, team_world)
        
        # If this team is ahead (higher world or same world but higher level or same world/level but higher game state)
        if (team_world > target_world_number or 
            (team_world == target_world_number and team_level > target_level_number) or
            (team_world == target_world_number and team_level == target_level_number and team_effective_game_state > target_effective_game_state)):
            teams_ahead += 1
    
    return teams_ahead + 1  # 1-based ranking

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
