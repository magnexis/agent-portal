import { readFile } from "node:fs/promises";
import path from "node:path";
import {
  ActionQueueItem,
  AgentDefinition,
  BrowserExecuteResult,
  BrowserInspectionResult,
  BrowserElementText,
  ConsoleLogEntry,
  GoalDefinition,
  GoalPlan,
  GoalPlanner,
  MemoryRecord,
  NetworkEvent,
  PortalGraph,
  PortalGraphNode,
  ProjectAwareness,
  RuntimeStatus,
  ScreenUnderstanding,
  ScrollOptions,
  SteeringState,
  VisionCore,
  VisualSnapshot,
  WorkspaceDefinition,
  createDefaultWorkspace
} from "@agent-portal/core";

export interface PortalOptions {
  runtimeUrl?: string;
  apiToken?: string;
  workspaceName?: string;
  workspace?: WorkspaceDefinition;
  workspaceBasePath?: string;
}

interface RuntimeStatusResponse {
  session: {
    runtime_status: RuntimeStatus | string;
    current_goal?: string | null;
    pending_actions: Array<{
      action_id: string;
      action_type: string;
      target?: string;
      payload?: string;
      reason: string;
      risk_level: string;
      created_at: string;
      status: string;
      result?: string | null;
      before_screenshot?: string | null;
      after_screenshot?: string | null;
    }>;
  };
  browser: {
    connected: boolean;
    current_url?: string | null;
    page_title?: string | null;
    last_error?: string | null;
  };
  policy?: {
    mode?: string;
    approval_threshold?: string;
    domain_lock?: string | null;
    tab_lock?: string | null;
    read_only?: boolean;
  };
}

interface RuntimeCaptureResponse {
  action?: {
    after_screenshot?: string | null;
  };
  inspection: {
    url?: string | null;
    title?: string | null;
    dom?: string;
    consoleErrors?: string[];
    networkErrors?: string[];
  };
  screenshotPath?: string | null;
}

export class Portal {
  private readonly runtimeUrl: string;
  private readonly apiToken?: string;
  private readonly workspace: WorkspaceDefinition;
  private readonly workspaceBasePath: string;
  private readonly vision = new VisionCore();
  private readonly planner = new GoalPlanner();
  private readonly graphBuilder = new PortalGraph();
  private readonly graphNodes: PortalGraphNode[] = [];
  private readonly memoryRecords: MemoryRecord[] = [];
  private readonly agents = new Map<string, AgentDefinition>();

  constructor(options: PortalOptions = {}) {
    this.runtimeUrl = options.runtimeUrl ?? "http://127.0.0.1:8765";
    this.apiToken = options.apiToken;
    this.workspace =
      options.workspace ?? createDefaultWorkspace(options.workspaceName ?? "default");
    this.workspaceBasePath = options.workspaceBasePath ?? process.cwd();
  }

  launch(): string {
    return `Portal client ready for ${this.runtimeUrl}`;
  }

  async startRuntime(): Promise<RuntimeStatusResponse> {
    return this.post("/control/start");
  }

  async stopRuntime(): Promise<unknown> {
    return this.post("/control/stop");
  }

  async restartRuntime(): Promise<RuntimeStatusResponse> {
    return this.post("/control/restart");
  }

  async startBrowser(): Promise<RuntimeStatusResponse> {
    return this.post("/browser/start");
  }

  async open(target: string): Promise<string> {
    await this.post("/browser/open", { url: target });
    return `open on ${target}`;
  }

  async click(target: string, reason = "Click element"): Promise<string> {
    await this.post("/browser/click", { selector: target, reason });
    return `click on ${target}`;
  }

  async type(target: string, payload: string, reason = "Type into element"): Promise<string> {
    await this.post("/browser/type", { selector: target, value: payload, reason });
    return `type on ${target}`;
  }

  async hover(target: string, reason = "Hover over element"): Promise<string> {
    await this.post("/browser/hover", { selector: target, reason });
    return `hover on ${target}`;
  }

