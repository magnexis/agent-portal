# VS Code Extension

The VS Code extension lives in `apps/vscode-extension`.

## Features

- sidebar control center
- runtime start and stop commands
- restart runtime command
- connect directly to the Python runtime HTTP server
- pending action queue preview
- approve and reject controls
- local development server detection for:
  - `localhost:3000`
  - `localhost:5173`
  - `localhost:8080`
  - `localhost:8000`
  - `localhost:5000`

## Primary Commands

- `Agent Portal: Start Runtime`
- `Agent Portal: Stop Runtime`
- `Agent Portal: Restart Runtime`
- `Agent Portal: Open Current Project`
- `Agent Portal: Run Agent`
- `Agent Portal: Pause Agent`
- `Agent Portal: Resume Agent`
- `Agent Portal: Stop Agent`
- `Agent Portal: Approve Next Action`
- `Agent Portal: Reject Next Action`
- `Agent Portal: Generate Report`
- `Agent Portal: Open Documentation`

## Runtime Relationship

The extension is the developer-facing control panel.
The Python `agent_portal` package owns the local runtime, Playwright session, and API surfaces.

## Settings

- `agentPortal.runtimeUrl`
- `agentPortal.preferredLocalDevPort`
