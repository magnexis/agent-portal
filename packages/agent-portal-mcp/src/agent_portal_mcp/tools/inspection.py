from __future__ import annotations

from typing import Any

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.tools.common import build_result


def capture_screenshot(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.capture(str(args.get("label", "mcp-capture")))
    action = payload.get("action", {})
    return build_result(
        "capture_screenshot",
        status,
        action if isinstance(action, dict) else None,
        "completed",
        "safe",
        "Captured screenshot.",
        payload,
    )


def read_page_text(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.read_text(
        str(args.get("selector", "body")),
        str(args.get("reason", "Read page text")),
    )
    return build_result("read_page_text", status, payload.get("action"), "completed", "safe", "Read page text.", payload)


def read_dom(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.read_dom()
    return build_result("read_dom", status, None, "completed", "safe", "Read page DOM.", payload)


def read_accessibility_tree(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.read_accessibility_tree()
    return build_result(
        "read_accessibility_tree",
        status,
        None,
        "completed",
        "safe",
        "Read accessibility tree.",
        payload,
    )


def read_console_errors(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.read_console_errors()
    return build_result(
        "read_console_errors",
        status,
        None,
        "completed",
        "safe",
        "Read console errors.",
        payload,
    )


def read_network_failures(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.read_network_failures()
    return build_result(
        "read_network_failures",
        status,
        None,
        "completed",
        "safe",
        "Read network failures.",
        payload,
    )


def inspect_element(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.inspect_element(str(args.get("selector", "")))
    return build_result(
        "inspect_element",
        status,
        None,
        "completed",
        "safe",
        "Inspected element.",
        payload,
    )
