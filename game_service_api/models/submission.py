from dataclasses import dataclass
from .player import Player

@dataclass
class Submission:
    submitted_by: str
    approved_by: str
    admin_approval_embed_id: str
    approved: bool
