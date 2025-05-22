from flask import Flask, request, jsonify, abort
from pymongo import MongoClient
from dataclasses import asdict, field
from typing import List, Optional
import os
from models.player import Player
from models.team import Team

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["summer_bingo"]

def player_from_dict(data):
    return Player(
        discord_id=data["discord_id"],
        runescape_accounts=data["runescape_accounts"]
    )

def team_from_dict(data):
    players = [player_from_dict(p) for p in data["players"]]
    return Team(
        team_name=data["team_name"],
        players=players,
        current_tile=data.get("current_tile", 0),
        current_world=data.get("current_world")
    )

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/teams", methods=["POST"])
def create_team():
    data = request.get_json()
    players = [Player(**p) for p in data["players"]]
    team = Team(
        team_name=data["team_name"],
        players=players,
        current_tile=1,
        current_world=1
    )
    team_dict = asdict(team)
    team_dict["players"] = [asdict(p) for p in team.players]
    db.teams.insert_one(team_dict)
    return jsonify(team_dict), 201

@app.route("/teams/<team_name>", methods=["GET"])
def get_team(team_name):
    team = db.teams.find_one({"team_name": team_name})
    if not team:
        abort(404, description="Team not found")
    team["players"] = [p for p in team["players"]]
    return jsonify(team), 200

@app.route("/teams/<team_name>/advance_tile", methods=["POST"])
def advance_tile(team_name):
    team = db.teams.find_one({"team_name": team_name})
    if not team:
        abort(404, description="Team not found")
    current_tile = team.get("current_tile", 0) + 1
    db.teams.update_one({"team_name": team_name}, {"$set": {"current_tile": current_tile}})
    team["current_tile"] = current_tile
    return jsonify(team), 200

@app.route("/players", methods=["POST"])
def create_player():
    data = request.get_json()
    player = Player(**data)
    db.players.insert_one(asdict(player))
    return jsonify(asdict(player)), 201

@app.route("/players/<discord_id>", methods=["GET"])
def get_player(discord_id):
    player = db.players.find_one({"discord_id": discord_id})
    if not player:
        abort(404, description="Player not found")
    return jsonify(player), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
