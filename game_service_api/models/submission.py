from dataclasses import dataclass
from .player import Player

@dataclass
class Submission:
    submitted_by: str
    approved_by: str
    approved: bool
    admin_approval_embed_id: str
    pending_team_embed_id: str
    team_channel_id: str
