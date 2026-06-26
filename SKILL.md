# Agent Portal — SKILL.md

> Instructions for AI coding agents (Codex, Claude Code, Cursor, Windsurf, Copilot, etc.)
> working on this repository.

## Project Overview

Agent Portal is a **desktop-native operating environment for AI agents**. It gives LLMs a
controlled visual workspace with browser automation, action policies, plugin extensibility,
and real-time steering — all running locally on the developer's machine.

The system has two primary surfaces:

1. **Python runtime** (`python/agent_portal/`) — owns the Playwright browser session,
   serves the HTTP API, enforces safety policies, and generates reports. This is the
   source of truth for all runtime state.

2. **TypeScript clients** (`apps/`, `packages/`, `connectors/`) — consumer-layer code
   that talks to the Python runtime over HTTP. Includes a VS Code extension, MCP bridge,
   SDK, and connector scaffolds.

## Repository Structure

```
agent-portal/
├── python/                          # PYTHON RUNTIME (source of truth)
│   ├── agent_portal/
│   │   ├── runtime.py               # PortalRuntime — core state machine, browser lifecycle, policy engine
│   │   ├── server.py                # HTTP API server (single-threaded HTTPServer)
│   │   ├── browser.py               # BrowserController — Playwright wrapper for all browser actions
│   │   ├── models.py                # Data models: RuntimeConfigModel, ActionRequest, ActionResult, etc.
│   │   ├── config.py                # Config loading from agent-portal.config.json
│   │   ├── cli.py                   # CLI entry point (agent-portal start/stop/doctor/...)
│   │   ├── doctor.py                # Diagnostic health checks
│   │   ├── plugin_system.py         # Plugin manifest discovery and validation
│   │   ├── validation.py            # Input validation (URLs, selectors, XSS detection)
│   │   ├── rate_limit.py            # Per-client rate limiting
│   │   ├── metrics.py               # Telemetry and performance tracking
│   │   ├── logging_utils.py         # Structured logger factory
│   │   └── exceptions.py            # AgentPortalError hierarchy
│   └── tests/                       # Python unit tests (unittest)
│
├── packages/
│   ├── core/                        # Shared TypeScript types, policies, contracts
│   ├── sdk/                         # Runtime client SDK (TypeScript)
│   ├── mcp-server/                  # MCP tool bridge surface (TypeScript)
│   └── agent-portal-mcp/            # Python MCP server — exposes runtime as MCP tools
│       └── agent_portal_mcp/
│           ├── server.py            # MCP server entry point
│           ├── bridge/runtime_client.py  # HTTP client to Python runtime
│           ├── tools/               # MCP tool definitions (browser, navigation, steering, etc.)
│           ├── schemas/             # Pydantic-like action/result schemas
│           └── security/policy.py   # MCP-level security policy
│
├── apps/
│   ├── desktop/                     # Local dev proving ground (Vite + vanilla TS)
│   └── vscode-extension/            # VS Code extension (developer control panel)
│
├── connectors/
│   ├── chatgpt-tools/               # ChatGPT tool-use connector
│   ├── claude-mcp-server/           # Claude MCP integration
│   ├── gemini-connector/            # Gemini integration
│   └── rest-websocket-api/          # Generic transport connector
│
├── plugins/                         # Manifest-driven plugins
│   ├── plugin.schema.json           # JSON Schema for plugin.json manifests
│   └── */plugin.json                # Plugin manifests
│
├── agent-portal.config.json         # Runtime configuration
├── docs/                            # Architecture, roadmap
├── tests/*.test.mjs                 # Node.js integration tests
└── scripts/                         # Build/release scripts
```

## Build & Test Commands

### Setup

```bash
# Node dependencies (for TypeScript workspaces and tests)
npm install

# Playwright browser binaries (required for Python runtime)
npx playwright install chromium

# Python runtime (editable install)
pip install -e ./python
```

### Build

```bash
# Build all TypeScript workspaces
npm run build

# Type-check everything
npm run check
```

### Test

```bash
# Run all tests (Python unit tests + MCP tests + Node tests)
npm test

# Python-only
python -m unittest discover -s python/tests -v

# Python MCP tests
python -m unittest discover -s packages/agent-portal-mcp/tests -v

# Node integration tests only
node --test tests/*.test.mjs

# Individual Python test file
python -m unittest python/tests/test_runtime.py -v
```

