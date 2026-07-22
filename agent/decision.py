from dataclasses import dataclass


@dataclass
class Decision:
    selected_tool: str
    reason: str
    requires_screen: bool = False
    requires_memory: bool = False
    requires_internet: bool = False
    requires_llm: bool = False
    requires_confirmation: bool = False
    priority: int = 0
