from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SourceResult:
    name: str
    items: list = field(default_factory=list)
    ok: bool = True
    error: str = ""
    detail: str = ""
