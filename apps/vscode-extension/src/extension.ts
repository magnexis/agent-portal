import * as net from "node:net";
import * as path from "node:path";
import * as vscode from "vscode";

type ExtensionStatus =
  | "thinking"
  | "waiting-approval"
  | "acting"
  | "paused"
  | "blocked"
  | "finished"
  | "failed"
  | "stopped"
  | "idle";

interface ActionQueueItem {
  action_id: string;
  action_type: string;
  target?: string;
  reason: string;
  risk_level: string;
  status: string;
  created_at: string;
}

interface RuntimeStatusResponse {
  session: {
    runtime_status: string;
    current_goal?: string | null;
    pending_actions: ActionQueueItem[];
  };
  browser: {
    connected: boolean;
    current_url?: string | null;
    page_title?: string | null;
    last_error?: string | null;
  };
}

interface ExtensionState {
  runtimeStatus: ExtensionStatus;
  browserStatus: string;
  currentGoal: string;
  pendingActions: ActionQueueItem[];
  latestReportPath?: string;
  currentUrl?: string;
  pageTitle?: string;
  runtimeUrl: string;
  logs: string[];
  detectedServers: string[];
}

class AgentPortalSidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "agentPortal.sidebar";
  private view?: vscode.WebviewView;

  constructor(
    private readonly context: vscode.ExtensionContext,
    private readonly store: AgentPortalExtensionStore
  ) {}

  resolveWebviewView(webviewView: vscode.WebviewView): void {
    this.view = webviewView;
    webviewView.webview.options = {
      enableScripts: true
    };
    webviewView.webview.onDidReceiveMessage(async (message: { command: string }) => {
      await vscode.commands.executeCommand(message.command);
    });
    this.render();
  }

  render(): void {
    if (!this.view) {
      return;
    }

    const state = this.store.snapshot();
    const webview = this.view.webview;
    this.view.title = "Control Center";
    webview.html = getSidebarHtml(webview, this.context, state);
  }
}

class AgentPortalExtensionStore {
  private terminal?: vscode.Terminal;
  private state: ExtensionState = {
    runtimeStatus: "idle",
    browserStatus: "idle",
    currentGoal: "No active goal",
    pendingActions: [],
    logs: [],
    detectedServers: [],
    runtimeUrl: "http://127.0.0.1:8765"
  };

  snapshot(): ExtensionState {
    return {
      ...this.state,
      pendingActions: [...this.state.pendingActions],
      logs: [...this.state.logs],
      detectedServers: [...this.state.detectedServers]
    };
  }

  update(partial: Partial<ExtensionState>): void {
    this.state = {
      ...this.state,
      ...partial
    };
  }

  log(message: string): void {
    this.state.logs = [message, ...this.state.logs].slice(0, 8);
  }

  setTerminal(terminal?: vscode.Terminal): void {
    this.terminal = terminal;
  }

