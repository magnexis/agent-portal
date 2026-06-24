from __future__ import annotations

from dataclasses import dataclass

from agent_portal_mcp.schemas.risk import RiskLevel, compare_risk


@dataclass(slots=True)
class RuntimePolicySnapshot:
    mode: str = "assisted"
    approval_threshold: RiskLevel = "medium"
    read_only: bool = False


class McpPolicy:
    def should_auto_execute(self, risk: RiskLevel, snapshot: RuntimePolicySnapshot) -> bool:
        if risk == "blocked":
            return False
        if risk == "high":
            return False
        if snapshot.read_only and risk != "safe":
            return False
        if compare_risk(risk, snapshot.approval_threshold) >= 0 and risk != "safe":
            return False
        if snapshot.mode not in {"assisted", "autonomous", "manual-override", "read-only"}:
            return False
        return True
