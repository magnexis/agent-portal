from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_portal.doctor import run_doctor


class DoctorTests(unittest.TestCase):
    def test_doctor_returns_checks(self) -> None:
        report = run_doctor()
        self.assertGreater(len(report.checks), 0)


if __name__ == "__main__":
    unittest.main()
