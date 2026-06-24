# Testing

Run the full test sweep with:

```bash
npm test
```

That command currently runs:

- Python unit tests in `python/tests`
- TypeScript builds across the workspace
- Node tests in `tests/*.test.mjs`

## Focus Areas

Current automated coverage includes:

- runtime action queue behavior
- blocked action policy
- report generation
- runtime HTTP status endpoint
- plugin manifest validation
- TypeScript workspace build verification
- VS Code extension build verification through workspace build

## Recommended Manual Verification

```bash
agent-portal doctor
agent-portal start
agent-portal open http://localhost:3000
agent-portal screenshot --label smoke-test
agent-portal report
```
