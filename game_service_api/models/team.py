from dataclasses import dataclass
import datetime
from typing import List, Optional
from .player import Player

@dataclass
class Team:
    team_name: str
    discord_channel_id: str
    players: List[Player]
    last_rolled_at: datetime
    current_tile: int = 0
    current_world: int = 0
    world1_shuffled_tiles: Optional[List[int]] = None
    world2_shuffled_tiles: Optional[List[int]] = None
    world3_shuffled_tiles: Optional[List[int]] = None
    world4_shuffled_tiles: Optional[List[int]] = None
    completion_counter: int = 1
    # 0 = Normal map, 1 = Key, 2 = Boss
    game_state: int = 0

    # Completion counters for W1 key tiles
    w1key1_completion_counter: int = 1
    w1key2_completion_counter: int = 1
    w1key3_completion_counter: int = 4
    w1key4_completion_counter: int = 1
    w1key5_completion_counter: int = 10

    w1boss_completion_counter: int = 1
    w2boss_completion_counter: int = 3
    w3boss_completion_counter: int = 1
    w4boss_completion_counter: int = 5

    team_image_path: str = "1.png"
    thumbnail_url: str = ""
