from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.tools import browser, inspection, navigation, reports, steering


ToolHandler = Callable[[AgentPortalRuntimeClient, dict[str, Any]], ToolResult]


@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler


def build_tool_registry() -> dict[str, ToolDefinition]:
    definitions = [
        ToolDefinition("browser_open", "Open a browser URL through Agent Portal.", {"type": "object", "properties": {"url": {"type": "string"}, "reason": {"type": "string"}}, "required": ["url"]}, browser.browser_open),
        ToolDefinition("browser_close", "Close the current browser session.", {"type": "object", "properties": {"reason": {"type": "string"}}}, browser.browser_close),
        ToolDefinition("browser_refresh", "Refresh the current page.", {"type": "object", "properties": {"reason": {"type": "string"}}}, browser.browser_refresh),
        ToolDefinition("browser_back", "Navigate backward in history.", {"type": "object", "properties": {"reason": {"type": "string"}}}, browser.browser_back),
        ToolDefinition("browser_forward", "Navigate forward in history.", {"type": "object", "properties": {"reason": {"type": "string"}}}, browser.browser_forward),
        ToolDefinition("browser_status", "Return browser session status.", {"type": "object", "properties": {}}, browser.browser_status),
        ToolDefinition("navigate_to_url", "Navigate to a URL through the runtime.", {"type": "object", "properties": {"url": {"type": "string"}, "reason": {"type": "string"}}, "required": ["url"]}, navigation.navigate_to_url),
        ToolDefinition("click_element", "Click an element selected by CSS, role text, or label.", {"type": "object", "properties": {"selector": {"type": "string"}, "reason": {"type": "string"}}, "required": ["selector"]}, navigation.click_element),
        ToolDefinition("type_text", "Type text into an input element.", {"type": "object", "properties": {"selector": {"type": "string"}, "text": {"type": "string"}, "reason": {"type": "string"}}, "required": ["selector", "text"]}, navigation.type_text),
        ToolDefinition("scroll_page", "Scroll the page or bring an element into view.", {"type": "object", "properties": {"selector": {"type": "string"}, "reason": {"type": "string"}}}, navigation.scroll_page),
        ToolDefinition("hover_element", "Hover over an element.", {"type": "object", "properties": {"selector": {"type": "string"}, "reason": {"type": "string"}}, "required": ["selector"]}, navigation.hover_element),
        ToolDefinition("wait_for_page", "Wait for a page element to appear.", {"type": "object", "properties": {"selector": {"type": "string"}, "reason": {"type": "string"}}, "required": ["selector"]}, navigation.wait_for_page),
        ToolDefinition("capture_screenshot", "Capture a screenshot with evidence metadata.", {"type": "object", "properties": {"label": {"type": "string"}}}, inspection.capture_screenshot),
        ToolDefinition("read_page_text", "Read visible text from an element.", {"type": "object", "properties": {"selector": {"type": "string"}, "reason": {"type": "string"}}, "required": ["selector"]}, inspection.read_page_text),
        ToolDefinition("read_dom", "Read the current page DOM.", {"type": "object", "properties": {}}, inspection.read_dom),
        ToolDefinition("read_accessibility_tree", "Read the page accessibility tree.", {"type": "object", "properties": {}}, inspection.read_accessibility_tree),
        ToolDefinition("read_console_errors", "Read collected console errors.", {"type": "object", "properties": {}}, inspection.read_console_errors),
        ToolDefinition("read_network_failures", "Read collected network failures.", {"type": "object", "properties": {}}, inspection.read_network_failures),
        ToolDefinition("inspect_element", "Inspect a specific element.", {"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]}, inspection.inspect_element),
        ToolDefinition("propose_action", "Propose an action through the runtime policy engine.", {"type": "object", "properties": {"action_type": {"type": "string"}, "target": {"type": "string"}, "payload": {"type": "string"}, "reason": {"type": "string"}, "risk": {"type": "string"}}, "required": ["action_type", "reason"]}, steering.propose_action),
        ToolDefinition("approve_action", "Approve and optionally execute a queued action.", {"type": "object", "properties": {"action_id": {"type": "string"}, "execute": {"type": "boolean"}}, "required": ["action_id"]}, steering.approve_action),
        ToolDefinition("reject_action", "Reject a queued action.", {"type": "object", "properties": {"action_id": {"type": "string"}, "reason": {"type": "string"}}, "required": ["action_id"]}, steering.reject_action),
        ToolDefinition("pause_agent", "Pause the agent runtime.", {"type": "object", "properties": {}}, steering.pause_agent),
        ToolDefinition("resume_agent", "Resume the agent runtime.", {"type": "object", "properties": {}}, steering.resume_agent),
        ToolDefinition("stop_agent", "Stop the agent runtime.", {"type": "object", "properties": {}}, steering.stop_agent),
        ToolDefinition("set_goal", "Set the current runtime goal.", {"type": "object", "properties": {"goal": {"type": "string"}}, "required": ["goal"]}, steering.set_goal),
        ToolDefinition("get_current_goal", "Get the current runtime goal.", {"type": "object", "properties": {}}, steering.get_current_goal),
        ToolDefinition("get_action_queue", "Get the runtime action queue.", {"type": "object", "properties": {}}, steering.get_action_queue),
        ToolDefinition("set_action_mode", "Set the runtime action mode.", {"type": "object", "properties": {"mode": {"type": "string"}}, "required": ["mode"]}, steering.set_action_mode),
        ToolDefinition("generate_report", "Generate a runtime report.", {"type": "object", "properties": {}}, reports.generate_report),
        ToolDefinition("list_reports", "List available runtime reports.", {"type": "object", "properties": {}}, reports.list_reports),
        ToolDefinition("read_report", "Read a report by name.", {"type": "object", "properties": {"report": {"type": "string"}}, "required": ["report"]}, reports.read_report),
        ToolDefinition("export_report", "Export a report to a destination path.", {"type": "object", "properties": {"report": {"type": "string"}, "destination": {"type": "string"}}, "required": ["report"]}, reports.export_report),
    ]
    return {definition.name: definition for definition in definitions}