  getTerminal(): vscode.Terminal | undefined {
    return this.terminal;
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const store = new AgentPortalExtensionStore();
  const sidebar = new AgentPortalSidebarProvider(context, store);

  const refreshSidebar = async (): Promise<void> => {
    const runtimeUrl = getRuntimeUrl();
    const runtimeStatus = await fetchRuntimeStatus(runtimeUrl);
    const detectedServers = await detectLocalDevelopmentServers();

    store.update({
      runtimeUrl,
      detectedServers
    });

    if (runtimeStatus) {
      store.update({
        runtimeStatus: normalizeRuntimeStatus(runtimeStatus.session.runtime_status),
        browserStatus: runtimeStatus.browser.connected ? "connected" : "idle",
        currentGoal: runtimeStatus.session.current_goal ?? "No active goal",
        pendingActions: runtimeStatus.session.pending_actions,
        currentUrl: runtimeStatus.browser.current_url ?? undefined,
        pageTitle: runtimeStatus.browser.page_title ?? undefined
      });
    } else {
      store.update({
        runtimeStatus: "stopped",
        browserStatus: "disconnected",
        pendingActions: []
      });
    }

    sidebar.render();
  };

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      AgentPortalSidebarProvider.viewType,
      sidebar
    ),
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (
        event.affectsConfiguration("agentPortal.runtimeUrl") ||
        event.affectsConfiguration("agentPortal.preferredLocalDevPort")
      ) {
        void refreshSidebar();
      }
    }),
    vscode.commands.registerCommand("agentPortal.startRuntime", async () => {
      const workspaceRoot = getWorkspaceRoot();
      if (!workspaceRoot) {
        void vscode.window.showErrorMessage(
          "Open the Agent Portal workspace before starting the runtime."
        );
        return;
      }

      const runtimeUrl = getRuntimeUrl();
      const { host, port } = parseRuntimeUrl(runtimeUrl);
      const terminal =
        store.getTerminal() ??
        vscode.window.createTerminal({
          name: "Agent Portal Runtime",
          cwd: workspaceRoot
        });
      store.setTerminal(terminal);
      terminal.show();
      terminal.sendText(`python -m agent_portal --host ${host} --port ${port} start`);
      store.log(`Starting runtime on ${runtimeUrl}.`);
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.stopRuntime", async () => {
      const response = await postRuntimeCommand("/control/stop");
      if (!response) {
        void vscode.window.showErrorMessage("Runtime is not available to stop.");
        return;
      }
      store.setTerminal(undefined);
      store.log("Stopped runtime.");
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.restartRuntime", async () => {
      const response = await postRuntimeCommand("/control/restart");
      if (!response) {
        void vscode.window.showErrorMessage("Runtime is not available to restart.");
        return;
      }
      store.log("Restarted runtime.");
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.openCurrentProject", async () => {
      const snapshot = store.snapshot();
      const preferredPort =
        vscode.workspace
          .getConfiguration("agentPortal")
          .get<number>("preferredLocalDevPort", 3000) ?? 3000;
      const preferredServer = snapshot.detectedServers.find((server) =>
        server.endsWith(`:${preferredPort}`)
      );
      const target = preferredServer ?? snapshot.currentUrl ?? snapshot.detectedServers[0];

      if (!target) {
        void vscode.window.showInformationMessage(
          "No local development server or runtime page is available yet."
        );
        return;
      }

      await vscode.env.openExternal(vscode.Uri.parse(target));
      store.log(`Opened ${target}.`);
      sidebar.render();
    }),
    vscode.commands.registerCommand("agentPortal.runAgent", async () => {
      const response = await postRuntimeCommand("/control/resume");
      if (!response) {
        void vscode.window.showErrorMessage("Runtime is not available.");
        return;
      }
      store.log("Resumed agent execution.");
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.pauseAgent", async () => {
      const response = await postRuntimeCommand("/control/pause");
      if (!response) {
        void vscode.window.showErrorMessage("Runtime is not available.");
        return;
      }
      store.log("Paused agent execution.");
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.resumeAgent", async () => {
      const response = await postRuntimeCommand("/control/resume");
      if (!response) {
        void vscode.window.showErrorMessage("Runtime is not available.");
        return;
      }
      store.log("Resumed agent execution.");
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.stopAgent", async () => {
      const response = await postRuntimeCommand("/control/pause");
      if (!response) {
        void vscode.window.showErrorMessage("Runtime is not available.");
        return;
      }
      store.log("Stopped agent execution and left runtime paused.");
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.approveNextAction", async () => {
      const response = await postRuntimeCommand("/control/approve-next");
      if (!response) {
        void vscode.window.showErrorMessage("Runtime is not available.");
        return;
      }
      store.log("Approved next action.");
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.rejectNextAction", async () => {
      const response = await postRuntimeCommand("/control/reject-next", {
        reason: "Rejected from VS Code"
      });
      if (!response) {
        void vscode.window.showErrorMessage("Runtime is not available.");
        return;
      }
      store.log("Rejected next action.");
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.generateReport", async () => {
      const report = await fetchRuntimeReport();
      if (!report?.reportPath) {
        void vscode.window.showInformationMessage(
          "The runtime is not available to generate a report."
        );
        return;
      }

      const document = await vscode.workspace.openTextDocument(report.reportPath);
      await vscode.window.showTextDocument(document);
      store.update({ latestReportPath: report.reportPath });
      store.log(`Opened report ${report.reportPath}.`);
      await refreshSidebar();
    }),
    vscode.commands.registerCommand("agentPortal.openDocumentation", async () => {
      const workspaceRoot = getWorkspaceRoot();
      if (!workspaceRoot) {
        return;
      }

      const quickstart = path.join(workspaceRoot, "QUICKSTART.md");
      const document = await vscode.workspace.openTextDocument(quickstart);
      await vscode.window.showTextDocument(document);
      store.log("Opened quickstart documentation.");
      sidebar.render();
    }),
    vscode.commands.registerCommand("agentPortal.connectRuntime", async () => {
      await refreshSidebar();
      store.log("Connected to runtime status endpoint.");
      sidebar.render();
    })
  );

  const interval = setInterval(() => {
    void refreshSidebar();
  }, 5_000);
  context.subscriptions.push({
    dispose: () => clearInterval(interval)
  });

  void refreshSidebar();
}

