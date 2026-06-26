from __future__ import annotations

from typing import Any

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient
from agent_portal_mcp.schemas.actions import McpAction
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.tools.common import build_result, execute_or_queue


def browser_open(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "browser_open",
        McpAction(
            tool="browser_open",
            runtime_action_type="open_url",
            reason=str(args.get("reason", "Open browser URL")),
            target=str(args.get("url", "")),
            risk_hint="low",
        ),
        lambda _: {"url": args.get("url")},
    )


def browser_close(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "browser_close",
        McpAction(
            tool="browser_close",
            runtime_action_type="browser_close",
            reason=str(args.get("reason", "Close browser session")),
            risk_hint="medium",
        ),
    )


def browser_refresh(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "browser_refresh",
        McpAction(
            tool="browser_refresh",
            runtime_action_type="browser_refresh",
            reason=str(args.get("reason", "Refresh current page")),
            risk_hint="low",
        ),
    )


def browser_back(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "browser_back",
        McpAction(
            tool="browser_back",
            runtime_action_type="browser_back",
            reason=str(args.get("reason", "Navigate backward")),
            risk_hint="low",
        ),
    )


def browser_forward(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "browser_forward",
        McpAction(
            tool="browser_forward",
            runtime_action_type="browser_forward",
            reason=str(args.get("reason", "Navigate forward")),
            risk_hint="low",
        ),
    )


def browser_status(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    browser = client.browser_status()
    return build_result(
        "browser_status",
        status,
        None,
        "completed",
        "safe",
        "Returned browser status.",
        {"browser": browser},
    )
