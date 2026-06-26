# Installation

## Requirements

- Node.js 20+
- npm 10+
- Python 3.10+
- Playwright browser binaries installed with `npx playwright install chromium`

## Setup

1. Install dependencies:

```bash
npm install
```

2. Install Playwright Chromium:

```bash
npx playwright install chromium
```

3. Install the Python runtime package:

```bash
pip install -e ./python
```

4. Build the workspace:

```bash
npm run build
```

## VS Code Extension

The VS Code extension is included in `apps/vscode-extension`.

Build it with:

```bash
npm run build --workspace @agent-portal/vscode-extension
```

## Python Runtime

Run a health check first:

```bash
agent-portal doctor
```

Start the runtime server with:

```bash
agent-portal start
```
