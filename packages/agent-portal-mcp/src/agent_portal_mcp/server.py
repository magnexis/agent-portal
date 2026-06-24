from __future__ import annotations

import json
import sys
from dataclasses import asdict
from typing import Any

from agent_portal_mcp.bridge.runtime_client import AgentPortalRuntimeClient, RuntimeClientError
from agent_portal_mcp.schemas.results import ToolResult
from agent_portal_mcp.tool_registry import ToolDefinition, build_tool_registry


class AgentPortalMcpServer:
    def __init__(self, runtime_url: str = "http://127.0.0.1:8765") -> None:
        self.client = AgentPortalRuntimeClient(runtime_url=runtime_url)
        self.tools = build_tool_registry()

    def serve_stdio(self) -> None:
        while True:
            payload = self._read_message()
            if payload is None:
                return
            response = self.handle_request(payload)
            if response is not None:
                self._write_message(response)

    def handle_request(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        method = payload.get("method")
        request_id = payload.get("id")

        if method == "notifications/initialized":
            return None
        if method == "initialize":
            return self._jsonrpc(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "agent-portal-mcp", "version": "0.1.0"},
                },
            )
        if method == "ping":
            return self._jsonrpc(request_id, {})
        if method == "tools/list":
            return self._jsonrpc(
                request_id,
                {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.input_schema,
                        }
                        for tool in self.tools.values()
                    ]
                },
            )
        if method == "tools/call":
            params = payload.get("params", {})
            name = str(params.get("name", ""))
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}
            result = self.call_tool(name, arguments)
            return self._jsonrpc(
                request_id,
                {
                    "content": [{"type": "text", "text": json.dumps(result.to_dict(), indent=2)}],
                    "structuredContent": result.to_dict(),
                    "isError": not result.ok,
                },
            )

        return self._error(request_id, -32601, f"Method not found: {method}")

    def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        definition = self.tools.get(name)
        if definition is None:
            return ToolResult(
                ok=False,
                tool=name,
                session_id=None,
                action_id=None,
                status="failed",
                risk="blocked",
                message=f"Unknown MCP tool: {name}",
                errors=[f"Tool `{name}` is not registered."],
            )

        try:
            return definition.handler(self.client, arguments)
        except RuntimeClientError as exc:
            return ToolResult(
                ok=False,
                tool=name,
                session_id=None,
                action_id=None,
                status="failed",
                risk="blocked",
                message=str(exc),
                errors=[str(exc)],
            )
        except Exception as exc:
            return ToolResult(
                ok=False,
                tool=name,
                session_id=None,
                action_id=None,
                status="failed",
                risk="blocked",
                message="MCP tool execution failed.",
                errors=[self._redact(str(exc))],
            )

    def _read_message(self) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return None
            if line in {b"\r\n", b"\n"}:
                break
            key, value = line.decode("utf8").split(":", 1)
            headers[key.strip().lower()] = value.strip()

        length = int(headers.get("content-length", "0"))
        if length <= 0:
            return None
        body = sys.stdin.buffer.read(length)
        return json.loads(body.decode("utf8"))

    def _write_message(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf8")
        sys.stdout.buffer.write(f"Content-Length: {len(encoded)}\r\n\r\n".encode("utf8"))
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()

    def _jsonrpc(self, request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _error(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def _redact(self, value: str) -> str:
        token = self.client.token
        if token:
            return value.replace(token, "[REDACTED]")
        return value
