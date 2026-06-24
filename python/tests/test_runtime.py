from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_portal.models import ActionRequest, RuntimeConfigModel
from agent_portal.runtime import PortalRuntime


class StubBrowser:
    def __init__(self) -> None:
        self.connected = False
        self.url: str | None = None
        self.console_errors: list[str] = []
        self.network_errors: list[str] = []

    def available(self) -> bool:
        return True

    def start(self) -> None:
        self.connected = True

    def stop(self) -> None:
        self.connected = False

    def open_url(self, url: str) -> None:
        self.url = url

    def screenshot(self, label: str) -> str:
        return f"{label}.png"

    def click(self, selector: str) -> None:
        self.url = self.url or "http://localhost/test"

    def type_text(self, selector: str, value: str) -> None:
        return None

    def scroll(self, selector: str | None = None) -> None:
        return None

    def hover(self, selector: str) -> None:
        return None

    def wait(self, selector: str) -> None:
        return None

    def inspect(self) -> dict[str, object]:
        return {
            "url": self.url,
            "title": "Fixture",
            "dom": "<html></html>",
            "consoleErrors": self.console_errors,
            "networkErrors": self.network_errors,
        }

    def current_url(self) -> str | None:
        return self.url

    def current_title(self) -> str | None:
        return "Fixture" if self.url else None

    def read_console(self) -> list[str]:
        return list(self.console_errors)

    def read_network(self) -> list[str]:
        return list(self.network_errors)


class RuntimeTests(unittest.TestCase):
    def build_runtime(self, root: Path) -> PortalRuntime:
        config = RuntimeConfigModel(
            screenshot_directory="shots",
            report_directory="reports",
            sensitive_screenshots_enabled=True,
            safe_mode=False,
        )
        runtime = PortalRuntime(root, config)
        runtime.browser = StubBrowser()  # type: ignore[assignment]
        return runtime

    def test_runtime_proposes_and_rejects_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = self.build_runtime(Path(temp_dir))
            action = runtime.propose_action(
                ActionRequest("click", "Click a safe element", target="#ok")
            )
            rejected = runtime.reject_action(action.action_id, "Rejected for test")
            self.assertEqual(rejected.status, "rejected")
            self.assertEqual(runtime.session.runtime_status, "blocked")

    def test_runtime_blocks_password_typing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = self.build_runtime(Path(temp_dir))
            action = runtime.propose_action(
                ActionRequest("type", "Enter password", target="#password", payload="secret")
            )
            self.assertEqual(action.status, "blocked")

    def test_runtime_open_and_report_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime = self.build_runtime(root)
            runtime.start()
            runtime.ensure_browser()
            result = runtime.open_url("http://localhost:3000")
            report_path = runtime.generate_report()

            self.assertEqual(result.status, "completed")
            self.assertTrue(report_path.exists())

            report = json.loads(report_path.read_text(encoding="utf8"))
            self.assertEqual(report["current_url"], "http://localhost:3000")
            self.assertGreaterEqual(len(report["actions_completed"]), 1)


if __name__ == "__main__":
    unittest.main()
