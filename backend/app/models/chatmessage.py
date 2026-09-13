from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    pid: str
    message: str
    sent_at: datetime