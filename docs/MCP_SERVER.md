# MCP Server

## What MCP Is

MCP, or Model Context Protocol, is a structured way for AI clients to discover and call tools through a standard interface.

## Why Agent Portal Uses MCP

Agent Portal already has a local runtime, policy engine, browser control layer, reporting, and steering controls. MCP turns those capabilities into a consistent tool surface that other AI clients can connect to without custom one-off integrations.

## Start The Runtime

```bash
agent-portal start
```

## Start The MCP Server

```bash
agent-portal mcp start
```

or:

```bash
agent-portal-mcp start
```

## Available Tool Groups

- Browser
- Navigation
- Inspection
- Agent Steering
- Reports

## Security Model

- localhost-first runtime URL by default
- optional bearer token through `AGENT_PORTAL_TOKEN` or `agent-portal.config.json`
- risky actions are classified before execution
- blocked actions are never auto-executed
- approval-required actions stay in the queue until approved
- secret tokens are redacted from MCP errors

## Approval Flow

1. A risky MCP tool proposes an action through the Agent Portal runtime.
2. The runtime applies its policy engine and assigns a risk level.
3. Safe actions can auto-execute.
4. Higher-risk actions become `pending_approval`.
5. `approve_action` can approve and execute a queued action.
6. `reject_action` rejects the queued action.

## Example Tool Calls

- `browser_open`
- `navigate_to_url`
- `click_element`
- `capture_screenshot`
- `get_action_queue`
- `generate_report`

## Troubleshooting

- If the runtime is offline, start it with `agent-portal start`.
- If token auth is enabled, set `AGENT_PORTAL_TOKEN`.
- If tools are not visible, run `agent-portal mcp doctor`.
