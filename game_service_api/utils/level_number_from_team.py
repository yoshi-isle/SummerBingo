from constants.world_names import WORLD_NAMES
from constants.tiles import world1_tiles, world2_tiles, world3_tiles, world4_tiles

def level_number_from_team(team):
    world = int(team.get('current_world', 1))
    level = int(team.get('current_tile', 1))
    shuffled_tiles = team.get(f'world{world}_shuffled_tiles')
    return next(i + 1 for i, tile in enumerate(shuffled_tiles) if tile == level)
        
world_tiles_map = {
    1: world1_tiles,
    2: world2_tiles,
    3: world3_tiles,
    4: world4_tiles
}