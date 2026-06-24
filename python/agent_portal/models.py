from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


RiskLevel = Literal["safe", "low", "medium", "high", "blocked"]
ActionStatus = Literal["pending", "approved", "rejected", "completed", "failed", "blocked"]
RuntimeStatus = Literal[
    "idle",
    "thinking",
    "acting",
    "waiting-approval",
    "paused",
    "blocked",
    "finished",
    "failed",
    "stopped",
]
ActionMode = Literal["read-only", "assisted", "autonomous", "manual-override"]


@dataclass(slots=True)
class RuntimeConfigModel:
    runtime_host: str = "127.0.0.1"
    runtime_port: int = 8765
    screenshot_directory: str = "workspaces/runtime/screenshots"
    report_directory: str = "workspaces/runtime/reports"
    default_browser: str = "chromium"
    action_mode: ActionMode = "assisted"
    approval_policy: RiskLevel = "medium"
    allowed_domains: list[str] = field(default_factory=list)
    blocked_domains: list[str] = field(default_factory=list)
    enabled_plugins: list[str] = field(default_factory=list)
    log_level: str = "INFO"
    retention_days: int = 14
    sensitive_screenshots_enabled: bool = False
    safe_mode: bool = True
    api_token: str | None = None


@dataclass(slots=True)
class BrowserState:
    browser_name: str = "chromium"
    connected: bool = False
    current_url: str | None = None
    page_title: str | None = None
    last_error: str | None = None
    session_id: str | None = None


@dataclass(slots=True)
class RiskPolicy:
    mode: ActionMode = "assisted"
    approval_threshold: RiskLevel = "medium"
    domain_lock: str | None = None
    tab_lock: str | None = None
    read_only: bool = False


@dataclass(slots=True)
class PluginManifestModel:
    name: str
    version: str
    type: str
    permissions: list[str]
    entryPoint: str | None = None
    commands: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    panels: list[str] = field(default_factory=list)
    lifecycleHooks: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ActionRequest:
    action_type: str
    reason: str
    target: str | None = None
    payload: str | None = None
    risk_level: RiskLevel = "low"


@dataclass(slots=True)
class ActionResult:
    action_id: str
    action_type: str
    status: ActionStatus
    reason: str
    result: str | None = None
    error: dict[str, object] | None = None
    risk_level: RiskLevel = "low"
    before_screenshot: str | None = None
    after_screenshot: str | None = None
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class SessionState:
    session_id: str
    started_at: str = field(default_factory=utc_now)
    ended_at: str | None = None
    runtime_status: RuntimeStatus = "idle"
    current_goal: str | None = None
    pending_actions: list[ActionResult] = field(default_factory=list)
    approved_actions: list[ActionResult] = field(default_factory=list)
    completed_actions: list[ActionResult] = field(default_factory=list)
    rejected_actions: list[ActionResult] = field(default_factory=list)
    blocked_actions: list[ActionResult] = field(default_factory=list)
    failed_actions: list[ActionResult] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    network_errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class HealthCheckResult:
    name: str
    status: Literal["passed", "warning", "failed"]
    details: str
    suggested_fix: str | None = None


@dataclass(slots=True)
class DoctorReport:
    checks: list[HealthCheckResult] = field(default_factory=list)


@dataclass(slots=True)
class SessionReport:
    project_name: str
    runtime_version: str
    session_id: str
    start_time: str
    end_time: str
    browser_used: str
    current_url: str | None
    goals: list[str]
    actions_proposed: list[ActionResult]
    actions_approved: list[ActionResult]
    actions_rejected: list[ActionResult]
    actions_blocked: list[ActionResult]
    actions_completed: list[ActionResult]
    console_errors: list[str]
    network_errors: list[str]
    screenshots: list[str]
    risk_events: list[str]
    failed_steps: list[str]
    suggested_fixes: list[str]
    reproduction_steps: list[str]
    environment_details: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
