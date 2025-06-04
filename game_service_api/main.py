from flask import Flask, request, jsonify, abort
from pymongo import MongoClient
from dataclasses import asdict, field
from typing import List, Optional
import os
from models.player import Player
from models.team import Team
from controllers.teams_controller import tms_bp
from controllers.players_controller import plyr_bp

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["summer_bingo"]
app.config['DB'] = db

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

app.register_blueprint(tms_bp)
app.register_blueprint(plyr_bp)

@app.route("/", methods=["GET"])
def health_check():
    try:
        db.command("ping")
        mongo_status = "ok"
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    return jsonify({"status": "ok", "mongo": mongo_status}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
