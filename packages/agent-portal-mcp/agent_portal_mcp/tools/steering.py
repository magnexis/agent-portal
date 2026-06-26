from __future__ import annotations

from typing import Any

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.tools.common import build_result


def propose_action(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.status()
    action = client.propose_action(
        str(args.get("action_type", "")),
        str(args.get("reason", "Propose action")),
        target=str(args["target"]) if "target" in args and args["target"] is not None else None,
        payload=str(args["payload"]) if "payload" in args and args["payload"] is not None else None,
        risk_level=str(args.get("risk", "low")),
    )
    mapped_status = "pending_approval" if action.get("status") == "pending" else str(action.get("status", "failed"))
    return build_result(
        "propose_action",
        status,
        action,
        mapped_status,  # type: ignore[arg-type]
        str(action.get("risk_level", "low")),  # type: ignore[arg-type]
        "Proposed action through the runtime policy engine.",
        {"action": action},
    )


def approve_action(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.status()
    action = client.approve_action(str(args.get("action_id", "")), execute=bool(args.get("execute", True)))
    return build_result(
        "approve_action",
        status,
        action,
        "completed" if action.get("status") == "completed" else "pending_approval",
        str(action.get("risk_level", "low")),  # type: ignore[arg-type]
        "Approved action through Agent Portal.",
        {"action": action},
    )


def reject_action(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.status()
    action = client.reject_action(str(args.get("action_id", "")), str(args.get("reason", "Rejected by user")))
    return build_result(
        "reject_action",
        status,
        action,
        "rejected",
        str(action.get("risk_level", "low")),  # type: ignore[arg-type]
        "Rejected action through Agent Portal.",
        {"action": action},
    )


def pause_agent(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.pause()
    return build_result("pause_agent", status, None, "completed", "safe", "Paused agent runtime.", status)


def resume_agent(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.resume()
    return build_result("resume_agent", status, None, "completed", "safe", "Resumed agent runtime.", status)


def stop_agent(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.stop()
    return build_result("stop_agent", {"session": {}}, None, "completed", "medium", "Stopped agent runtime.", status)


def set_goal(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.set_goal(str(args.get("goal", "")))
    return build_result("set_goal", status, None, "completed", "safe", "Set current goal.", status)


def get_current_goal(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    goal = client.current_goal()
    return build_result("get_current_goal", status, None, "completed", "safe", "Returned current goal.", goal)


def get_action_queue(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    queue = client.action_queue()
    return build_result("get_action_queue", status, None, "completed", "safe", "Returned action queue.", queue)


def set_action_mode(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.set_action_mode(str(args.get("mode", "assisted")))
    return build_result("set_action_mode", status, None, "completed", "medium", "Updated action mode.", status)