export function deactivate(): void {}

function getWorkspaceRoot(): string | undefined {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

function getRuntimeUrl(): string {
  return (
    vscode.workspace
      .getConfiguration("agentPortal")
      .get<string>("runtimeUrl", "http://127.0.0.1:8765") ?? "http://127.0.0.1:8765"
  );
}

function parseRuntimeUrl(runtimeUrl: string): { host: string; port: number } {
  const parsed = new URL(runtimeUrl);
  return {
    host: parsed.hostname,
    port: parsed.port ? Number(parsed.port) : 8765
  };
}

async function fetchRuntimeStatus(
  runtimeUrl: string
): Promise<RuntimeStatusResponse | undefined> {
  return fetchJson<RuntimeStatusResponse>(`${runtimeUrl}/status`);
}

async function fetchRuntimeReport(): Promise<
  { reportPath?: string; report?: unknown } | undefined
> {
  return fetchJson(`${getRuntimeUrl()}/report/latest`);
}

async function postRuntimeCommand(
  pathName: string,
  payload?: Record<string, unknown>
): Promise<unknown | undefined> {
  const runtimeUrl = getRuntimeUrl();
  return fetchJson(`${runtimeUrl}${pathName}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload ?? {})
  });
}

async function fetchJson<T>(
  url: string,
  init?: RequestInit
): Promise<T | undefined> {
  try {
    const response = await fetch(url, {
      ...init,
      signal: AbortSignal.timeout(2_500)
    });
    if (!response.ok) {
      return undefined;
    }
    return (await response.json()) as T;
  } catch {
    return undefined;
  }
}

async function detectLocalDevelopmentServers(): Promise<string[]> {
  const ports = [3000, 5173, 8080, 8000, 5000];
  const checks = await Promise.all(ports.map((port) => isPortOpen(port)));

  return checks
    .filter((entry): entry is { port: number; open: true } => entry.open)
    .map((entry) => `http://localhost:${entry.port}`);
}

async function isPortOpen(
  port: number
): Promise<{ port: number; open: boolean }> {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    const finish = (open: boolean): void => {
      socket.destroy();
      resolve({ port, open });
    };

    socket.setTimeout(250);
    socket.once("connect", () => finish(true));
    socket.once("timeout", () => finish(false));
    socket.once("error", () => finish(false));
    socket.connect(port, "127.0.0.1");
  });
}

function normalizeRuntimeStatus(status: string): ExtensionStatus {
  switch (status) {
    case "thinking":
    case "waiting-approval":
    case "acting":
    case "paused":
    case "blocked":
    case "finished":
    case "failed":
    case "stopped":
      return status;
    default:
      return "idle";
  }
}

