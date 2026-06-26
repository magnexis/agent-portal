# Troubleshooting

## Playwright Browser Missing

Run:

```bash
npx playwright install chromium
python -m playwright install chromium
```

## Runtime Does Not Start

- verify `npm install` completed
- run `agent-portal doctor`
- run `npm run check`
- inspect the runtime report directory from `agent-portal.config.json`

## No VS Code Sidebar Data

- open the Agent Portal repo as the current workspace
- make sure `agent-portal start` is running
- confirm `agentPortal.runtimeUrl` matches the local runtime
- use `Agent Portal: Connect To Running Runtime`

## Action Was Blocked

- inspect the queue in the session report
- review domain lock, tab lock, and approval thresholds
- edit or redirect the action before retrying
