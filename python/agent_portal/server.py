from __future__ import annotations

import json
import threading
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .exceptions import AgentPortalError
from .models import ActionRequest
from .runtime import PortalRuntime


def build_server(runtime: PortalRuntime) -> HTTPServer:
    class AgentPortalHandler(BaseHTTPRequestHandler):
        server_version = "AgentPortalRuntime/0.0.3"

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
                if parsed.path == "/control/goal/current":
                    self._send_json(
                        HTTPStatus.OK,
                        {"goal": runtime.get_current_goal()},
                    )
                    return
                if parsed.path == "/control/action-mode":
                    runtime.set_action_mode(str(payload.get("mode", "")))
                    self._send_json(HTTPStatus.OK, runtime.status())
                    return
                if parsed.path == "/control/action-queue":
                    self._send_json(HTTPStatus.OK, {"actions": runtime.get_action_queue()})
                    return
                if parsed.path == "/control/propose-action":
                    action = runtime.propose_action(
                        ActionRequest(
                            action_type=str(payload.get("actionType", "")),
                            reason=str(payload.get("reason", "")),
                            target=str(payload["target"]) if "target" in payload and payload["target"] is not None else None,
                            payload=str(payload["payload"]) if "payload" in payload and payload["payload"] is not None else None,
                            risk_level=str(payload.get("riskLevel", "low")),
                        )
                    )
                    self._send_json(HTTPStatus.OK, asdict(action))
                    return
                if parsed.path == "/control/approve-action":
                    action_id = str(payload.get("actionId", ""))
                    execute_now = bool(payload.get("execute", False))
                    result = runtime.execute_action(action_id) if execute_now else runtime.approve_action(action_id)
                    self._send_json(HTTPStatus.OK, asdict(result))
                    return
                if parsed.path == "/control/reject-action":
                    result = runtime.reject_action(
                        str(payload.get("actionId", "")),
                        str(payload.get("reason", "Rejected by user")),
                    )
                    self._send_json(HTTPStatus.OK, asdict(result))
                    return
                if parsed.path == "/browser/start":
                    runtime.ensure_browser()
                    self._send_json(HTTPStatus.OK, runtime.status())
                    return
                if parsed.path == "/browser/close":
                    self._send_json(HTTPStatus.OK, asdict(runtime.close_browser()))
                    return
                if parsed.path == "/browser/refresh":
                    self._send_json(HTTPStatus.OK, asdict(runtime.refresh()))
                    return
                if parsed.path == "/browser/back":
                    self._send_json(HTTPStatus.OK, asdict(runtime.back()))
                    return
                if parsed.path == "/browser/forward":
                    self._send_json(HTTPStatus.OK, asdict(runtime.forward()))
                    return
                if parsed.path == "/browser/status":
                    self._send_json(HTTPStatus.OK, runtime.browser_status())
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
                if parsed.path == "/browser/read-dom":
                    self._send_json(HTTPStatus.OK, runtime.read_dom())
                    return
                if parsed.path == "/browser/read-accessibility-tree":
                    self._send_json(HTTPStatus.OK, runtime.read_accessibility_tree())
                    return
                if parsed.path == "/browser/read-console-errors":
                    self._send_json(HTTPStatus.OK, runtime.read_console_errors())
                    return
                if parsed.path == "/browser/read-network-failures":
                    self._send_json(HTTPStatus.OK, runtime.read_network_failures())
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
                if parsed.path == "/browser/inspect-element":
                    self._send_json(
                        HTTPStatus.OK,
                        runtime.inspect_element(str(payload.get("selector", ""))),
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
                if parsed.path == "/report/list":
                    self._send_json(HTTPStatus.OK, {"reports": runtime.list_reports()})
                    return
                if parsed.path == "/report/read":
                    self._send_json(
                        HTTPStatus.OK,
                        runtime.read_report(str(payload.get("report", ""))),
                    )
                    return
                if parsed.path == "/report/export":
                    self._send_json(
                        HTTPStatus.OK,
                        runtime.export_report(
                            str(payload.get("report", "")),
                            str(payload["destination"]) if "destination" in payload and payload["destination"] is not None else None,
                        ),
                    )
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown path"})
            except AgentPortalError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, exc.to_dict())

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = HTTPServer(
        (runtime.config.runtime_host, runtime.config.runtime_port),
        AgentPortalHandler,
    )
    server.allow_reuse_address = True
    return server


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
