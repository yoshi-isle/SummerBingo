from dataclasses import dataclass
from typing import List

@dataclass
class Player:
    discord_id: str
    runescape_accounts: List[str]
