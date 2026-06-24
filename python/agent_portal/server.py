from __future__ import annotations

import json
import threading
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .exceptions import AgentPortalError
from .runtime import PortalRuntime


def build_server(runtime: PortalRuntime) -> ThreadingHTTPServer:
    class AgentPortalHandler(BaseHTTPRequestHandler):
        server_version = "AgentPortalRuntime/0.1.0"

        def _send_json(self, status: int, payload: object) -> None:
            encoded = json.dumps(payload, indent=2).encode("utf8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(encoded)

        def _read_json(self) -> dict[str, object]:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length == 0:
                return {}
            return json.loads(self.rfile.read(content_length).decode("utf8"))

        def _authorize(self) -> bool:
            token = runtime.config.api_token
            if not token:
                return True
            header = self.headers.get("Authorization", "")
            return header == f"Bearer {token}"

        def _unauthorized(self) -> None:
            self._send_json(
                HTTPStatus.UNAUTHORIZED,
                {
                    "error": "Unauthorized",
                    "suggestedFix": "Provide the configured runtime API token as a Bearer token.",
                },
            )

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/health" and not self._authorize():
                self._unauthorized()
                return
            if parsed.path == "/health":
                self._send_json(HTTPStatus.OK, runtime.health())
                return
            if parsed.path == "/status":
                self._send_json(HTTPStatus.OK, runtime.status())
                return
            if parsed.path == "/report/latest":
                report_path = runtime.generate_report()
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "reportPath": str(report_path),
                        "report": json.loads(report_path.read_text(encoding="utf8")),
                    },
                )
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown path"})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if not self._authorize():
                self._unauthorized()
                return
            payload = self._read_json()
            try:
                if parsed.path == "/control/start":
                    runtime.start()
                    self._send_json(HTTPStatus.OK, runtime.status())
                    return
                if parsed.path == "/control/stop":
                    self._send_json(HTTPStatus.OK, {"status": "stopping"})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    runtime.stop()
                    return
                if parsed.path == "/control/pause":
                    runtime.pause()
                    self._send_json(HTTPStatus.OK, runtime.status())
                    return
                if parsed.path == "/control/resume":
                    runtime.resume()
                    self._send_json(HTTPStatus.OK, runtime.status())
                    return
                if parsed.path == "/control/restart":
                    runtime.restart()
                    self._send_json(HTTPStatus.OK, runtime.status())
                    return
                if parsed.path == "/control/goal":
                    runtime.set_goal(str(payload.get("goal", "")))
                    self._send_json(HTTPStatus.OK, runtime.status())
                    return
                if parsed.path == "/browser/start":
                    runtime.ensure_browser()
                    self._send_json(HTTPStatus.OK, runtime.status())
                    return
                if parsed.path == "/browser/open":
                    self._send_json(
                        HTTPStatus.OK,
                        asdict(runtime.open_url(str(payload.get("url", "")))),
                    )
                    return
                if parsed.path == "/browser/click":
                    self._send_json(
                        HTTPStatus.OK,
                        asdict(
                            runtime.click(
                                str(payload.get("selector", "")),
                                str(payload.get("reason", "Click element")),
                            )
                        ),
                    )
                    return
                if parsed.path == "/browser/type":
                    self._send_json(
                        HTTPStatus.OK,
                        asdict(
                            runtime.type_text(
                                str(payload.get("selector", "")),
                                str(payload.get("value", "")),
                                str(payload.get("reason", "Type into element")),
                            )
                        ),
                    )
                    return
                if parsed.path == "/browser/scroll":
                    self._send_json(
                        HTTPStatus.OK,
                        asdict(
                            runtime.scroll(
                                str(payload["selector"]) if "selector" in payload and payload["selector"] is not None else None,
                                str(payload.get("reason", "Scroll page")),
                            )
                        ),
                    )
                    return
                if parsed.path == "/browser/hover":
                    self._send_json(
                        HTTPStatus.OK,
                        asdict(
                            runtime.hover(
                                str(payload.get("selector", "")),
                                str(payload.get("reason", "Hover over element")),
                            )
                        ),
                    )
                    return
                if parsed.path == "/browser/wait":
                    self._send_json(
                        HTTPStatus.OK,
                        asdict(
                            runtime.wait(
                                str(payload.get("selector", "")),
                                str(payload.get("reason", "Wait for element")),
                            )
                        ),
                    )
                    return
                if parsed.path == "/browser/screenshot":
                    self._send_json(
                        HTTPStatus.OK,
                        asdict(runtime.screenshot(str(payload.get("label", "manual")))),
                    )
                    return
                if parsed.path == "/browser/capture":
                    self._send_json(
                        HTTPStatus.OK,
                        runtime.capture_snapshot(str(payload.get("label", "capture"))),
                    )
                    return
                if parsed.path == "/browser/inspect":
                    self._send_json(HTTPStatus.OK, runtime.inspect())
                    return
                if parsed.path == "/browser/read-text":
                    self._send_json(
                        HTTPStatus.OK,
                        runtime.read_text(
                            str(payload.get("selector", "")),
                            str(payload.get("reason", "Read text from element")),
                        ),
                    )
                    return
                if parsed.path == "/browser/execute":
                    self._send_json(
                        HTTPStatus.OK,
                        runtime.execute(
                            str(payload.get("script", "")),
                            str(payload.get("reason", "Execute script in page context")),
                        ),
                    )
                    return
                if parsed.path == "/control/approve-next":
                    if runtime.session.pending_actions:
                        result = runtime.approve_action(runtime.session.pending_actions[0].action_id)
                        self._send_json(HTTPStatus.OK, asdict(result))
                        return
                    self._send_json(HTTPStatus.OK, {"message": "No pending action"})
                    return
                if parsed.path == "/control/reject-next":
                    if runtime.session.pending_actions:
                        result = runtime.reject_action(
                            runtime.session.pending_actions[0].action_id,
                            str(payload.get("reason", "Rejected by user")),
                        )
                        self._send_json(HTTPStatus.OK, asdict(result))
                        return
                    self._send_json(HTTPStatus.OK, {"message": "No pending action"})
                    return
                if parsed.path == "/report/generate":
                    report_path = runtime.generate_report()
                    self._send_json(HTTPStatus.OK, {"reportPath": str(report_path)})
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown path"})
            except AgentPortalError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, exc.to_dict())

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    return ThreadingHTTPServer(
        (runtime.config.runtime_host, runtime.config.runtime_port),
        AgentPortalHandler,
    )


def serve(runtime: PortalRuntime | None = None) -> None:
    active_runtime = runtime or PortalRuntime(Path.cwd())
    active_runtime.start()
    server = build_server(active_runtime)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        active_runtime.stop()


def main() -> None:
    serve()