### Run the Runtime

```bash
# Start the Python runtime server (listens on 127.0.0.1:8765)
agent-portal start

# Health check
agent-portal doctor

# Open a URL in the controlled browser
agent-portal open --url https://example.com

# Take a screenshot
agent-portal screenshot --label my-test

# Generate a session report
agent-portal report

# List discovered plugins
agent-portal plugins list
```

### MCP Server

```bash
# Start the MCP bridge server (requires runtime running)
agent-portal mcp start
```

### Release Packaging

```bash
npm run release:python    # → releases/python/*.tar.gz, *.whl
npm run release:desktop   # → releases/desktop/agent-portal-desktop.zip
```

## Key Architecture Rules

### Runtime Ownership

The Python runtime (`PortalRuntime` in `runtime.py`) is the **single owner** of browser
sessions and state. No TypeScript code should launch Playwright directly — all browser
operations go through the HTTP API at `127.0.0.1:8765`.

### Single-Threaded Server

The HTTP server in `server.py` uses Python's `HTTPServer` (NOT `ThreadingHTTPServer`).
This is intentional — Playwright sync greenlets are pinned to the thread that started the
browser. A threaded server would crash every browser action with a greenlet thread-switch
error. **Do not change to ThreadingHTTPServer.**

### Data Flow

```
LLM/Agent → Connector/MCP → HTTP POST → Python Runtime → Playwright → Browser
                  ↓                                    ↓
              Approval Queue ←── Risk Policy ←── ActionResult
```

1. External clients (MCP, SDK, connectors) send action requests via HTTP POST.
2. The runtime evaluates risk policy and may queue the action for approval.
3. If approved, the action is executed against the Playwright browser.
4. Results (including screenshots) are returned as JSON.

### Risk & Approval Model

- `ActionMode`: `read-only`, `assisted`, `autonomous`, `manual-override`
- `RiskLevel`: `safe`, `low`, `medium`, `high`, `blocked`
- Actions at or above the `approval_policy` threshold are queued for human approval.
- Password-typing and payment-related actions are always blocked.
- Domain allow/block lists can restrict navigation scope.

### Configuration

Runtime behavior is controlled by `agent-portal.config.json` at the workspace root.
The `RuntimeConfigModel` dataclass in `models.py` defines all fields with defaults.
Config is loaded by `config.py` using `load_config()`.

### Error Handling