function getSidebarHtml(
  webview: vscode.Webview,
  context: vscode.ExtensionContext,
  state: ExtensionState
): string {
  const logoUri = webview.asWebviewUri(
    vscode.Uri.joinPath(context.extensionUri, "media", "agent-portal-logo.png")
  );
  const pendingCards =
    state.pendingActions.length > 0
      ? state.pendingActions
          .map(
            (action) => `
              <article class="card action">
                <div class="label">${action.action_type}</div>
                <strong>${escapeHtml(action.target ?? "No target")}</strong>
                <p>${escapeHtml(action.reason)}</p>
                <span class="badge risk-${action.risk_level}">${action.risk_level}</span>
              </article>
            `
          )
          .join("")
      : `<article class="card empty"><strong>No pending actions</strong><p>The queue is currently clear.</p></article>`;

  const logs = state.logs.map((log) => `<li>${escapeHtml(log)}</li>`).join("");
  const servers = state.detectedServers
    .map((server) => `<li>${escapeHtml(server)}</li>`)
    .join("");

  return `<!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <style>
        body {
          font-family: "Segoe UI", sans-serif;
          padding: 12px;
          color: var(--vscode-foreground);
        }
        .hero {
          display: grid;
          gap: 10px;
          margin-bottom: 16px;
        }
        .hero img {
          width: 100%;
          border-radius: 16px;
        }
        .status-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }
        .card {
          border: 1px solid var(--vscode-panel-border);
          border-radius: 12px;
          padding: 12px;
          background: color-mix(in srgb, var(--vscode-editor-background) 92%, white 8%);
        }
        .action {
          margin-bottom: 10px;
        }
        .label {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          opacity: 0.7;
        }
        .badge {
          display: inline-block;
          margin-top: 8px;
          padding: 4px 8px;
          border-radius: 999px;
          font-size: 11px;
          text-transform: uppercase;
        }
        .risk-safe, .risk-low {
          background: rgba(60, 200, 140, 0.2);
        }
        .risk-medium {
          background: rgba(255, 194, 64, 0.24);
        }
        .risk-high, .risk-blocked {
          background: rgba(255, 90, 90, 0.24);
        }
        .controls {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        button {
          border: 0;
          border-radius: 10px;
          padding: 10px;
          color: white;
          cursor: pointer;
          background: linear-gradient(90deg, #179cff, #ff9b21);
        }
        ul {
          margin: 8px 0 0;
          padding-left: 18px;
        }
      </style>
    </head>
    <body>
      <section class="hero">
        <img src="${logoUri}" alt="Agent Portal" />
        <div class="card">
          <div class="label">Current Goal</div>
          <strong>${escapeHtml(state.currentGoal)}</strong>
          <p>${escapeHtml(state.runtimeUrl)}</p>
        </div>
      </section>
      <section class="status-row">
        <div class="card">
          <div class="label">Runtime</div>
          <strong>${escapeHtml(state.runtimeStatus)}</strong>
        </div>
        <div class="card">
          <div class="label">Browser</div>
          <strong>${escapeHtml(state.browserStatus)}</strong>
        </div>
      </section>
      <section class="card">
        <div class="label">Current Page</div>
        <strong>${escapeHtml(state.pageTitle ?? "No page open")}</strong>
        <p>${escapeHtml(state.currentUrl ?? "No active browser session")}</p>
      </section>
      <section class="card">
        <div class="label">Pending Action Queue</div>
        ${pendingCards}
      </section>
      <section class="controls">
        <button onclick="post('agentPortal.startRuntime')">Start Runtime</button>
        <button onclick="post('agentPortal.connectRuntime')">Connect Runtime</button>
        <button onclick="post('agentPortal.pauseAgent')">Pause Agent</button>
        <button onclick="post('agentPortal.resumeAgent')">Resume Agent</button>
        <button onclick="post('agentPortal.approveNextAction')">Approve Next</button>
        <button onclick="post('agentPortal.rejectNextAction')">Reject Next</button>
        <button onclick="post('agentPortal.generateReport')">Open Report</button>
        <button onclick="post('agentPortal.restartRuntime')">Restart Runtime</button>
      </section>
      <section class="card">
        <div class="label">Detected Local Servers</div>
        <ul>${servers || "<li>None detected</li>"}</ul>
      </section>
      <section class="card">
        <div class="label">Recent Logs</div>
        <ul>${logs || "<li>No recent extension activity</li>"}</ul>
      </section>
      <script>
        const vscode = acquireVsCodeApi();
        function post(command) {
          vscode.postMessage({ command });
        }
      </script>
    </body>
  </html>`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
