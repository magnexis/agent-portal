from __future__ import annotations

import importlib.util
import json
import os
import socket
import sys
from pathlib import Path

from .config import DEFAULT_CONFIG_PATH, load_config
from .models import DoctorReport, HealthCheckResult
from .plugin_system import discover_plugins, validate_plugin_manifest


def run_doctor(base_path: Path | None = None) -> DoctorReport:
    root = base_path or Path.cwd()
    config = load_config(root)
    report = DoctorReport()

    report.checks.append(check_python_version())
    report.checks.append(check_dependency("playwright", "Install with `pip install -e ./python`."))
    report.checks.append(check_config_file(root))
    report.checks.append(check_runtime_port(config.runtime_host, config.runtime_port))
    report.checks.append(check_directory_writable(root / config.screenshot_directory, "Screenshot directory"))
    report.checks.append(check_directory_writable(root / config.report_directory, "Report directory"))
    report.checks.extend(check_plugin_manifests(root))
    report.checks.append(check_vscode_extension(root))
    report.checks.append(check_os_support())
    report.checks.append(check_chromium_presence())
    return report


def check_python_version() -> HealthCheckResult:
    if sys.version_info >= (3, 10):
        return HealthCheckResult("python-version", "passed", sys.version.split()[0])
    return HealthCheckResult(
        "python-version",
        "failed",
        sys.version.split()[0],
        "Install Python 3.10 or newer.",
    )


def check_dependency(module_name: str, suggested_fix: str) -> HealthCheckResult:
    found = importlib.util.find_spec(module_name) is not None
    if found:
        return HealthCheckResult(module_name, "passed", "Installed")
    return HealthCheckResult(module_name, "failed", "Missing", suggested_fix)


def check_config_file(root: Path) -> HealthCheckResult:
    config_path = root / DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return HealthCheckResult(
            "config-file",
            "warning",
            f"{config_path.name} not found",
            "Start the runtime once or create the default config with `agent-portal start`.",
        )
    try:
        json.loads(config_path.read_text(encoding="utf8"))
        return HealthCheckResult("config-file", "passed", str(config_path))
    except json.JSONDecodeError as exc:
        return HealthCheckResult(
            "config-file",
            "failed",
            str(exc),
            "Fix the JSON syntax in agent-portal.config.json.",
        )


def check_runtime_port(host: str, port: int) -> HealthCheckResult:
    sock = socket.socket()
    try:
        sock.bind((host, port))
        return HealthCheckResult("runtime-port", "passed", f"{host}:{port} is available")
    except OSError:
        return HealthCheckResult(
            "runtime-port",
            "warning",
            f"{host}:{port} is already in use",
            "Stop the other runtime or choose a different port.",
        )
    finally:
        sock.close()


def check_directory_writable(directory: Path, label: str) -> HealthCheckResult:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        test_file = directory / ".write-test"
        test_file.write_text("ok", encoding="utf8")
        test_file.unlink()
        return HealthCheckResult(label, "passed", str(directory))
    except OSError as exc:
        return HealthCheckResult(
            label,
            "failed",
            str(exc),
            f"Fix filesystem permissions for {directory}.",
        )


def check_plugin_manifests(root: Path) -> list[HealthCheckResult]:
    results: list[HealthCheckResult] = []
    for plugin_manifest in discover_plugins(root):
        errors = validate_plugin_manifest(plugin_manifest)
        if errors:
            results.append(
                HealthCheckResult(
                    f"plugin:{plugin_manifest.parent.name}",
                    "failed",
                    "; ".join(errors),
                    "Fix the manifest fields and retry.",
                )
            )
        else:
            results.append(
                HealthCheckResult(
                    f"plugin:{plugin_manifest.parent.name}",
                    "passed",
                    "Valid"
                )
            )
    return results


def check_vscode_extension(root: Path) -> HealthCheckResult:
    extension_dir = root / "apps" / "vscode-extension"
    package_json = extension_dir / "package.json"
    if package_json.exists():
        return HealthCheckResult("vscode-extension", "passed", str(package_json))
    return HealthCheckResult(
        "vscode-extension",
        "warning",
        str(package_json),
        "Restore the VS Code extension package if editor integration is required.",
    )


def check_os_support() -> HealthCheckResult:
    if os.name == "nt":
        return HealthCheckResult("os-support", "passed", "Windows supported")
    return HealthCheckResult(
        "os-support",
        "warning",
        os.name,
        "Validate browser paths and runtime behavior on this operating system.",
    )


def check_chromium_presence() -> HealthCheckResult:
    locations = [
        Path.home() / "AppData" / "Local" / "ms-playwright",
        Path.home() / ".cache" / "ms-playwright",
    ]
    for playwright_cache in locations:
        if playwright_cache.exists():
            return HealthCheckResult("chromium-installed", "passed", str(playwright_cache))
    return HealthCheckResult(
        "chromium-installed",
        "warning",
        "Chromium cache not found",
        "Run `npx playwright install chromium` and `python -m playwright install chromium` if needed.",
    )
