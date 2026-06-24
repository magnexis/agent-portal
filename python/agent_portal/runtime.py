from __future__ import annotations

import json
import os
import socket
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from .browser import BrowserController
from .config import load_config
from .exceptions import AgentPortalError, PolicyBlockedError, RuntimeStartupError
from .logging_utils import build_logger
from .models import (
    ActionRequest,
    ActionResult,
    BrowserState,
    RiskPolicy,
    RuntimeConfigModel,
    SessionReport,
    SessionState,
    utc_now,
)
from .plugin_system import discover_plugins, validate_plugin_manifest


RISK_ORDER = ["safe", "low", "medium", "high", "blocked"]


class PortalRuntime:
    def __init__(self, base_path: Path | None = None, config: RuntimeConfigModel | None = None) -> None:
        self.base_path = base_path or Path.cwd()
        self.config = config or load_config(self.base_path)
        self.logger = build_logger("agent_portal.runtime", self.config.log_level)
        self.session = SessionState(session_id=f"session-{utc_now().replace(':', '-')}")
        self.browser_state = BrowserState(browser_name=self.config.default_browser)
        self.risk_policy = RiskPolicy(
            mode=self.config.action_mode,
            approval_threshold=self.config.approval_policy,
            read_only=self.config.action_mode == "read-only",
        )
        self.browser = BrowserController(
            screenshot_directory=self.base_path / self.config.screenshot_directory
        )
        self._lock_path = self.base_path / ".agent-portal-runtime.lock"
        self._started = False

    def startup_validation(self) -> None:
        if self.config.runtime_host == "0.0.0.0":
            self.logger.warning(
                "Runtime is configured to bind publicly.",
                extra={"context": {"host": self.config.runtime_host}},
            )

        try:
            self._ensure_single_instance()
            self._ensure_port_available()
        except OSError as exc:
            raise RuntimeStartupError(
                "Runtime could not bind to the requested port.",
                module="agent_portal.runtime",
                likely_cause="Another runtime instance is already running.",
                suggested_fix="Run `agent-portal stop` or change the configured port.",
                can_continue=False,
            ) from exc

    def start(self) -> None:
        if self._started:
            return
        self.startup_validation()
        self.session.started_at = utc_now()
        self.session.ended_at = None
        self.session.runtime_status = "idle"
        self._started = True
        self.logger.info("Runtime started")

    def stop(self) -> None:
        self.session.runtime_status = "stopped"
        self.session.ended_at = utc_now()
        self.browser_state.connected = False
        try:
            self.browser.stop()
        finally:
            self._remove_lock()
            self._started = False
        self.logger.info("Runtime stopped")

    def pause(self) -> None:
        self.session.runtime_status = "paused"
        self.session.logs.insert(0, "Runtime paused")

    def resume(self) -> None:
        self.session.runtime_status = "acting"
        self.session.logs.insert(0, "Runtime resumed")

    def restart(self) -> None:
        self.stop()
        self.start()

    def set_goal(self, goal: str) -> None:
        self.session.current_goal = goal
        self.session.logs.insert(0, f"Goal set to {goal}")

    def status(self) -> dict[str, Any]:
        return {
            "session": asdict(self.session),
            "browser": asdict(self.browser_state),
            "config": asdict(self.config),
            "policy": asdict(self.risk_policy),
            "plugins": self.list_plugins(),
        }

    def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "runtimeStatus": self.session.runtime_status,
            "browserConnected": self.browser_state.connected,
            "currentUrl": self.browser_state.current_url,
            "pageTitle": self.browser_state.page_title,
            "pluginCount": len(discover_plugins(self.base_path)),
        }

    def ensure_browser(self) -> None:
        if not self.browser.available():
            raise RuntimeStartupError(
                "Python Playwright dependency is missing.",
                module="agent_portal.runtime",
                likely_cause="The Python runtime dependencies were not installed.",
                suggested_fix="Run `pip install -e ./python`.",
                can_continue=False,
            )
        try:
            self.browser.start()
            self.browser_state.connected = True
            self.session.runtime_status = "acting"
        except AgentPortalError as exc:
            self.browser_state.last_error = exc.message
            self.browser_state.connected = False
            raise

    def open_url(self, url: str) -> ActionResult:
        return self._execute_action(
            ActionRequest("open_url", "Open a URL", target=url),
            lambda action: self._open_url_impl(url, action),
        )

    def screenshot(self, label: str = "manual") -> ActionResult:
        return self._execute_action(
            ActionRequest("screenshot", "Capture a screenshot", risk_level="safe"),
            lambda action: self.complete_action(
                action.action_id,
                "Captured screenshot",
                after_screenshot=self.browser.screenshot(label),
            ),
        )

    def click(self, selector: str, reason: str) -> ActionResult:
        return self._execute_action(
            ActionRequest("click", reason, target=selector),
            lambda action: self._click_impl(selector, action),
        )

    def type_text(self, selector: str, value: str, reason: str) -> ActionResult:
        risk = "blocked" if "password" in selector.lower() else "low"
        action = self.propose_action(
            ActionRequest("type", reason, target=selector, payload=value, risk_level=risk)
        )
        if action.status == "blocked":
            raise PolicyBlockedError(
                "Action was blocked because it attempted to type into a protected field.",
                module="agent_portal.runtime",
                likely_cause="The target appears to be a password field or protected input.",
                suggested_fix="Use manual override only if you intend to enter a sensitive value.",
                can_continue=True,
            )
        return self._execute_approved_action(
            action.action_id,
            lambda approved: self._type_impl(selector, value, approved),
        )

    def scroll(self, selector: str | None = None, reason: str = "Scroll the page") -> ActionResult:
        return self._execute_action(
            ActionRequest("scroll", reason, target=selector, risk_level="safe"),
            lambda action: self._scroll_impl(selector, action),
        )

    def hover(self, selector: str, reason: str = "Hover over element") -> ActionResult:
        return self._execute_action(
            ActionRequest("hover", reason, target=selector, risk_level="safe"),
            lambda action: self._hover_impl(selector, action),
        )

    def wait(self, selector: str, reason: str = "Wait for element") -> ActionResult:
        return self._execute_action(
            ActionRequest("wait", reason, target=selector, risk_level="safe"),
            lambda action: self._wait_impl(selector, action),
        )

    def inspect(self) -> dict[str, Any]:
        snapshot = self.browser.inspect()
        self.session.console_errors = self.browser.read_console()
        self.session.network_errors = self.browser.read_network()
        self.browser_state.current_url = snapshot.get("url")
        self.browser_state.page_title = snapshot.get("title")
        return snapshot

    def read_text(self, selector: str, reason: str = "Read text from element") -> dict[str, Any]:
        holder: dict[str, Any] = {}
        action = self._execute_action(
            ActionRequest("inspect", reason, target=selector, risk_level="safe"),
            lambda approved: self._read_text_impl(selector, approved, holder),
        )
        return {
            "action": asdict(action),
            "selector": selector,
            "text": holder.get("text"),
        }

    def execute(self, script: str, reason: str = "Execute script in page context") -> dict[str, Any]:
        holder: dict[str, Any] = {}
        action = self._execute_action(
            ActionRequest("execute", reason, payload=script, risk_level="medium"),
            lambda approved: self._execute_script_impl(script, approved, holder),
        )
        return {
            "action": asdict(action),
            "result": holder.get("result"),
        }

    def capture_snapshot(self, label: str = "capture") -> dict[str, Any]:
        screenshot = self.screenshot(label)
        inspection = self.inspect()
        return {
            "action": asdict(screenshot),
            "inspection": inspection,
            "screenshotPath": screenshot.after_screenshot,
        }

    def propose_action(self, request: ActionRequest) -> ActionResult:
        self._enforce_policy(request)
        next_index = (
            len(self.session.pending_actions)
            + len(self.session.approved_actions)
            + len(self.session.completed_actions)
            + len(self.session.rejected_actions)
            + len(self.session.blocked_actions)
            + len(self.session.failed_actions)
            + 1
        )
        action = ActionResult(
            action_id=f"{request.action_type}-{next_index}",
            action_type=request.action_type,
            status="pending",
            reason=request.reason,
            risk_level=request.risk_level,
        )
        if request.risk_level == "blocked":
            action.status = "blocked"
            self.session.blocked_actions.append(action)
            self.session.runtime_status = "blocked"
        else:
            self.session.pending_actions.append(action)
            self.session.runtime_status = "waiting-approval"
        return action

    def approve_action(self, action_id: str) -> ActionResult:
        action = self._remove_pending(action_id)
        action.status = "approved"
        self.session.approved_actions.append(action)
        self.session.runtime_status = "acting"
        return action

    def reject_action(self, action_id: str, reason: str) -> ActionResult:
        action = self._remove_pending(action_id)
        action.status = "rejected"
        action.result = reason
        self.session.rejected_actions.append(action)
        self.session.runtime_status = "blocked"
        return action

    def complete_action(
        self,
        action_id: str,
        result: str,
        before_screenshot: str | None = None,
        after_screenshot: str | None = None,
    ) -> ActionResult:
        action = next(entry for entry in self.session.approved_actions if entry.action_id == action_id)
        action.status = "completed"
        action.result = result
        action.before_screenshot = before_screenshot
        action.after_screenshot = after_screenshot
        self.session.approved_actions = [
            entry for entry in self.session.approved_actions if entry.action_id != action_id
        ]
        self.session.completed_actions.append(action)
        self.session.console_errors = self.browser.read_console()
        self.session.network_errors = self.browser.read_network()
        self.session.runtime_status = "idle"
        return action

    def fail_action(self, action_id: str, error: AgentPortalError) -> ActionResult:
        action = next(entry for entry in self.session.approved_actions if entry.action_id == action_id)
        action.status = "failed"
        action.error = error.to_dict()
        action.result = error.message
        self.session.approved_actions = [
            entry for entry in self.session.approved_actions if entry.action_id != action_id
        ]
        self.session.failed_actions.append(action)
        self.browser_state.last_error = error.message
        self.session.runtime_status = "failed"
        return action

    def generate_report(self) -> Path:
        report_dir = self.base_path / self.config.report_directory
        report_dir.mkdir(parents=True, exist_ok=True)
        report = SessionReport(
            project_name=self.base_path.name,
            runtime_version="0.1.0",
            session_id=self.session.session_id,
            start_time=self.session.started_at,
            end_time=utc_now(),
            browser_used=self.browser_state.browser_name,
            current_url=self.browser_state.current_url,
            goals=[self.session.current_goal] if self.session.current_goal else [],
            actions_proposed=self.session.pending_actions + self.session.completed_actions,
            actions_approved=self.session.approved_actions + self.session.completed_actions,
            actions_rejected=self.session.rejected_actions,
            actions_blocked=self.session.blocked_actions,
            actions_completed=[action for action in self.session.completed_actions if action.status == "completed"],
            console_errors=self.session.console_errors,
            network_errors=self.session.network_errors,
            screenshots=[
                action.after_screenshot
                for action in self.session.completed_actions + self.session.failed_actions
                if action.after_screenshot
            ],
            risk_events=[
                f"{action.action_type}:{action.risk_level}"
                for action in self.session.completed_actions + self.session.blocked_actions + self.session.failed_actions
            ],
            failed_steps=[action.reason for action in self.session.failed_actions],
            suggested_fixes=[
                "Review blocked or rejected actions before retrying.",
                "Check local development server health if navigation or network actions fail.",
            ],
            reproduction_steps=[
                action.action_type for action in self.session.completed_actions
            ],
            environment_details={
                "host": self.config.runtime_host,
                "port": str(self.config.runtime_port),
                "browser": self.config.default_browser,
            },
        )
        report_path = report_dir / f"{self.session.session_id}.json"
        report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf8")
        return report_path

    def list_plugins(self) -> list[dict[str, Any]]:
        manifests: list[dict[str, Any]] = []
        for plugin_path in discover_plugins(self.base_path):
            manifests.append(
                {
                    "path": str(plugin_path),
                    "errors": validate_plugin_manifest(plugin_path),
                }
            )
        return manifests

    def _enforce_policy(self, request: ActionRequest) -> None:
        haystack = f"{request.reason} {request.target or ''} {request.payload or ''}".lower()
        if self.risk_policy.read_only and request.action_type not in {"inspect", "screenshot", "wait"}:
            request.risk_level = "blocked"
        elif any(token in haystack for token in ["payment", "billing", "checkout", "card"]):
            request.risk_level = "blocked"
        elif any(token in haystack for token in ["delete", "drop database", "destroy"]):
            request.risk_level = "high"
        elif any(token in haystack for token in ["submit", "send", "publish", "login"]):
            request.risk_level = max_risk(request.risk_level, "medium")

        if request.target and "password" in request.target.lower():
            request.risk_level = "blocked"

        if self.risk_policy.domain_lock and request.action_type == "open_url" and request.target:
            if self.risk_policy.domain_lock not in request.target:
                request.risk_level = "blocked"

    def _remove_pending(self, action_id: str) -> ActionResult:
        for index, action in enumerate(self.session.pending_actions):
            if action.action_id == action_id:
                return self.session.pending_actions.pop(index)
        raise AgentPortalError(
            f"Pending action {action_id} was not found.",
            module="agent_portal.runtime",
            likely_cause="The action was already handled or the ID is incorrect.",
            suggested_fix="Refresh the action queue and retry the operation.",
            can_continue=True,
        )

    def _capture_if_allowed(self, label: str) -> str | None:
        if not self.config.sensitive_screenshots_enabled and self.config.safe_mode:
            return None
        return self.browser.screenshot(label)

    def _execute_action(
        self,
        request: ActionRequest,
        callback: Callable[[ActionResult], ActionResult],
    ) -> ActionResult:
        action = self.propose_action(request)
        if action.status == "blocked":
            raise PolicyBlockedError(
                "Action was blocked by the runtime policy engine.",
                module="agent_portal.runtime",
                likely_cause="The action exceeded the current safety policy or approval boundary.",
                suggested_fix="Review the queue, adjust steering mode, or manually override the action if appropriate.",
                can_continue=True,
            )
        return self._execute_approved_action(action.action_id, callback)

    def _execute_approved_action(
        self,
        action_id: str,
        callback: Callable[[ActionResult], ActionResult],
    ) -> ActionResult:
        approved = self.approve_action(action_id)
        try:
            result = callback(approved)
            self.browser_state.current_url = self.browser.current_url()
            self.browser_state.page_title = self.browser.current_title()
            return result
        except AgentPortalError as exc:
            self.fail_action(action_id, exc)
            raise
        except Exception as exc:
            wrapped = AgentPortalError(
                "Browser action failed unexpectedly.",
                module="agent_portal.runtime",
                likely_cause=str(exc),
                suggested_fix="Inspect the runtime logs and browser state, then retry the action.",
                can_continue=True,
            )
            self.fail_action(action_id, wrapped)
            raise wrapped from exc

    def _open_url_impl(self, url: str, action: ActionResult) -> ActionResult:
        before = self._capture_if_allowed(f"{action.action_id}-before")
        self.browser.open_url(url)
        after = self._capture_if_allowed(f"{action.action_id}-after")
        return self.complete_action(action.action_id, "Opened URL", before, after)

    def _click_impl(self, selector: str, action: ActionResult) -> ActionResult:
        before = self._capture_if_allowed(f"{action.action_id}-before")
        self.browser.click(selector)
        after = self._capture_if_allowed(f"{action.action_id}-after")
        return self.complete_action(action.action_id, "Clicked element", before, after)

    def _type_impl(self, selector: str, value: str, action: ActionResult) -> ActionResult:
        before = self._capture_if_allowed(f"{action.action_id}-before")
        self.browser.type_text(selector, value)
        after = self._capture_if_allowed(f"{action.action_id}-after")
        return self.complete_action(action.action_id, "Typed into element", before, after)

    def _scroll_impl(self, selector: str | None, action: ActionResult) -> ActionResult:
        before = self._capture_if_allowed(f"{action.action_id}-before")
        self.browser.scroll(selector)
        after = self._capture_if_allowed(f"{action.action_id}-after")
        return self.complete_action(action.action_id, "Scrolled", before, after)

    def _hover_impl(self, selector: str, action: ActionResult) -> ActionResult:
        before = self._capture_if_allowed(f"{action.action_id}-before")
        self.browser.hover(selector)
        after = self._capture_if_allowed(f"{action.action_id}-after")
        return self.complete_action(action.action_id, "Hovered element", before, after)

    def _wait_impl(self, selector: str, action: ActionResult) -> ActionResult:
        self.browser.wait(selector)
        return self.complete_action(action.action_id, "Waited for element")

    def _read_text_impl(
        self,
        selector: str,
        action: ActionResult,
        holder: dict[str, Any],
    ) -> ActionResult:
        holder["text"] = self.browser.read_text(selector)
        after = self._capture_if_allowed(f"{action.action_id}-after")
        return self.complete_action(action.action_id, "Read text from element", after_screenshot=after)

    def _execute_script_impl(
        self,
        script: str,
        action: ActionResult,
        holder: dict[str, Any],
    ) -> ActionResult:
        holder["result"] = self.browser.execute(script)
        after = self._capture_if_allowed(f"{action.action_id}-after")
        return self.complete_action(action.action_id, "Executed browser script", after_screenshot=after)

    def _ensure_single_instance(self) -> None:
        if self._lock_path.exists():
            raise OSError("Runtime lock file already exists")
        self._lock_path.write_text(str(os.getpid()), encoding="utf8")

    def _ensure_port_available(self) -> None:
        sock = socket.socket()
        try:
            sock.bind((self.config.runtime_host, self.config.runtime_port))
        finally:
            sock.close()

    def _remove_lock(self) -> None:
        if self._lock_path.exists():
            self._lock_path.unlink()


def max_risk(left: str, right: str) -> str:
    return left if RISK_ORDER.index(left) >= RISK_ORDER.index(right) else right
