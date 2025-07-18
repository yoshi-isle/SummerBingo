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
    
    # 0 = Normal map, 1 = Key, 2 = Boss
    game_state: int = 0
    completion_counter: int = 1

    # Boss tile completion counters
    w1boss_completion_counter: int = 1
    w2boss_completion_counter: int = 1
    w3boss_completion_counter: int = 2
    w4boss_completion_counter: int = 5

    # World 1 key tile completion counters
    w1key1_completion_counter: int = 2
    w1key2_completion_counter: int = 1
    w1key3_completion_counter: int = 4
    w1key4_completion_counter: int = 1
    w1key5_completion_counter: int = 10

    # World 2 key tile completion counters
    w2key1_completion_counter: int = 1
    w2key2_completion_counter: int = 1
    w2key3_completion_counter: int = 3
    w2key4_completion_counter: int = 3
    w2key5_completion_counter: int = 3

    # World 2 specific state variables
    w2_path_chosen: int = 0

    # World 3 specific state variables
    w3_braziers_lit: int = 0
    w3key1_completion_counter: int = 10
    w3key2_completion_counter: int = 1
    w3key3_completion_counter: int = 8
    w3key4_completion_counter: int = 6
    w3key5_completion_counter: int = 1
    w3key6_completion_counter: int = 1

    # World 4 specific state variables
    w4_trial_iteration: int = 0 # 0 = first trial, 1 = pick one of three, 2 = final
    w4key1_completion_counter: int = 3
    w4key2_completion_counter: int = 3
    w4key3_completion_counter: int = 1
    w4key4_completion_counter: int = 1
    w4key5_completion_counter: int = 1

    team_image_path: str = "1.png"
    thumbnail_url: str = ""

    world1_shuffled_tiles: Optional[List[int]] = None
    world2_shuffled_tiles: Optional[List[int]] = None
    world3_shuffled_tiles: Optional[List[int]] = None
    world4_shuffled_tiles: Optional[List[int]] = None