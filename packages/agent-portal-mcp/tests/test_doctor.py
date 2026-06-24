from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_portal_mcp.doctor import run_doctor


class McpDoctorTests(unittest.TestCase):
    def test_doctor_returns_checks(self) -> None:
        result = run_doctor("http://127.0.0.1:9")
        self.assertGreater(len(result.checks), 0)
        self.assertTrue(any(check.name == "tool-registry" for check in result.checks))


if __name__ == "__main__":
    unittest.main()
