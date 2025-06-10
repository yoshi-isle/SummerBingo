from dataclasses import dataclass
from .player import Player

@dataclass
class Submission:
    discord_user_id: str
    submitted_by: Player
    approved: bool
    admin_approval_embed_id: str