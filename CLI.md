# CLI

The Python package installs the `agent-portal` command.

## Commands

```bash
agent-portal start
agent-portal stop
agent-portal status
agent-portal doctor
agent-portal open http://localhost:3000
agent-portal screenshot --label homepage
agent-portal report
agent-portal plugins list
agent-portal plugins validate
```

## Global Options

```bash
agent-portal --json --host 127.0.0.1 --port 8765 status
```

Supported options:

- `--json` for machine-readable output
- `--host` to override the runtime host
- `--port` to override the runtime port
- `--verbose`
- `--debug`
- `--profile`

## Notes

- `start` writes a default `agent-portal.config.json` if one does not exist.
- runtime-facing commands call the local HTTP runtime.
- if the runtime is unavailable, the CLI returns a helpful error with a suggested start command.
