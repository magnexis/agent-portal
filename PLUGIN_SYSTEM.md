# Plugin System

Agent Portal supports a manifest-driven plugin model.

## Manifest Fields

- `name`
- `version`
- `type`
- `permissions`
- `entryPoint`
- `commands`
- `settings`
- `panels`
- `lifecycleHooks`

## Included Plugin Manifests

- `plugins/agent-portal-vscode/plugin.json`
- `plugins/agent-portal-browser/plugin.json`
- `plugins/agent-portal-python/plugin.json`
- `plugins/agent-portal-skills/plugin.json`

## Connector Scaffolds

- `connectors/chatgpt-tools`
- `connectors/claude-mcp-server`
- `connectors/gemini-connector`
- `connectors/rest-websocket-api`

## Validation

The core runtime exports `validatePluginManifest()` for manifest checks.