  async scroll(options: ScrollOptions = {}): Promise<string> {
    await this.post("/browser/scroll", {
      selector: options.selector,
      reason: options.selector ? "Scroll target into view" : "Scroll page",
      deltaX: options.deltaX,
      deltaY: options.deltaY
    });
    return `scroll${options.selector ? ` on ${options.selector}` : ""}`;
  }

  async waitFor(target: string, timeoutMs?: number): Promise<string> {
    await this.post("/browser/wait", {
      selector: target,
      reason: timeoutMs
        ? `Wait for element within ${timeoutMs}ms`
        : "Wait for element"
    });
    return `wait on ${target}`;
  }

  async execute(script: string): Promise<BrowserExecuteResult> {
    const response = await this.post<{ result: unknown }>("/browser/execute", { script });
    return {
      result: response.result
    };
  }

  async capture(label = "capture"): Promise<BrowserInspectionResult> {
    const response = await this.post<RuntimeCaptureResponse>("/browser/capture", { label });
    return this.buildInspectionResult(response.inspection, response.screenshotPath ?? undefined, label);
  }

  async inspect(target = "inspect"): Promise<BrowserInspectionResult> {
    const response = await this.post<RuntimeCaptureResponse>("/browser/capture", { label: target });
    return this.buildInspectionResult(response.inspection, response.screenshotPath ?? undefined, target);
  }

  async close(): Promise<void> {
    await this.stopRuntime().catch(() => undefined);
  }

  async readText(target: string): Promise<BrowserElementText> {
    const response = await this.post<{ text: string | null; selector: string }>(
      "/browser/read-text",
      { selector: target }
    );
    return {
      selector: response.selector,
      text: response.text
    };
  }

  async writeReport(): Promise<string> {
    const response = await this.post<{ reportPath: string }>("/report/generate");
    return response.reportPath;
  }

  async status(): Promise<RuntimeStatusResponse> {
    return this.get("/status");
  }

  async health(): Promise<Record<string, unknown>> {
    return this.get("/health");
  }

  understand(result: BrowserInspectionResult, goal?: string): ScreenUnderstanding {
    return this.vision.analyze({
      snapshot: result.snapshot,
      goal
    });
  }

  planGoal(goal: GoalDefinition, understanding?: ScreenUnderstanding): GoalPlan {
    return this.planner.createPlan(goal, understanding);
  }

  async remember(record: MemoryRecord): Promise<string> {
    this.memoryRecords.push(record);
    return path.join(this.workspaceBasePath, this.workspace.directories.memory, `${record.id}.json`);
  }

  mapCurrentPage(result: BrowserInspectionResult, understanding: ScreenUnderstanding): void {
    const next = this.graphBuilder.fromSnapshot(result.snapshot, understanding);
    const index = this.graphNodes.findIndex((entry) => entry.id === next.id);
    if (index >= 0) {
      this.graphNodes[index] = next;
      return;
    }
    this.graphNodes.push(next);
  }

  async detectProjectAwareness(): Promise<ProjectAwareness> {
    const packageJsonPath = path.resolve(this.workspaceBasePath, "package.json");
    const frameworks = new Set<string>();
    const services = new Set<string>();
    const packageManagers = new Set<string>();

    try {
      const raw = await readFile(packageJsonPath, "utf8");
      const pkg = JSON.parse(raw) as {
        dependencies?: Record<string, string>;
        devDependencies?: Record<string, string>;
        packageManager?: string;
      };
      const names = Object.keys({
        ...(pkg.dependencies ?? {}),
        ...(pkg.devDependencies ?? {})
      });

      if (names.includes("next")) frameworks.add("Next.js");
      if (names.includes("react")) frameworks.add("React");
      if (names.includes("vue")) frameworks.add("Vue");
      if (names.includes("angular")) frameworks.add("Angular");
      if (names.includes("express")) frameworks.add("Express");
      if (names.includes("fastapi")) frameworks.add("FastAPI");
      if (names.includes("@supabase/supabase-js")) services.add("Supabase");
      if (names.includes("stripe")) services.add("Stripe");
      if (pkg.packageManager) packageManagers.add(pkg.packageManager.split("@")[0]);
    } catch {
      return {
        frameworks: [],
        services: [],
        packageManagers: [],
        summary: "Project awareness could not be derived from package.json."
      };
    }

    return {
      frameworks: [...frameworks],
      services: [...services],
      packageManagers: [...packageManagers],
      summary: `Detected ${[...frameworks, ...services].join(", ") || "no known frameworks or services"}.`
    };
  }

