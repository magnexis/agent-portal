from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_portal.config import load_config, save_default_config


class ConfigTests(unittest.TestCase):
    def test_default_config_can_be_created_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = save_default_config(root)
            config = load_config(root)
            self.assertTrue(config_path.exists())
            self.assertEqual(config.runtime_port, 8765)


if __name__ == "__main__":
    unittest.main()
