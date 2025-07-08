from constants.world_names import WORLD_NAMES
from utils.level_number_from_team import level_number_from_team


def level_name_from_team(team):
    return f"{WORLD_NAMES[team.get('current_world')]} {team.get('current_world')}-{level_number_from_team(team)}"