All runtime errors inherit from `AgentPortalError` (in `exceptions.py`). Use `str(error)`
to get the message — do NOT access `.message` attribute (it doesn't exist). Each error
includes `module`, `likely_cause`, `suggested_fix`, and `can_continue` fields.

### Plugin System

Plugins are manifest-driven (`plugin.json` files). The schema is in
`plugins/plugin.schema.json`. Manifests declare name, version, type, permissions,
commands, settings, panels, and lifecycle hooks. Validation happens in
`plugin_system.py`.

## Coding Conventions

### Python

- **Python 3.10+** with `from __future__ import annotations` in every file.
- Use **dataclasses** with `slots=True` for all model types (see `models.py`).
- Use **type hints** everywhere. Use `Literal` types for enums (see `RiskLevel`, etc.).
- Use `pathlib.Path` for file paths, never raw strings.
- The custom logger: `from .logging_utils import build_logger`.
- Structured errors: raise `AgentPortalError` subclasses, never bare `Exception`.
- HTTP responses: always JSON with `Content-Type: application/json`.
- All browser actions go through `BrowserController` — never call Playwright directly
  from outside `browser.py`.

### TypeScript

- Strict TypeScript (`"strict": true` in all tsconfig.json files).
- ESM modules (`"type": "module"` where applicable).
- The monorepo uses npm workspaces (`apps/*`, `packages/*`).
- Shared types live in `packages/core/src/index.ts`.
- The SDK (`packages/sdk/`) is a thin HTTP client — it does NOT own browser sessions.

### MCP Tools

- MCP tools are defined as plain functions in `packages/agent-portal-mcp/agent_portal_mcp/tools/`.
- Each function takes `(client: AgentPortalRuntimeClient, args: dict) -> ToolResult`.
- Use `execute_or_queue()` from `tools/common.py` to handle risk-checking and queuing.
- Tool schemas (input/output) are in `schemas/actions.py` and `schemas/results.py`.

## HTTP API Reference

All endpoints are on `http://127.0.0.1:8765` (configurable).

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Liveness check |
| GET | `/status` | Full runtime state |
| GET | `/report/latest` | Latest session report |
| POST | `/control/start` | Start the runtime |
| POST | `/control/stop` | Stop the runtime |
| POST | `/control/pause` | Pause execution |
| POST | `/control/resume` | Resume execution |
| POST | `/control/restart` | Restart runtime |
| POST | `/control/goal` | Set current goal |
| POST | `/control/approve-next` | Approve pending action |
| POST | `/control/reject-next` | Reject pending action |
| POST | `/browser/start` | Launch browser |
| POST | `/browser/open` | Navigate to URL |
| POST | `/browser/click` | Click element |
| POST | `/browser/type` | Type into element |
| POST | `/browser/scroll` | Scroll the page |
| POST | `/browser/hover` | Hover over element |
| POST | `/browser/wait` | Wait for condition |
| POST | `/browser/screenshot` | Capture screenshot |
| POST | `/browser/capture` | Capture page text |
| POST | `/browser/inspect` | Inspect element |
| POST | `/browser/read-text` | Read page text |
| POST | `/browser/execute` | Execute JS in page |
| POST | `/report/generate` | Generate report |

Authentication (optional): Bearer token via `Authorization` header, configured in
`agent-portal.config.json` → `api_token`.

## Common Tasks for LLM Agents

### Adding a new browser action

1. Add the method to `BrowserController` in `python/agent_portal/browser.py`.
2. Add the route handler in `python/agent_portal/server.py` → `do_POST()`.
3. Add risk scoring in `python/agent_portal/runtime.py` → `execute_action()`.
4. Add the MCP tool function in `packages/agent-portal-mcp/agent_portal_mcp/tools/browser.py`.
5. Add a Python unit test in `python/tests/`.
6. Run `npm test` to verify.

### Adding a new MCP tool

1. Create a function in the appropriate file under
   `packages/agent-portal-mcp/agent_portal_mcp/tools/`.
2. Follow the pattern: `def tool_name(client, args) -> ToolResult`.
3. Use `execute_or_queue()` for risk-checked actions, or `build_result()` for
   read-only queries.
4. Register the tool in `packages/agent-portal-mcp/agent_portal_mcp/tools/__init__.py`.

### Adding a new plugin

1. Create a directory under `plugins/`.
2. Add a `plugin.json` manifest following `plugins/plugin.schema.json`.
3. Validate with `agent-portal plugins list`.

### Modifying risk policy

Risk scoring lives in `python/agent_portal/runtime.py` in the `_score_action()` method.
The `RISK_ORDER` list defines severity ordering. Blocked categories (passwords, payments)
are checked before scoring.

### Changing the server

The server is in `python/agent_portal/server.py`. Key rules:
- Always use `HTTPServer`, never `ThreadingHTTPServer`.
- All responses use `_send_json()`.
- All POST bodies use `_read_json()`.
- Check auth with `_authorize()` before processing.
- Return proper HTTP status codes.

## Safety-Critical Areas

- **`validation.py`** — Input sanitization, XSS detection, dangerous protocol blocking.
  Do not weaken these checks.
- **`rate_limit.py`** — Prevents abuse. Do not remove rate limits.
- **`server.py`** — Must stay single-threaded. Do not switch to async or threaded.
- **`runtime.py`** — Risk scoring and action blocking. High-risk actions must be escalated.
- **`browser.py`** — All Playwright calls go here. Do not bypass for direct browser access.

## Testing Patterns

Python tests use `unittest`. Each test file in `python/tests/` tests one module.
Tests create `PortalRuntime` instances with test configs and mock browser operations
where needed. See `test_runtime.py` and `test_server.py` for patterns.

Node tests in `tests/*.test.mjs` are integration tests that verify the workspace
builds, extension manifests are valid, and HTTP routes behave correctly against
a running runtime.

## Published Packages

- **PyPI**: `agent-portal` (Python runtime)
- **VS Code Marketplace**: Agent Portal extension (publisher: `magnificent-language`)
- **npm**: `agent-portal-2` (scoped due to name conflict)