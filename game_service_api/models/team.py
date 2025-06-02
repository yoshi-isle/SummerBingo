from dataclasses import dataclass
from typing import List, Optional
from .player import Player

@dataclass
class Team:
    team_name: str
    players: List[Player]
    current_tile: int = 0
    current_world: int = 0
