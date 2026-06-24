from __future__ import annotations

from typing import Any

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient
from agent_portal_mcp.schemas.actions import McpAction
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.tools.common import execute_or_queue


def navigate_to_url(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "navigate_to_url",
        McpAction(
            tool="navigate_to_url",
            runtime_action_type="open_url",
            reason=str(args.get("reason", "Navigate to URL")),
            target=str(args.get("url", "")),
            risk_hint="low",
        ),
    )


def click_element(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "click_element",
        McpAction(
            tool="click_element",
            runtime_action_type="click",
            reason=str(args.get("reason", "Click element")),
            target=str(args.get("selector", "")),
            risk_hint="low",
        ),
    )


def type_text(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "type_text",
        McpAction(
            tool="type_text",
            runtime_action_type="type",
            reason=str(args.get("reason", "Type text into element")),
            target=str(args.get("selector", "")),
            payload=str(args.get("text", "")),
            risk_hint="medium",
        ),
    )


def scroll_page(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "scroll_page",
        McpAction(
            tool="scroll_page",
            runtime_action_type="scroll",
            reason=str(args.get("reason", "Scroll page")),
            target=str(args["selector"]) if "selector" in args and args["selector"] is not None else None,
            risk_hint="safe",
        ),
    )


def hover_element(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "hover_element",
        McpAction(
            tool="hover_element",
            runtime_action_type="hover",
            reason=str(args.get("reason", "Hover over element")),
            target=str(args.get("selector", "")),
            risk_hint="safe",
        ),
    )


def wait_for_page(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    return execute_or_queue(
        client,
        "wait_for_page",
        McpAction(
            tool="wait_for_page",
            runtime_action_type="wait",
            reason=str(args.get("reason", "Wait for page element")),
            target=str(args.get("selector", "")),
            risk_hint="safe",
        ),
    )