  startAgent(agentId: string): AgentDefinition {
    return this.updateAgent(agentId, "running");
  }

  blockAgent(agentId: string): AgentDefinition {
    return this.updateAgent(agentId, "blocked");
  }

  completeAgent(agentId: string): AgentDefinition {
    return this.updateAgent(agentId, "completed");
  }

  resetAgent(agentId: string): AgentDefinition {
    return this.updateAgent(agentId, "idle");
  }

  async pause(): Promise<void> {
    await this.post("/control/pause");
  }

  async resume(): Promise<void> {
    await this.post("/control/resume");
  }

  async stop(): Promise<void> {
    await this.post("/control/stop");
  }

  clearStop(): void {
    return;
  }

  enableStepByStep(): void {
    return;
  }

  disableStepByStep(): void {
    return;
  }

  async redirectGoal(goal: string): Promise<void> {
    await this.post("/control/goal", { goal });
  }

  async lockToDomain(domain: string): Promise<void> {
    await this.post("/control/domain-lock", { domain });
  }

  async unlockDomain(): Promise<void> {
    await this.post("/control/domain-lock", { domain: null });
  }

  async lockToTab(url: string): Promise<void> {
    await this.post("/control/tab-lock", { url });
  }

  async unlockTab(): Promise<void> {
    await this.post("/control/tab-lock", { url: null });
  }

  async approveNextAction(): Promise<ActionQueueItem | undefined> {
    const result = await this.post<Record<string, unknown>>("/control/approve-next");
    return this.normalizeQueueItem(result);
  }

  async rejectNextAction(reason?: string): Promise<ActionQueueItem | undefined> {
    const result = await this.post<Record<string, unknown>>("/control/reject-next", {
      reason
    });
    return this.normalizeQueueItem(result);
  }

  editNextAction(): ActionQueueItem | undefined {
    return undefined;
  }

  async pendingActions(): Promise<ActionQueueItem[]> {
    const status = await this.status();
    return status.session.pending_actions.map((action) => this.mapRuntimeAction(action));
  }

  async steering(): Promise<SteeringState> {
    const status = await this.status();
    return {
      paused: status.session.runtime_status === "paused",
      stopped: status.session.runtime_status === "stopped",
      stepByStepMode: false,
      currentGoal: status.session.current_goal ?? undefined,
      lockedDomain: status.policy?.domain_lock ?? undefined,
      lockedTabUrl: status.policy?.tab_lock ?? undefined,
      requireApprovalAtOrAbove:
        (status.policy?.approval_threshold as SteeringState["requireApprovalAtOrAbove"]) ?? "medium"
    };
  }

  async runtimeStatus(): Promise<RuntimeStatus> {
    const status = await this.status();
    return this.normalizeRuntimeStatus(status.session.runtime_status);
  }

  async report(): Promise<{
    runtimeStatus: RuntimeStatus;
    browserConnected: boolean;
    currentUrl?: string;
    pendingActions: ActionQueueItem[];
  }> {
    const status = await this.status();
    return {
      runtimeStatus: this.normalizeRuntimeStatus(status.session.runtime_status),
      browserConnected: status.browser.connected,
      currentUrl: status.browser.current_url ?? undefined,
      pendingActions: status.session.pending_actions.map((action) => this.mapRuntimeAction(action))
    };
  }

  private async get<T>(route: string): Promise<T> {
    return this.request<T>(route, {
      method: "GET"
    });
  }

