from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentContext:
    user_command: str
    intent: str
    screen_available: bool = False
    internet_available: bool = False
    memory_available: bool = False
    knowledge_available: bool = False
    vision_available: bool = False
    automation_available: bool = False
    confidence: float = 0.0
    notes: Optional[str] = None
