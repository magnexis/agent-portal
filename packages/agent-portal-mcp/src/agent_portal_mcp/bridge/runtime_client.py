from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class RuntimeClientError(RuntimeError):
    pass


class AgentPortalRuntimeClient:
    def __init__(
        self,
        runtime_url: str = "http://127.0.0.1:8765",
        token: str | None = None,
        retries: int = 2,
        timeout_seconds: float = 4.0,
    ) -> None:
        self.runtime_url = runtime_url.rstrip("/")
        self.token = token or self._load_token()
        self.retries = retries
        self.timeout_seconds = timeout_seconds

    def health(self) -> dict[str, Any]:
        return self.get("/health")

    def status(self) -> dict[str, Any]:
        return self.get("/status")

    def propose_action(
        self,
        action_type: str,
        reason: str,
        target: str | None = None,
        payload: str | None = None,
        risk_level: str = "low",
    ) -> dict[str, Any]:
        return self.post(
            "/control/propose-action",
            {
                "actionType": action_type,
                "reason": reason,
                "target": target,
                "payload": payload,
                "riskLevel": risk_level,
            },
        )

    def approve_action(self, action_id: str, execute: bool = False) -> dict[str, Any]:
        return self.post("/control/approve-action", {"actionId": action_id, "execute": execute})

    def reject_action(self, action_id: str, reason: str) -> dict[str, Any]:
        return self.post("/control/reject-action", {"actionId": action_id, "reason": reason})

    def action_queue(self) -> dict[str, Any]:
        return self.post("/control/action-queue", {})

    def set_goal(self, goal: str) -> dict[str, Any]:
        return self.post("/control/goal", {"goal": goal})

    def current_goal(self) -> dict[str, Any]:
        return self.post("/control/goal/current", {})

    def pause(self) -> dict[str, Any]:
        return self.post("/control/pause", {})

    def resume(self) -> dict[str, Any]:
        return self.post("/control/resume", {})

    def stop(self) -> dict[str, Any]:
        return self.post("/control/stop", {})

    def set_action_mode(self, mode: str) -> dict[str, Any]:
        return self.post("/control/action-mode", {"mode": mode})

    def browser_start(self) -> dict[str, Any]:
        return self.post("/browser/start", {})

    def browser_status(self) -> dict[str, Any]:
        return self.post("/browser/status", {})

    def browser_close(self) -> dict[str, Any]:
        return self.post("/browser/close", {})

    def browser_refresh(self) -> dict[str, Any]:
        return self.post("/browser/refresh", {})

    def browser_back(self) -> dict[str, Any]:
        return self.post("/browser/back", {})

    def browser_forward(self) -> dict[str, Any]:
        return self.post("/browser/forward", {})

    def capture(self, label: str = "capture") -> dict[str, Any]:
        return self.post("/browser/capture", {"label": label})

    def read_text(self, selector: str, reason: str) -> dict[str, Any]:
        return self.post("/browser/read-text", {"selector": selector, "reason": reason})

    def read_dom(self) -> dict[str, Any]:
        return self.post("/browser/read-dom", {})

    def read_accessibility_tree(self) -> dict[str, Any]:
        return self.post("/browser/read-accessibility-tree", {})

    def read_console_errors(self) -> dict[str, Any]:
        return self.post("/browser/read-console-errors", {})

    def read_network_failures(self) -> dict[str, Any]:
        return self.post("/browser/read-network-failures", {})

    def inspect(self) -> dict[str, Any]:
        return self.post("/browser/inspect", {})

    def inspect_element(self, selector: str) -> dict[str, Any]:
        return self.post("/browser/inspect-element", {"selector": selector})

    def generate_report(self) -> dict[str, Any]:
        return self.post("/report/generate", {})

    def list_reports(self) -> dict[str, Any]:
        return self.post("/report/list", {})

    def read_report(self, report_name: str) -> dict[str, Any]:
        return self.post("/report/read", {"report": report_name})

    def export_report(self, report_name: str, destination: str | None = None) -> dict[str, Any]:
        return self.post("/report/export", {"report": report_name, "destination": destination})

    def get(self, route: str) -> dict[str, Any]:
        return self._request(route, method="GET")

    def post(self, route: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(route, method="POST", payload=payload)

    def _request(
        self,
        route: str,
        method: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.runtime_url}{route}"
        data = json.dumps(payload or {}).encode("utf8") if method == "POST" else None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                request = Request(url, data=data, headers=headers, method=method)
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf8"))
            except (HTTPError, URLError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.2 * (attempt + 1))
                    continue
        raise RuntimeClientError(
            "Agent Portal runtime is not running. Start it with: agent-portal start"
        ) from last_error

    def _load_token(self) -> str | None:
        env_token = os.getenv("AGENT_PORTAL_TOKEN")
        if env_token:
            return env_token
        config_path = Path.cwd() / "agent-portal.config.json"
        if not config_path.exists():
            return None
        try:
            raw = json.loads(config_path.read_text(encoding="utf8"))
        except json.JSONDecodeError:
            return None
        token = raw.get("api_token")
        return token if isinstance(token, str) and token else None
