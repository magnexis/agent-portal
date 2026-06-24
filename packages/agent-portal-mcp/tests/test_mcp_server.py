from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_portal_mcp.bridge.runtime_client import RuntimeClientError
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.server import AgentPortalMcpServer
from agent_portal_mcp.tool_registry import build_tool_registry
from agent_portal_mcp.tools import browser, inspection, navigation, reports


class FakeClient:
    def __init__(self, risk: str = "low", blocked: bool = False, auto_complete: bool = True) -> None:
        self.risk = risk
        self.blocked = blocked
        self.auto_complete = auto_complete
        self.token = "super-secret-token"

    def status(self) -> dict[str, object]:
        return {
            "session": {"session_id": "session-1", "runtime_status": "idle"},
            "policy": {"mode": "assisted", "approval_threshold": "medium", "read_only": False},
        }

    def propose_action(self, action_type: str, reason: str, target=None, payload=None, risk_level="low"):
        if self.blocked:
            return {
                "action_id": "action-1",
                "action_type": action_type,
                "status": "blocked",
                "reason": reason,
                "target": target,
                "payload": payload,
                "risk_level": "blocked",
                "result": "blocked",
            }
        return {
            "action_id": "action-1",
            "action_type": action_type,
            "status": "pending",
            "reason": reason,
            "target": target,
            "payload": payload,
            "risk_level": self.risk,
        }

    def approve_action(self, action_id: str, execute: bool = False):
        return {
            "action_id": action_id,
            "status": "completed" if execute and self.auto_complete else "approved",
            "risk_level": self.risk,
            "after_screenshot": "after.png",
        }

    def browser_status(self):
        return {"connected": True}

    def capture(self, label: str = "capture"):
        return {"action": {"action_id": "capture-1", "after_screenshot": f"{label}.png"}, "screenshotPath": f"{label}.png", "inspection": {"url": "http://localhost", "title": "Fixture", "dom": "<html></html>", "consoleErrors": [], "networkErrors": []}}

    def read_text(self, selector: str, reason: str):
        return {"action": {"action_id": "read-1"}, "selector": selector, "text": "hello"}

    def read_dom(self):
        return {"dom": "<html></html>"}

    def read_accessibility_tree(self):
        return {"accessibilityTree": {"role": "document"}}

    def read_console_errors(self):
        return {"consoleErrors": ["error"]}

    def read_network_failures(self):
        return {"networkFailures": ["GET /api - failed"]}

    def inspect_element(self, selector: str):
        return {"selector": selector, "visible": True}

    def generate_report(self):
        return {"reportPath": "report.json"}

    def list_reports(self):
        return {"reports": [{"name": "report.json"}]}

    def read_report(self, report_name: str):
        return {"name": report_name}

    def export_report(self, report_name: str, destination=None):
        return {"exportPath": destination or report_name}

    def health(self):
        return {"ok": True, "runtimeVersion": "0.1.0"}


class McpServerTests(unittest.TestCase):
    def test_tools_are_registered(self) -> None:
        registry = build_tool_registry()
        self.assertIn("browser_open", registry)
        self.assertIn("capture_screenshot", registry)
        self.assertIn("approve_action", registry)

    def test_server_initialize_and_list_tools(self) -> None:
        server = AgentPortalMcpServer()
        initialize = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertEqual(initialize["result"]["serverInfo"]["name"], "agent-portal-mcp")
        self.assertGreater(len(tools["result"]["tools"]), 5)

    def test_browser_open_tool_executes(self) -> None:
        result = browser.browser_open(FakeClient(), {"url": "http://localhost:3000"})
        self.assertTrue(result.ok)
        self.assertEqual(result.status, "completed")

    def test_capture_screenshot_tool_executes(self) -> None:
        result = inspection.capture_screenshot(FakeClient(), {"label": "home"})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["screenshotPath"], "home.png")

    def test_click_element_can_enter_pending_approval(self) -> None:
        result = navigation.click_element(FakeClient(risk="high"), {"selector": "#danger"})
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "pending_approval")

    def test_high_risk_action_can_be_blocked(self) -> None:
        result = navigation.type_text(
            FakeClient(blocked=True),
            {"selector": "#password", "text": "secret", "reason": "Enter password"},
        )
        self.assertEqual(result.status, "blocked")

    def test_report_generation_tool(self) -> None:
        result = reports.generate_report(FakeClient(), {})
        self.assertEqual(result.data["reportPath"], "report.json")

    def test_token_redaction(self) -> None:
        server = AgentPortalMcpServer()
        server.client = FakeClient()  # type: ignore[assignment]
        redacted = server._redact("token super-secret-token should not leak")
        self.assertNotIn("super-secret-token", redacted)

    def test_runtime_offline_error(self) -> None:
        server = AgentPortalMcpServer()

        class OfflineClient:
            token = None

            def status(self):
                raise RuntimeClientError("Agent Portal runtime is not running. Start it with: agent-portal start")

        server.client = OfflineClient()  # type: ignore[assignment]
        result = server.call_tool("browser_status", {})
        self.assertFalse(result.ok)
        self.assertIn("agent-portal start", result.message)


if __name__ == "__main__":
    unittest.main()
