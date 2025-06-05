import random

def shuffle_tiles(tiles):
    tile_ids = [tile["id"] for tile in tiles]
    random.shuffle(tile_ids)
    return tile_ids
