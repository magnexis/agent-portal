from __future__ import annotations

from typing import Any

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.tools.common import build_result


def generate_report(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.generate_report()
    return build_result("generate_report", status, None, "completed", "safe", "Generated report.", payload)


def list_reports(client: AgentPortalRuntimeClient, _args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.list_reports()
    return build_result("list_reports", status, None, "completed", "safe", "Listed reports.", payload)


def read_report(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.read_report(str(args.get("report", "")))
    return build_result("read_report", status, None, "completed", "safe", "Read report.", payload)


def export_report(client: AgentPortalRuntimeClient, args: dict[str, Any]) -> ToolResult:
    status = client.status()
    payload = client.export_report(
        str(args.get("report", "")),
        str(args["destination"]) if "destination" in args and args["destination"] is not None else None,
    )
    return build_result("export_report", status, None, "completed", "safe", "Exported report.", payload)
