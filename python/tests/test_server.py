from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
import sys
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_portal.models import RuntimeConfigModel
from agent_portal.runtime import PortalRuntime
from agent_portal.server import build_server


class ServerTests(unittest.TestCase):
    def test_status_endpoint_responds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]

            config = RuntimeConfigModel(runtime_host="127.0.0.1", runtime_port=port)
            runtime = PortalRuntime(root, config)
            runtime.start()
            server = build_server(runtime)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                time.sleep(0.1)
                with urlopen(f"http://127.0.0.1:{port}/status") as response:
                    payload = json.loads(response.read().decode("utf8"))
                self.assertEqual(payload["session"]["runtime_status"], "idle")
            finally:
                request = Request(
                    f"http://127.0.0.1:{port}/control/stop",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(request):
                    pass
                thread.join(timeout=2)
                server.server_close()


if __name__ == "__main__":
    unittest.main()
