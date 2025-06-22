from dataclasses import dataclass
from typing import List, Optional
from .player import Player

@dataclass
class Team:
    team_name: str
    discord_channel_id: str
    players: List[Player]
    current_tile: int = 0
    current_world: int = 0
    world1_shuffled_tiles: Optional[List[int]] = None
    completion_counter: int = 1
