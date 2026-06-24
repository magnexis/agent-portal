from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from typing import Literal

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient, RuntimeClientError
from agent_portal_mcp.tool_registry import build_tool_registry


@dataclass(slots=True)
class DoctorCheck:
    name: str
    status: Literal["passed", "warning", "failed"]
    details: str
    suggested_fix: str | None = None


@dataclass(slots=True)
class DoctorResult:
    checks: list[DoctorCheck] = field(default_factory=list)


def run_doctor(runtime_url: str = "http://127.0.0.1:8765") -> DoctorResult:
    result = DoctorResult()
    result.checks.append(_check_python_version())
    result.checks.append(_check_package_installed())
    result.checks.append(_check_localhost_binding(runtime_url))
    result.checks.append(_check_tools_registered())
    result.checks.append(_check_runtime(runtime_url))
    return result


def _check_python_version() -> DoctorCheck:
    if sys.version_info >= (3, 10):
        return DoctorCheck("python-version", "passed", sys.version.split()[0])
    return DoctorCheck("python-version", "failed", sys.version.split()[0], "Use Python 3.10 or newer.")


def _check_package_installed() -> DoctorCheck:
    if importlib.util.find_spec("agent_portal_mcp") is not None:
        return DoctorCheck("mcp-package", "passed", "Installed")
    return DoctorCheck("mcp-package", "warning", "Not installed into current environment", "Install with `pip install -e ./packages/agent-portal-mcp`.")


def _check_localhost_binding(runtime_url: str) -> DoctorCheck:
    if runtime_url.startswith("http://127.0.0.1") or runtime_url.startswith("http://localhost"):
        return DoctorCheck("localhost-binding", "passed", runtime_url)
    return DoctorCheck("localhost-binding", "warning", runtime_url, "Prefer localhost-only runtime URLs for MCP usage.")


def _check_tools_registered() -> DoctorCheck:
    count = len(build_tool_registry())
    return DoctorCheck("tool-registry", "passed", f"{count} tools registered")


def _check_runtime(runtime_url: str) -> DoctorCheck:
    client = AgentPortalRuntimeClient(runtime_url=runtime_url)
    try:
        health = client.health()
    except RuntimeClientError:
        return DoctorCheck(
            "runtime-reachable",
            "failed",
            runtime_url,
            "Agent Portal runtime is not running. Start it with: agent-portal start",
        )

    version = str(health.get("runtimeVersion", "unknown"))
    return DoctorCheck("runtime-reachable", "passed", f"{runtime_url} (runtime {version})")
