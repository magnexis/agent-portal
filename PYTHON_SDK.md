# Python Runtime And SDK

The Python runtime package lives in `python/agent_portal`.

## Current Status

- package metadata is in `python/pyproject.toml`
- runtime models are in `python/agent_portal/models.py`
- runtime controller is in `python/agent_portal/runtime.py`
- HTTP runtime server is in `python/agent_portal/server.py`
- doctor checks are in `python/agent_portal/doctor.py`
- CLI commands are in `python/agent_portal/cli.py`

## Direction

This package currently owns:

- the local runtime
- Playwright session ownership
- browser automation and steering state
- HTTP transport
- report retrieval and connector access
