# Architecture

See [docs/architecture.md](docs/architecture.md) for the detailed architecture document.

## Current Layers

- `python/agent_portal`: primary local runtime, Playwright process owner, and REST/WebSocket server scaffold
- `apps/vscode-extension`: developer control panel for the running runtime
- `connectors/`: integration entry points for ChatGPT tools, Claude MCP, Gemini, and generic APIs
- `packages/core`: shared TypeScript-side control logic, policy, reporting, and contracts
- `packages/sdk`: developer-facing TypeScript API
- `packages/mcp-server`: tool-facing command surface
- `apps/desktop`: local proving ground and runtime demo
