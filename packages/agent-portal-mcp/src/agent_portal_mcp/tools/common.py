from __future__ import annotations

from typing import Any, Callable

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient
from agent_portal_mcp.schemas.actions import McpAction
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.schemas.risk import RiskLevel
from agent_portal_mcp.security.policy import McpPolicy, RuntimePolicySnapshot


def runtime_policy_snapshot(status_payload: dict[str, Any]) -> RuntimePolicySnapshot:
    policy = status_payload.get("policy", {})
    return RuntimePolicySnapshot(
        mode=str(policy.get("mode", "assisted")),
        approval_threshold=str(policy.get("approval_threshold", "medium")),  # type: ignore[arg-type]
        read_only=bool(policy.get("read_only", False)),
    )


def build_result(
    tool: str,
    status_payload: dict[str, Any],
    action_payload: dict[str, Any] | None,
    status: str,
    risk: RiskLevel,
    message: str,
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> ToolResult:
    session = status_payload.get("session", {})
    return ToolResult(
        ok=status == "completed",
        tool=tool,
        session_id=session.get("session_id"),
        action_id=action_payload.get("action_id") if action_payload else None,
        status=status,  # type: ignore[arg-type]
        risk=risk,
        message=message,
        data=data or {},
        screenshot_before=action_payload.get("before_screenshot") if action_payload else None,
        screenshot_after=action_payload.get("after_screenshot") if action_payload else None,
        errors=errors or [],
    )


def execute_or_queue(
    client: AgentPortalRuntimeClient,
    tool: str,
    action: McpAction,
    data_builder: Callable[[dict[str, Any] | None], dict[str, Any]] | None = None,
) -> ToolResult:
    status_payload = client.status()
    proposed = client.propose_action(
        action.runtime_action_type,
        action.reason,
        target=action.target,
        payload=action.payload,
        risk_level=action.risk_hint,
    )
    risk = str(proposed.get("risk_level", action.risk_hint))  # type: ignore[assignment]
    policy = McpPolicy()
    snapshot = runtime_policy_snapshot(status_payload)

    if proposed.get("status") == "blocked":
        return build_result(
            tool,
            status_payload,
            proposed,
            "blocked",
            risk,  # type: ignore[arg-type]
            "Action was blocked by the Agent Portal runtime policy engine.",
            data_builder(proposed) if data_builder else {},
            [str(proposed.get("result") or "blocked")],
        )

    if not policy.should_auto_execute(risk, snapshot):  # type: ignore[arg-type]
        return build_result(
            tool,
            status_payload,
            proposed,
            "pending_approval",
            risk,  # type: ignore[arg-type]
            "Action entered the approval queue.",
            data_builder(proposed) if data_builder else {},
        )

    completed = client.approve_action(str(proposed.get("action_id", "")), execute=True)
    fresh_status = client.status()
    return build_result(
        tool,
        fresh_status,
        completed,
        "completed",
        risk,  # type: ignore[arg-type]
        "Action executed through the Agent Portal runtime.",
        data_builder(completed) if data_builder else {},
    )
