from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .risk import RiskLevel, ToolStatus


@dataclass(slots=True)
class ToolResult:
    ok: bool
    tool: str
    session_id: str | None
    action_id: str | None
    status: ToolStatus
    risk: RiskLevel
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    screenshot_before: str | None = None
    screenshot_after: str | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
