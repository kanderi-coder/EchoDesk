from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ScreenContext:
    application: Optional[str] = None
    window_title: Optional[str] = None
    visible_text: Optional[str] = None
    sections: Optional[List[str]] = None
    buttons: Optional[List[str]] = None
    menus: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    language: Optional[str] = None
    summary: Optional[str] = None
