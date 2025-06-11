from flask import Flask, request, jsonify, abort, send_from_directory
from pymongo import MongoClient
from dataclasses import asdict, field
from typing import List, Optional
import os
from models.player import Player
from models.team import Team
from controllers.teams_controller import teams_blueprint
from controllers.submission_controller import submissions_blueprint
from controllers.image_controller import image_blueprint

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["summer_bingo"]
app.config['DB'] = db

app.register_blueprint(teams_blueprint)
app.register_blueprint(submissions_blueprint)
app.register_blueprint(image_blueprint)

@app.route("/", methods=["GET"])
def health_check():
    try:
        db.command("ping")
        mongo_status = "ok"
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    return jsonify({"status": "ok", "mongo": mongo_status}), 200

@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'images'), filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
