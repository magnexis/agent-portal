from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .risk import RiskLevel


@dataclass(slots=True)
class McpAction:
    tool: str
    runtime_action_type: str
    reason: str
    target: str | None = None
    payload: str | None = None
    risk_hint: RiskLevel = "low"
    metadata: dict[str, Any] = field(default_factory=dict)
