# Quickstart

1. Run `npm install`
2. Run `npx playwright install chromium`
3. Run `pip install -e ./python`
4. Run `agent-portal doctor`
5. Start the runtime with `agent-portal start`
6. Use `agent-portal open http://localhost:3000` or start the desktop demo with `npm run dev`
7. Run `agent-portal screenshot --label smoke-test`
8. Run `agent-portal report`
9. Open the VS Code extension sidebar and use `Agent Portal: Connect To Running Runtime`

## What You Should See

- a local browser workflow opens
- the agent types, clicks, scrolls, and captures evidence
- a session report is generated
- action queue, graph, and memory artifacts are persisted
- the VS Code extension reads live runtime status from the Python runtime
