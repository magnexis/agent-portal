# Runtime

The local runtime lives in `python/agent_portal`.

## Responsibilities

- own the local browser process
- enforce agent steering and risk policy
- expose runtime control endpoints
- generate session reports
- validate plugin manifests

## Startup

```bash
agent-portal doctor
agent-portal start
```

By default the runtime binds to `127.0.0.1:8765`.

## Safety Defaults

- localhost-only binding by default
- optional bearer token support through `api_token`
- blocked password typing
- blocked billing and payment actions
- destructive actions escalated to high risk
- screenshot capture disabled for sensitive flows unless enabled

## Reports

Generated reports include:

- project name
- session id
- current url
- goals
- approved, rejected, blocked, completed, and failed actions
- console and network errors
- screenshots
- reproduction steps

Reports are written to the configured report directory.
