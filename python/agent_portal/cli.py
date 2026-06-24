from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import load_config, save_default_config
from .doctor import run_doctor
from .plugin_system import discover_plugins, validate_plugin_manifest
from .runtime import PortalRuntime
from .server import serve


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    workspace = Path.cwd()
    save_default_config(workspace)
    config = load_config(workspace)
    host = args.host or config.runtime_host
    port = args.port or config.runtime_port
    runtime_url = f"http://{host}:{port}"

    config.runtime_host = host
    config.runtime_port = port

    try:
        if args.command == "start":
            serve(PortalRuntime(workspace, config))
            return
        if args.command == "stop":
            print_json_or_text(post_json(f"{runtime_url}/control/stop"), args.json)
            return
        if args.command == "status":
            print_json_or_text(get_json(f"{runtime_url}/status"), args.json)
            return
        if args.command == "doctor":
            report = run_doctor(workspace)
            payload = {"checks": [asdict(check) for check in report.checks]}
            print_json_or_text(payload, args.json)
            return
        if args.command == "open":
            payload = {"url": args.url}
            print_json_or_text(post_json(f"{runtime_url}/browser/open", payload), args.json)
            return
        if args.command == "screenshot":
            payload = {"label": args.label}
            print_json_or_text(post_json(f"{runtime_url}/browser/screenshot", payload), args.json)
            return
        if args.command == "report":
            print_json_or_text(post_json(f"{runtime_url}/report/generate"), args.json)
            return
        if args.command == "plugins":
            if args.plugins_command == "list":
                payload = [str(path) for path in discover_plugins(workspace)]
                print_json_or_text(payload, args.json)
                return
            if args.plugins_command == "validate":
                results = {
                    str(path): validate_plugin_manifest(path)
                    for path in discover_plugins(workspace)
                }
                print_json_or_text(results, args.json)
                return
        if args.command == "mcp":
            mcp_cli = load_mcp_cli_module()
            argv = [args.mcp_command]
            if args.host or args.port:
                argv.extend(["--runtime-url", runtime_url])
            if args.json:
                argv.append("--json")
            old_argv = sys.argv[:]
            try:
                sys.argv = ["agent-portal-mcp", *argv]
                mcp_cli.main()
            finally:
                sys.argv = old_argv
            return
    except (HTTPError, URLError) as exc:
        print_json_or_text(
            {
                "error": "Runtime request failed",
                "details": str(exc),
                "suggestedFix": f"Start the runtime with `agent-portal --host {host} --port {port} start`.",
            },
            True if args.json else False,
        )
        raise SystemExit(1) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-portal")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--profile")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("start")
    subparsers.add_parser("stop")
    subparsers.add_parser("status")
    subparsers.add_parser("doctor")

    open_parser = subparsers.add_parser("open")
    open_parser.add_argument("url")

    screenshot_parser = subparsers.add_parser("screenshot")
    screenshot_parser.add_argument("--label", default="manual")

    subparsers.add_parser("report")

    plugins_parser = subparsers.add_parser("plugins")
    plugins_subparsers = plugins_parser.add_subparsers(dest="plugins_command", required=True)
    plugins_subparsers.add_parser("list")
    plugins_subparsers.add_parser("validate")

    mcp_parser = subparsers.add_parser("mcp")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", required=True)
    mcp_subparsers.add_parser("start")
    mcp_subparsers.add_parser("doctor")
    return parser


def get_json(url: str) -> object:
    with urlopen(url) as response:
        return json.loads(response.read().decode("utf8"))


def post_json(url: str, payload: dict[str, object] | None = None) -> object:
    data = json.dumps(payload or {}).encode("utf8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf8"))


def print_json_or_text(payload: object, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, indent=2))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            print(f"{key}: {value}")
        return
    if isinstance(payload, list):
        for entry in payload:
            print(f"- {entry}")
        return
    print(payload)


def load_mcp_cli_module():
    repo_root = Path(__file__).resolve().parents[2]
    mcp_src = repo_root / "packages" / "agent-portal-mcp" / "src"
    if str(mcp_src) not in sys.path:
        sys.path.insert(0, str(mcp_src))
    from agent_portal_mcp import cli as mcp_cli  # type: ignore

    return mcp_cli
