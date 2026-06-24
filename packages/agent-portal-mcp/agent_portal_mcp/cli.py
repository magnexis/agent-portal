from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from agent_portal_mcp.doctor import run_doctor
from agent_portal_mcp.server import AgentPortalMcpServer


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent-portal-mcp")
    parser.add_argument("--runtime-url", default="http://127.0.0.1:8765")
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("start")
    subparsers.add_parser("doctor")
    args = parser.parse_args()

    if args.command == "start":
        AgentPortalMcpServer(runtime_url=args.runtime_url).serve_stdio()
        return

    result = run_doctor(runtime_url=args.runtime_url)
    payload = {"checks": [asdict(check) for check in result.checks]}
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    for check in result.checks:
        print(f"{check.status.upper():7} {check.name}: {check.details}")
        if check.suggested_fix:
            print(f"        fix: {check.suggested_fix}")
