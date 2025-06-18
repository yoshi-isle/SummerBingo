from flask import current_app as app
from models.team import Team
from bson import ObjectId
class TeamService:
    def __init__(self):
        pass

    def get_db(self):
        return app.config['DB']

    def get_team_by_discord_id(self, discord_id):
        db = self.get_db()
        team = db.teams.find_one({"players.discord_id": discord_id})
        return team
    
    def get_team_by_name(self, team_name):
        db = self.get_db()
        team = db.teams.find_one({"team_name": team_name})
        return team

    def get_team_by_id(self, team_id):
        db = self.get_db()
        team = db.teams.find_one({"_id": ObjectId(team_id)})
        return team