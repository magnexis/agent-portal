<p align="center">
  <img src="assets/branding/agent-portal-logo.png" alt="Agent Portal Logo" width="420" />
</p>

# Agent Portal

Agent Portal is a desktop-native operating environment for AI agents.

Instead of limiting an LLM to code generation, Agent Portal gives it a controlled visual workspace where it can understand, navigate, test, and interact with real user interfaces, local applications, browser sessions, development environments, and project ecosystems.

## Vision

Give AI agents eyes, hands, memory, context, and permissions.

That means combining:

- visual understanding
- browser and desktop control
- long-lived workspace memory
- multi-agent orchestration
- test and reporting workflows
- secure execution boundaries

## What Exists Today

The project now has a real local runtime foundation rather than just a concept scaffold. The current repository includes:

- a Python-first local runtime in `python/agent_portal`
- Playwright-backed browser control for open, click, type, hover, scroll, wait, inspect, screenshot, execute, and text reading
- a local HTTP runtime server for health, status, control, browser, and report routes
- an agent steering and policy layer with pause, resume, stop, queue approval, blocked actions, and risk-aware behavior
- report generation with runtime state, actions, risk events, screenshots, and reproduction steps
- plugin manifest discovery and validation
- a VS Code extension control center that talks directly to the Python runtime
- a TypeScript SDK surface that is being shifted into a client of the Python runtime
- connector scaffolds for ChatGPT-style tools, Claude MCP, Gemini, and generic REST/WebSocket integration
- a desktop demo surface for local runtime verification
- documentation for installation, quickstart, runtime, CLI, safety, testing, plugins, and architecture

## Core Direction

The strongest current architectural direction is:

```text
Agent Portal
│
├── agent-portal Python package
│   ├── local runtime owner
│   ├── Playwright browser/session owner
│   ├── control and safety policy engine
│   ├── HTTP API server
│   └── reporting and plugin validation
│
├── VS Code extension
│   └── developer-facing control panel
│
├── TypeScript SDK
│   └── client wrapper for the Python runtime
│
└── Agent connectors
    ├── ChatGPT tools
    ├── Claude MCP server
    ├── Gemini connector
    └── REST/WebSocket API
```

The key principle is that runtime and browser session ownership should live in the Python runtime server, while editor tooling, SDKs, and connectors should act as clients of that runtime.

## Repo Layout

```text
agent-portal.config.json      Runtime configuration
assets/
  branding/                   Shared logo and visual brand assets
apps/
  desktop/                    Desktop runtime demo and proving ground
  vscode-extension/           Developer control panel
connectors/
  chatgpt-tools/              ChatGPT-facing connector direction
  claude-mcp-server/          Claude MCP integration direction
  gemini-connector/           Gemini integration direction
  rest-websocket-api/         Generic transport direction
docs/
  architecture.md             System design and boundaries
  roadmap.md                  Suggested phased delivery plan
packages/
  core/                       Shared TypeScript contracts and intelligence helpers
  sdk/                        Runtime client SDK
  mcp-server/                 Tool-facing MCP bridge surface
plugins/
  */plugin.json               Plugin manifests and examples
python/
  agent_portal/               Local runtime, browser control, CLI, doctor, server
  tests/                      Python runtime test suite
tests/
  *.test.mjs                  Workspace-level Node tests
```

## Runtime Capabilities

The local Python runtime currently covers these areas:

- startup validation and single-instance locking
- runtime health checks and doctor diagnostics
- browser launch and cleanup
- browser action execution with structured errors
- policy-aware action approval and blocking
- screenshot evidence capture
- report generation
- plugin manifest validation
- localhost-first serving with optional bearer token auth

### Runtime HTTP Routes

- `GET /health`
- `GET /status`
- `GET /report/latest`
- `POST /control/start`
- `POST /control/stop`
- `POST /control/pause`
- `POST /control/resume`
- `POST /control/restart`
- `POST /control/goal`
- `POST /control/approve-next`
- `POST /control/reject-next`
- `POST /browser/start`
- `POST /browser/open`
- `POST /browser/click`
- `POST /browser/type`
- `POST /browser/scroll`
- `POST /browser/hover`
- `POST /browser/wait`
- `POST /browser/screenshot`
- `POST /browser/capture`
- `POST /browser/inspect`
- `POST /browser/read-text`
- `POST /browser/execute`
- `POST /report/generate`

