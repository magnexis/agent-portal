from __future__ import annotations

from typing import Literal


RiskLevel = Literal["safe", "low", "medium", "high", "blocked"]
ToolStatus = Literal[
    "completed",
    "pending_approval",
    "rejected",
    "blocked",
    "failed",
]


RISK_ORDER: list[RiskLevel] = ["safe", "low", "medium", "high", "blocked"]


def compare_risk(left: RiskLevel, right: RiskLevel) -> int:
    return RISK_ORDER.index(left) - RISK_ORDER.index(right)
