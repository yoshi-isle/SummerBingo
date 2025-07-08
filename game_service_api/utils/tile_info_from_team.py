from constants.tiles import world1_tiles, world2_tiles, world3_tiles, world4_tiles

def tile_info_from_team(team):
    world = int(team.get('current_world', 1))
    level = int(team.get('current_tile', 1))

    tiles = world_tiles_map[world]
    for tile in tiles['world_tiles']:
        if tile['id'] == level:
            return tile

world_tiles_map = {
    1: world1_tiles,
    2: world2_tiles,
    3: world3_tiles,
    4: world4_tiles
}