## Agent Steering

The current steering model is focused on keeping the runtime usable and safe while still allowing automation:

- pause agent execution
- resume execution
- stop execution
- inspect pending actions
- approve next pending action
- reject next pending action
- assign or redirect current goal
- risk-score actions
- block password typing
- block billing and payment-style actions
- escalate destructive actions

The longer-term target is a fuller steering layer with richer action editing, manual override states, and live queue streaming.

## Getting Started

1. Install Node dependencies:

```bash
npm install
```

2. Install Playwright browser binaries:

```bash
npx playwright install chromium
```

3. Install the Python runtime package:

```bash
pip install -e ./python
```

4. Run a health check:

```bash
agent-portal doctor
```

5. Start the Python runtime:

```bash
agent-portal start
```

6. In another terminal, run the desktop demo:

```bash
npm run dev --workspace @agent-portal/desktop
```

7. Open the VS Code extension sidebar and connect to the runtime.

## Developer Workflow

Typical local workflow:

1. Start your local app on something like `localhost:3000` or `localhost:5173`.
2. Start Agent Portal with `agent-portal start`.
3. Connect the VS Code extension to `http://127.0.0.1:8765`.
4. Use the runtime or SDK to open the app, inspect the page, and drive actions.
5. Capture screenshots and reports for QA or debugging.
6. Review blocked or pending actions through the control surface.

## VS Code Extension

The VS Code extension lives in `apps/vscode-extension` and is designed to be the developer-facing control panel.

It currently provides:

- a branded sidebar view
- runtime start, stop, and restart commands
- runtime polling and status display
- pending action queue display
- approve/reject controls
- current goal display
- local dev server detection
- quick access to reports and docs

Important settings:

- `agentPortal.runtimeUrl`
- `agentPortal.preferredLocalDevPort`

## SDK And Connectors

The TypeScript SDK is shifting toward a thin client model that targets the Python runtime instead of owning browser sessions itself.

Connector direction:

- ChatGPT tools should translate tool calls into runtime API actions
- Claude MCP should expose runtime tools and reports over MCP
- Gemini connector should mirror the same runtime contract
- REST/WebSocket connector should become the stable integration boundary for all external clients

## Plugins

The plugin model is manifest-driven.

Each plugin can declare:

- name
- version
- type
- permissions
- entry point
- commands
- settings
- panels
- lifecycle hooks

The repository includes example and product-surface plugin manifests under `plugins/`.

## Testing

Current verification commands:

```bash
python -m compileall python
python -m unittest discover -s python/tests -v
npm run check
npm test
```

These cover:

- Python runtime compilation
- runtime unit tests
- doctor/config/plugin validation
- HTTP server behavior
- workspace TypeScript builds
- extension manifest expectations
- local browser/runtime workflow coverage in Node tests

## Safety And Reliability

Current hardening themes include:

- localhost binding by default
- optional local bearer token auth
- structured runtime errors
- duplicate-instance prevention
- graceful shutdown paths
- blocked high-risk categories
- better user-facing diagnostics through `agent-portal doctor`
- report-based traceability for actions and failures

## Documentation

Top-level docs available in this repo:

- `INSTALLATION.md`
- `QUICKSTART.md`
- `CLI.md`
- `RUNTIME.md`
- `PYTHON_SDK.md`
- `VS_CODE_EXTENSION.md`
- `AGENT_STEERING.md`
- `PLUGIN_SYSTEM.md`
- `SAFETY_MODEL.md`
- `TESTING.md`
- `TROUBLESHOOTING.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`

## Near-Term Priorities

1. Complete the migration of live session ownership from TypeScript runtime surfaces into the Python runtime server.
2. Add a broadcast channel for live runtime events so the extension and connectors can stream state instead of polling.
3. Expand approval flow from "approve next pending action" into richer queued-action execution control.
4. Expand `VisionCore` from heuristics into a stronger multimodal understanding engine.
5. Add durable memory retrieval, comparison, and project-aware context reuse.
6. Extend runtime understanding beyond the browser into desktop applications and developer tools.