  private async post<T>(route: string, payload?: Record<string, unknown>): Promise<T> {
    return this.request<T>(route, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload ?? {})
    });
  }

  private async request<T>(route: string, init: RequestInit): Promise<T> {
    const headers = new Headers(init.headers);
    if (this.apiToken) {
      headers.set("Authorization", `Bearer ${this.apiToken}`);
    }

    const response = await fetch(`${this.runtimeUrl}${route}`, {
      ...init,
      headers,
      signal: AbortSignal.timeout(5_000)
    });

    if (!response.ok) {
      let message = `${response.status} ${response.statusText}`;
      try {
        const errorBody = (await response.json()) as { message?: string; error?: string };
        message = errorBody.message ?? errorBody.error ?? message;
      } catch {
        // Keep default message when the response body is not JSON.
      }
      throw new Error(`Agent Portal runtime request failed: ${message}`);
    }

    return (await response.json()) as T;
  }

  private buildInspectionResult(
    inspection: RuntimeCaptureResponse["inspection"],
    screenshotPath: string | undefined,
    label: string
  ): BrowserInspectionResult {
    const consoleLogs = (inspection.consoleErrors ?? []).map<ConsoleLogEntry>((text) => ({
      type: "error",
      text,
      at: new Date().toISOString()
    }));
    const networkEvents = (inspection.networkErrors ?? []).map<NetworkEvent>((text) => ({
      url: text,
      method: "GET",
      resourceType: "unknown",
      outcome: "failed",
      failureText: text,
      at: new Date().toISOString()
    }));
    const snapshot: VisualSnapshot = {
      id: `${Date.now()}-${label}`,
      source: "browser",
      capturedAt: new Date().toISOString(),
      screenshotPath,
      dom: inspection.dom ?? "",
      consoleLogs,
      networkEvents,
      label,
      url: inspection.url ?? undefined,
      detectedElements: []
    };

    return {
      url: inspection.url ?? "",
      title: inspection.title ?? "",
      dom: inspection.dom ?? "",
      screenshotPath: screenshotPath ?? "",
      consoleLogs,
      networkEvents,
      snapshot
    };
  }

  private updateAgent(
    agentId: string,
    status: AgentDefinition["status"]
  ): AgentDefinition {
    const current =
      this.agents.get(agentId) ?? {
        id: agentId,
        role: "custom",
        status: "idle"
      };
    const next = {
      ...current,
      status
    };
    this.agents.set(agentId, next);
    return next;
  }

  private mapRuntimeAction(action: RuntimeStatusResponse["session"]["pending_actions"][number]): ActionQueueItem {
    return {
      id: action.action_id,
      actionType: action.action_type as ActionQueueItem["actionType"],
      target: action.target,
      payload: action.payload,
      reason: action.reason,
      riskLevel: action.risk_level as ActionQueueItem["riskLevel"],
      timestamp: action.created_at,
      status: action.status as ActionQueueItem["status"],
      result: action.result ?? undefined,
      requiresApproval: action.status === "pending"
    };
  }

  private normalizeQueueItem(value: Record<string, unknown>): ActionQueueItem | undefined {
    if (typeof value.action_id !== "string" || typeof value.action_type !== "string") {
      return undefined;
    }

    return {
      id: value.action_id,
      actionType: value.action_type as ActionQueueItem["actionType"],
      target: typeof value.target === "string" ? value.target : undefined,
      payload: typeof value.payload === "string" ? value.payload : undefined,
      reason: typeof value.reason === "string" ? value.reason : "Runtime action",
      riskLevel: (typeof value.risk_level === "string" ? value.risk_level : "low") as ActionQueueItem["riskLevel"],
      timestamp: typeof value.created_at === "string" ? value.created_at : new Date().toISOString(),
      status: (typeof value.status === "string" ? value.status : "pending") as ActionQueueItem["status"],
      result: typeof value.result === "string" ? value.result : undefined,
      requiresApproval: value.status === "pending"
    };
  }

  private normalizeRuntimeStatus(status: string): RuntimeStatus {
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
}
