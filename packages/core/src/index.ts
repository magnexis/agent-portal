import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium, Locator, Page } from "playwright";

export type AgentRole =
  | "frontend"
  | "backend"
  | "qa"
  | "security"
  | "research"
  | "custom";

export type AgentStatus = "idle" | "running" | "blocked" | "completed";
export type RuntimeStatus =
  | "idle"
  | "thinking"
  | "acting"
  | "waiting-approval"
  | "paused"
  | "blocked"
  | "finished"
  | "failed"
  | "stopped";
export type BrowserSessionStatus =
  | "idle"
  | "launching"
  | "ready"
  | "disconnected"
  | "closing"
  | "closed"
  | "error";
export type ActionRiskLevel = "safe" | "low" | "medium" | "high" | "blocked";
export type ActionQueueStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "completed"
  | "failed"
  | "blocked";

export interface AgentDefinition {
  id: string;
  role: AgentRole;
  status: AgentStatus;
  description?: string;
}

export interface WorkspaceDirectories {
  browserSessions: string;
  documents: string;
  reports: string;
  screenshots: string;
  logs: string;
  agents: string;
  tasks: string;
  workflows: string;
  memory: string;
  settings: string;
}

export interface WorkspaceDefinition {
  id: string;
  name: string;
  rootPath: string;
  directories: WorkspaceDirectories;
}

export type UIElementType =
  | "button"
  | "form"
  | "input"
  | "dropdown"
  | "modal"
  | "menu"
  | "table"
  | "tab"
  | "card"
  | "dialog"
  | "link"
  | "custom";

export interface UIElement {
  id: string;
  type: UIElementType;
  label?: string;
  selector?: string;
  bounds?: { x: number; y: number; width: number; height: number };
  actionable: boolean;
}

export interface ConsoleLogEntry {
  type: "log" | "warning" | "error" | "info";
  text: string;
  location?: string;
  at: string;
}

export interface NetworkEvent {
  url: string;
  status?: number;
  method: string;
  resourceType: string;
  outcome: "pending" | "ok" | "failed";
  failureText?: string;
  at: string;
}

export interface VisualSnapshot {
  id: string;
  source: "browser" | "desktop" | "application";
  capturedAt: string;
  screenshotPath?: string;
  dom?: string;
  accessibilityTree?: string;
  ocrText?: string;
  consoleLogs?: ConsoleLogEntry[];
  networkEvents?: NetworkEvent[];
  label?: string;
  url?: string;
  detectedElements: UIElement[];
}

export interface BrowserAction {
  kind:
    | "open"
    | "click"
    | "type"
    | "scroll"
    | "hover"
    | "drag"
    | "drop"
    | "upload"
    | "download"
    | "capture"
    | "inspect"
    | "wait"
    | "execute";
  target?: string;
  payload?: string;
  timeoutMs?: number;
}

export interface ScrollOptions {
  selector?: string;
  deltaX?: number;
  deltaY?: number;
}

export interface SessionEvent {
  type: string;
  at: string;
  detail: string;
  artifactPath?: string;
}

export interface RootCauseHypothesis {
  label: string;
  confidence: number;
  evidence: string[];
}

export interface ScreenUnderstanding {
  pageCategory:
    | "login"
    | "signup"
    | "dashboard"
    | "docs"
    | "pricing"
    | "form"
    | "unknown";
  summary: string;
  userIntent?: string;
  issues: string[];
  likelyNextActions: string[];
  rootCauseHypotheses: RootCauseHypothesis[];
}

export interface PortalGraphNode {
  id: string;
  label: string;
  pageCategory: ScreenUnderstanding["pageCategory"];
  url?: string;
  links: string[];
}

export interface MemoryRecord {
  id: string;
  kind: "page-understanding" | "goal-plan" | "issue" | "project-awareness";
  summary: string;
  createdAt: string;
  payload: Record<string, unknown>;
}

export interface PluginManifest {
  name: string;
  version: string;
  type:
    | "vscode-extension"
    | "browser-extension"
    | "python-plugin"
    | "agent-connector"
    | "skill-plugin";
  permissions: string[];
  entryPoint?: string;
  commands: string[];
  settings?: Record<string, unknown>;
  panels?: string[];
  lifecycleHooks?: string[];
}

export interface ActionPolicyDecision {
  riskLevel: ActionRiskLevel;
  requiresApproval: boolean;
  blockedReason?: string;
  matchedPolicies: string[];
}

export interface ActionContext {
  reason: string;
  currentUrl?: string;
  candidateLabel?: string;
  targetFieldType?: string;
}

export interface ActionQueueItem {
  id: string;
  actionType: BrowserAction["kind"];
  target?: string;
  payload?: string;
  reason: string;
  riskLevel: ActionRiskLevel;
  timestamp: string;
  status: ActionQueueStatus;
  result?: string;
  errorMessage?: string;
  requiresApproval: boolean;
  beforeScreenshotPath?: string;
  afterScreenshotPath?: string;
  blockedReason?: string;
}

export interface SteeringState {
  paused: boolean;
  stopped: boolean;
  stepByStepMode: boolean;
  currentGoal?: string;
  lockedDomain?: string;
  lockedTabUrl?: string;
  requireApprovalAtOrAbove: ActionRiskLevel;
}

export interface SessionSummary {
  currentGoal?: string;
  actionsAttempted: number;
  approvedActions: number;
  rejectedActions: number;
  failedActions: number;
  blockedActions: number;
  consoleErrors: number;
  networkErrors: number;
  riskEvents: number;
  suggestedFixes: string[];
  reproductionSteps: string[];
}

export interface SessionReport {
  summary: SessionSummary;
  state: RuntimeState;
}

export interface RuntimeState {
  workspace: WorkspaceDefinition;
  agents: AgentDefinition[];
  runtimeStatus: RuntimeStatus;
  browserStatus: BrowserSessionStatus;
  steering: SteeringState;
  sessionEvents: SessionEvent[];
  snapshots: VisualSnapshot[];
  graph: PortalGraphNode[];
  memoryRecords: MemoryRecord[];
  actionQueue: ActionQueueItem[];
}

export interface RuntimeConfig {
  workspace: WorkspaceDefinition;
  agents?: AgentDefinition[];
  workspaceBasePath?: string;
}

export interface CaptureOptions {
  label?: string;
  includeAccessibilityTree?: boolean;
}

export interface BrowserSessionOptions {
  headless?: boolean;
  viewport?: {
    width: number;
    height: number;
  };
  basePath?: string;
  evidenceScreenshots?: boolean;
}

export interface BrowserInspectionResult {
  url: string;
  title: string;
  dom: string;
  accessibilityTree?: string;
  screenshotPath: string;
  consoleLogs: ConsoleLogEntry[];
  networkEvents: NetworkEvent[];
  snapshot: VisualSnapshot;
}

export interface BrowserElementText {
  selector: string;
  text: string | null;
}

export interface BrowserExecuteResult {
  result: unknown;
}

export interface VisionContext {
  snapshot: VisualSnapshot;
  goal?: string;
}

export interface GoalDefinition {
  id: string;
  title: string;
  description?: string;
}

export interface GoalPlanStep {
  id: string;
  title: string;
  detail: string;
  status: "pending" | "ready" | "blocked";
}

export interface GoalPlan {
  goal: GoalDefinition;
  steps: GoalPlanStep[];
}

export interface ProjectAwareness {
  frameworks: string[];
  services: string[];
  packageManagers: string[];
  summary: string;
}

interface SerializedUIElement {
  id: string;
  type: UIElementType;
  label?: string;
  selector?: string;
  bounds?: { x: number; y: number; width: number; height: number };
  actionable: boolean;
}

export class AgentPortalError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly details?: string
  ) {
    super(message);
    this.name = "AgentPortalError";
  }
}

export class ActionApprovalRequiredError extends AgentPortalError {
  constructor(public readonly actionId: string, message: string) {
    super("ACTION_APPROVAL_REQUIRED", message);
    this.name = "ActionApprovalRequiredError";
  }
}

export class ActionBlockedError extends AgentPortalError {
  constructor(public readonly actionId: string, message: string) {
    super("ACTION_BLOCKED", message);
    this.name = "ActionBlockedError";
  }
}

export class AgentPortalRuntime {
  private readonly state: RuntimeState;
  private readonly workspaceBasePath: string;

  constructor(config: RuntimeConfig) {
    this.state = {
      workspace: config.workspace,
      agents: config.agents ?? [],
      runtimeStatus: "idle",
      browserStatus: "idle",
      steering: {
        paused: false,
        stopped: false,
        stepByStepMode: false,
        requireApprovalAtOrAbove: "high"
      },
      sessionEvents: [],
      snapshots: [],
      graph: [],
      memoryRecords: [],
      actionQueue: []
    };
    this.workspaceBasePath = config.workspaceBasePath ?? process.cwd();
  }

  addAgent(agent: AgentDefinition): void {
    this.state.agents.push(agent);
    this.record({
      type: "agent.added",
      at: new Date().toISOString(),
      detail: `Added agent ${agent.id}`
    });
  }

  startAgent(agentId: string): AgentDefinition {
    return this.updateAgentStatus(agentId, "running", "agent.started");
  }

  blockAgent(agentId: string): AgentDefinition {
    return this.updateAgentStatus(agentId, "blocked", "agent.blocked");
  }

  completeAgent(agentId: string): AgentDefinition {
    return this.updateAgentStatus(agentId, "completed", "agent.completed");
  }

  resetAgent(agentId: string): AgentDefinition {
    return this.updateAgentStatus(agentId, "idle", "agent.reset");
  }

  pauseAgentExecution(): void {
    this.state.steering.paused = true;
    this.setRuntimeStatus("paused");
    this.recordStatusEvent("steering.paused", "Agent execution paused");
  }

  resumeAgentExecution(): void {
    this.state.steering.paused = false;
    if (this.state.runtimeStatus === "paused") {
      this.setRuntimeStatus("idle");
    }
    this.recordStatusEvent("steering.resumed", "Agent execution resumed");
  }

  stopAgentExecution(): void {
    this.state.steering.stopped = true;
    this.setRuntimeStatus("stopped");
    this.recordStatusEvent("steering.stopped", "Agent execution stopped");
  }

  clearStoppedState(): void {
    this.state.steering.stopped = false;
    if (this.state.runtimeStatus === "stopped") {
      this.setRuntimeStatus("idle");
    }
    this.recordStatusEvent("steering.stop-cleared", "Stopped state cleared");
  }

  enableStepByStepMode(): void {
    this.state.steering.stepByStepMode = true;
    this.recordStatusEvent("steering.step-by-step.enabled", "Step-by-step mode enabled");
  }

  disableStepByStepMode(): void {
    this.state.steering.stepByStepMode = false;
    this.recordStatusEvent("steering.step-by-step.disabled", "Step-by-step mode disabled");
  }

  redirectGoal(goal: string): void {
    this.state.steering.currentGoal = goal;
    this.recordStatusEvent("steering.goal.redirected", `Redirected goal to ${goal}`);
  }

  lockToDomain(domain: string): void {
    this.state.steering.lockedDomain = domain;
    this.recordStatusEvent("steering.domain.locked", `Locked agent to domain ${domain}`);
  }

  unlockDomain(): void {
    this.state.steering.lockedDomain = undefined;
    this.recordStatusEvent("steering.domain.unlocked", "Removed domain lock");
  }

  lockToTab(url: string): void {
    this.state.steering.lockedTabUrl = url;
    this.recordStatusEvent("steering.tab.locked", `Locked agent to tab ${url}`);
  }

  unlockTab(): void {
    this.state.steering.lockedTabUrl = undefined;
    this.recordStatusEvent("steering.tab.unlocked", "Removed tab lock");
  }

  setApprovalThreshold(level: ActionRiskLevel): void {
    this.state.steering.requireApprovalAtOrAbove = level;
    this.recordStatusEvent(
      "steering.threshold.updated",
      `Approval threshold set to ${level}`
    );
  }

  setBrowserStatus(status: BrowserSessionStatus): void {
    this.state.browserStatus = status;
    this.record({
      type: "browser.status.updated",
      at: new Date().toISOString(),
      detail: `Browser status is now ${status}`
    });
  }

  setRuntimeStatus(status: RuntimeStatus): void {
    this.state.runtimeStatus = status;
  }

  record(event: SessionEvent): void {
    this.state.sessionEvents.push(event);
  }

  addSnapshot(snapshot: VisualSnapshot): void {
    this.state.snapshots.push(snapshot);
  }

  addGraphNode(node: PortalGraphNode): void {
    const existing = this.state.graph.findIndex((entry) => entry.id === node.id);

    if (existing >= 0) {
      this.state.graph[existing] = node;
    } else {
      this.state.graph.push(node);
    }

    this.recordStatusEvent("graph.updated", `Updated graph node ${node.id}`);
  }

  addMemoryRecord(record: MemoryRecord): void {
    this.state.memoryRecords.push(record);
    this.recordStatusEvent("memory.recorded", `Stored memory record ${record.id}`);
  }

  planAction(action: BrowserAction): string {
    const target = action.target ? ` on ${action.target}` : "";
    return `${action.kind}${target}`;
  }

  getOverview(): RuntimeState {
    return {
      workspace: this.state.workspace,
      agents: [...this.state.agents],
      runtimeStatus: this.state.runtimeStatus,
      browserStatus: this.state.browserStatus,
      steering: { ...this.state.steering },
      sessionEvents: [...this.state.sessionEvents],
      snapshots: [...this.state.snapshots],
      graph: [...this.state.graph],
      memoryRecords: [...this.state.memoryRecords],
      actionQueue: [...this.state.actionQueue]
    };
  }

  getWorkspaceBasePath(): string {
    return this.workspaceBasePath;
  }

  getPendingActions(): ActionQueueItem[] {
    return this.state.actionQueue.filter((item) => item.status === "pending");
  }

  approveAction(actionId: string): ActionQueueItem {
    const action = this.requireAction(actionId);
    action.status = "approved";
    this.recordStatusEvent("action.approved", `Approved action ${actionId}`);
    return { ...action };
  }

  rejectAction(actionId: string, reason = "Rejected by user"): ActionQueueItem {
    const action = this.requireAction(actionId);
    action.status = "rejected";
    action.result = reason;
    this.recordStatusEvent("action.rejected", `Rejected action ${actionId}`);
    return { ...action };
  }

  editAction(
    actionId: string,
    patch: Partial<Pick<ActionQueueItem, "target" | "payload" | "reason">>
  ): ActionQueueItem {
    const action = this.requireAction(actionId);
    if (patch.target !== undefined) action.target = patch.target;
    if (patch.payload !== undefined) action.payload = patch.payload;
    if (patch.reason !== undefined) action.reason = patch.reason;
    this.recordStatusEvent("action.edited", `Edited action ${actionId}`);
    return { ...action };
  }

  createActionRecord(action: BrowserAction, context: ActionContext): ActionQueueItem {
    const decision = evaluateActionPolicy(action, context, this.state.steering);
    const actionRecord: ActionQueueItem = {
      id: createActionId(action.kind),
      actionType: action.kind,
      target: action.target,
      payload: action.payload,
      reason: context.reason,
      riskLevel: decision.riskLevel,
      timestamp: new Date().toISOString(),
      status: decision.blockedReason
        ? "blocked"
        : decision.requiresApproval
          ? "pending"
          : "approved",
      requiresApproval: decision.requiresApproval,
      blockedReason: decision.blockedReason
    };

    this.state.actionQueue.push(actionRecord);

    if (actionRecord.status === "pending") {
      this.setRuntimeStatus("waiting-approval");
      this.recordStatusEvent(
        "action.pending-approval",
        `Action ${actionRecord.id} requires approval`
      );
    } else if (actionRecord.status === "blocked") {
      this.setRuntimeStatus("blocked");
      this.recordStatusEvent(
        "action.blocked",
        `Action ${actionRecord.id} was blocked: ${decision.blockedReason}`
      );
    } else {
      this.recordStatusEvent("action.approved-automatic", `Auto-approved ${actionRecord.id}`);
    }

    return { ...actionRecord };
  }

  attachActionEvidence(
    actionId: string,
    evidence: Pick<ActionQueueItem, "beforeScreenshotPath" | "afterScreenshotPath">
  ): void {
    const action = this.requireAction(actionId);
    if (evidence.beforeScreenshotPath) {
      action.beforeScreenshotPath = evidence.beforeScreenshotPath;
    }
    if (evidence.afterScreenshotPath) {
      action.afterScreenshotPath = evidence.afterScreenshotPath;
    }
  }

  completeAction(actionId: string, result: string): ActionQueueItem {
    const action = this.requireAction(actionId);
    action.status = "completed";
    action.result = result;
    this.setRuntimeStatus("idle");
    this.recordStatusEvent("action.completed", `Completed action ${actionId}`);
    return { ...action };
  }

  failAction(actionId: string, message: string): ActionQueueItem {
    const action = this.requireAction(actionId);
    action.status = "failed";
    action.errorMessage = message;
    this.setRuntimeStatus("failed");
    this.recordStatusEvent("action.failed", `Action ${actionId} failed`);
    return { ...action };
  }

  async ensureWorkspaceDirectories(basePath = this.workspaceBasePath): Promise<void> {
    const directories = [
      this.state.workspace.rootPath,
      ...Object.values(this.state.workspace.directories)
    ];

    await Promise.all(
      directories.map((directory) =>
        mkdir(path.resolve(basePath, directory), { recursive: true })
      )
    );
  }

  async writeSessionReport(basePath = this.workspaceBasePath): Promise<string> {
    await this.ensureWorkspaceDirectories(basePath);

    const reportPath = path.resolve(
      basePath,
      this.state.workspace.directories.reports,
      `session-${Date.now()}.json`
    );

    const report: SessionReport = {
      summary: this.buildSessionSummary(),
      state: this.getOverview()
    };

    await writeFile(reportPath, JSON.stringify(report, null, 2), "utf8");

    this.record({
      type: "session.report.created",
      at: new Date().toISOString(),
      detail: "Session report written",
      artifactPath: reportPath
    });

    return reportPath;
  }

  async writeMemoryRecord(record: MemoryRecord): Promise<string> {
    this.addMemoryRecord(record);
    await this.ensureWorkspaceDirectories();

    const memoryPath = path.resolve(
      this.workspaceBasePath,
      this.state.workspace.directories.memory,
      `${record.id}.json`
    );

    await writeFile(memoryPath, JSON.stringify(record, null, 2), "utf8");
    return memoryPath;
  }

  async detectProjectAwareness(scanBasePath = this.workspaceBasePath): Promise<ProjectAwareness> {
    const packageJsonPath = path.resolve(scanBasePath, "package.json");
    const frameworks = new Set<string>();
    const services = new Set<string>();
    const packageManagers = new Set<string>();

    try {
      const packageJsonRaw = await readFile(packageJsonPath, "utf8");
      const packageJson = JSON.parse(packageJsonRaw) as {
        dependencies?: Record<string, string>;
        devDependencies?: Record<string, string>;
        packageManager?: string;
      };

      const dependencyMap = {
        ...(packageJson.dependencies ?? {}),
        ...(packageJson.devDependencies ?? {})
      };
      const dependencyNames = Object.keys(dependencyMap);

      if (dependencyNames.includes("next")) frameworks.add("Next.js");
      if (dependencyNames.includes("react")) frameworks.add("React");
      if (dependencyNames.includes("vue")) frameworks.add("Vue");
      if (dependencyNames.includes("angular")) frameworks.add("Angular");
      if (dependencyNames.includes("fastify")) frameworks.add("Fastify");
      if (dependencyNames.includes("express")) frameworks.add("Express");
      if (dependencyNames.some((name) => name.startsWith("@supabase/"))) services.add("Supabase");
      if (dependencyNames.some((name) => name.startsWith("stripe"))) services.add("Stripe");
      if (dependencyNames.includes("mongodb")) services.add("MongoDB");
      if (dependencyNames.includes("pg")) services.add("PostgreSQL");
      if (dependencyNames.includes("playwright")) services.add("Playwright");

      if (packageJson.packageManager) {
        packageManagers.add(packageJson.packageManager.split("@")[0]);
      } else {
        packageManagers.add("npm");
      }
    } catch {
      packageManagers.add("unknown");
    }

    return {
      frameworks: [...frameworks],
      services: [...services],
      packageManagers: [...packageManagers],
      summary:
        frameworks.size || services.size
          ? `Detected ${[...frameworks, ...services].join(", ")}`
          : "No strong framework or service signals detected yet"
    };
  }

  private buildSessionSummary(): SessionSummary {
    const consoleErrors = this.state.snapshots.flatMap((snapshot) => snapshot.consoleLogs ?? []);
    const networkErrors = this.state.snapshots.flatMap((snapshot) =>
      (snapshot.networkEvents ?? []).filter(
        (entry) => entry.outcome === "failed" || (entry.status !== undefined && entry.status >= 400)
      )
    );
    const approvedActions = this.state.actionQueue.filter(
      (action) => action.status === "approved" || action.status === "completed"
    );
    const rejectedActions = this.state.actionQueue.filter((action) => action.status === "rejected");
    const failedActions = this.state.actionQueue.filter((action) => action.status === "failed");
    const blockedActions = this.state.actionQueue.filter((action) => action.status === "blocked");

    return {
      currentGoal: this.state.steering.currentGoal,
      actionsAttempted: this.state.actionQueue.length,
      approvedActions: approvedActions.length,
      rejectedActions: rejectedActions.length,
      failedActions: failedActions.length,
      blockedActions: blockedActions.length,
      consoleErrors: consoleErrors.filter((entry) => entry.type === "error").length,
      networkErrors: networkErrors.length,
      riskEvents: this.state.actionQueue.filter((action) => action.riskLevel !== "safe").length,
      suggestedFixes: collectSuggestedFixes(this.state.actionQueue, networkErrors),
      reproductionSteps: this.state.actionQueue.map(
        (action) => `${action.actionType}${action.target ? ` ${action.target}` : ""}`
      )
    };
  }

  private requireAction(actionId: string): ActionQueueItem {
    const action = this.state.actionQueue.find((entry) => entry.id === actionId);

    if (!action) {
      throw new AgentPortalError("ACTION_NOT_FOUND", `Action ${actionId} does not exist`);
    }

    return action;
  }

  private updateAgentStatus(
    agentId: string,
    status: AgentStatus,
    eventType: string
  ): AgentDefinition {
    const agent = this.state.agents.find((entry) => entry.id === agentId);

    if (!agent) {
      throw new AgentPortalError("AGENT_NOT_FOUND", `Agent ${agentId} does not exist`);
    }

    agent.status = status;
    this.recordStatusEvent(eventType, `Agent ${agentId} is now ${status}`);
    return { ...agent };
  }

  private recordStatusEvent(type: string, detail: string): void {
    this.record({
      type,
      at: new Date().toISOString(),
      detail
    });
  }
}

export class BrowserSession {
  private readonly runtime: AgentPortalRuntime;
  private readonly basePath: string;
  private readonly options: BrowserSessionOptions;
  private page?: Page;
  private closeBrowser?: () => Promise<void>;
  private readonly consoleLogs: ConsoleLogEntry[] = [];
  private readonly networkEvents: NetworkEvent[] = [];
  private status: BrowserSessionStatus = "idle";

  constructor(
    runtime: AgentPortalRuntime,
    options: BrowserSessionOptions = {},
    basePath = options.basePath ?? runtime.getWorkspaceBasePath()
  ) {
    this.runtime = runtime;
    this.options = options;
    this.basePath = basePath;
  }

  getStatus(): BrowserSessionStatus {
    return this.status;
  }

  async launch(): Promise<void> {
    if (this.status === "ready" && this.page) {
      return;
    }

    if (this.status === "launching") {
      throw new AgentPortalError(
        "BROWSER_ALREADY_LAUNCHING",
        "A browser session is already launching."
      );
    }

    this.runtime.setRuntimeStatus("thinking");
    this.status = "launching";
    this.runtime.setBrowserStatus("launching");
    await this.runtime.ensureWorkspaceDirectories(this.basePath);

    try {
      const browser = await chromium.launch({
        headless: this.options.headless ?? true
      });
      const context = await browser.newContext({
        viewport: this.options.viewport ?? { width: 1440, height: 900 }
      });

      this.page = await context.newPage();
      this.attachPageListeners(this.page);
      this.closeBrowser = async () => {
        await context.close().catch(() => undefined);
        await browser.close().catch(() => undefined);
      };
      this.status = "ready";
      this.runtime.setBrowserStatus("ready");
      this.runtime.setRuntimeStatus("idle");
      this.runtime.record({
        type: "browser.launched",
        at: new Date().toISOString(),
        detail: "Browser session launched"
      });
    } catch (error) {
      this.status = "error";
      this.runtime.setBrowserStatus("error");
      this.runtime.setRuntimeStatus("failed");
      throw normalizeError(error, "Failed to launch Playwright browser session.");
    }
  }

  async open(url: string): Promise<void> {
    await this.runAction(
      { kind: "open", target: url },
      {
        reason: "Open the requested page",
        currentUrl: this.page?.url() || undefined
      },
      async () => {
        const page = this.getPage();
        await page.goto(url, { waitUntil: "domcontentloaded" });
        this.runtime.record({
          type: "browser.opened",
          at: new Date().toISOString(),
          detail: `Opened ${url}`
        });
      }
    );
  }

  async click(selector: string): Promise<void> {
    await this.runAction(
      { kind: "click", target: selector },
      {
        reason: "Click the requested element",
        currentUrl: this.page?.url(),
        candidateLabel: await this.tryReadLabel(selector)
      },
      async () => {
        const locator = await this.resolveLocator(selector);
        await locator.click();
        this.runtime.record({
          type: "browser.clicked",
          at: new Date().toISOString(),
          detail: `Clicked ${selector}`
        });
      }
    );
  }

  async type(selector: string, value: string): Promise<void> {
    await this.runAction(
      { kind: "type", target: selector, payload: value },
      {
        reason: "Type into the requested input",
        currentUrl: this.page?.url(),
        candidateLabel: await this.tryReadLabel(selector),
        targetFieldType: await this.tryReadInputType(selector)
      },
      async () => {
        const locator = await this.resolveLocator(selector);
        await locator.fill(value);
        this.runtime.record({
          type: "browser.typed",
          at: new Date().toISOString(),
          detail: `Typed into ${selector}`
        });
      }
    );
  }

  async hover(selector: string): Promise<void> {
    await this.runAction(
      { kind: "hover", target: selector },
      {
        reason: "Hover over the requested element",
        currentUrl: this.page?.url(),
        candidateLabel: await this.tryReadLabel(selector)
      },
      async () => {
        const locator = await this.resolveLocator(selector);
        await locator.hover();
        this.runtime.record({
          type: "browser.hovered",
          at: new Date().toISOString(),
          detail: `Hovered ${selector}`
        });
      }
    );
  }

  async scroll(options: ScrollOptions = {}): Promise<void> {
    await this.runAction(
      {
        kind: "scroll",
        target: options.selector,
        payload: `${options.deltaX ?? 0},${options.deltaY ?? 800}`
      },
      {
        reason: "Scroll to reveal more interface context",
        currentUrl: this.page?.url()
      },
      async () => {
        const page = this.getPage();
        if (options.selector) {
          const locator = await this.resolveLocator(options.selector);
          await locator.scrollIntoViewIfNeeded();
          this.runtime.record({
            type: "browser.scrolled",
            at: new Date().toISOString(),
            detail: `Scrolled to ${options.selector}`
          });
          return;
        }

        await page.mouse.wheel(options.deltaX ?? 0, options.deltaY ?? 800);
        this.runtime.record({
          type: "browser.scrolled",
          at: new Date().toISOString(),
          detail: `Scrolled by ${options.deltaX ?? 0}, ${options.deltaY ?? 800}`
        });
      }
    );
  }

  async waitForSelector(selector: string, timeoutMs = 5000): Promise<void> {
    await this.runAction(
      { kind: "wait", target: selector, timeoutMs },
      {
        reason: "Wait for an element to become available",
        currentUrl: this.page?.url(),
        candidateLabel: await this.tryReadLabel(selector)
      },
      async () => {
        const locator = await this.resolveLocator(selector);
        await locator.waitFor({ timeout: timeoutMs, state: "visible" });
        this.runtime.record({
          type: "browser.waited",
          at: new Date().toISOString(),
          detail: `Waited for ${selector}`
        });
      }
    );
  }

  async execute(script: string): Promise<BrowserExecuteResult> {
    let result: unknown;
    await this.runAction(
      { kind: "execute", payload: script },
      {
        reason: "Execute a browser script",
        currentUrl: this.page?.url()
      },
      async () => {
        const page = this.getPage();
        result = await page.evaluate((source) => {
          const callback = new Function(source);
          return callback();
        }, script);
        this.runtime.record({
          type: "browser.executed",
          at: new Date().toISOString(),
          detail: "Executed browser script"
        });
      }
    );

    return { result };
  }

  async readText(selector: string): Promise<BrowserElementText> {
    const page = this.getPage();
    const locator = await this.resolveLocator(selector);
    const text = await locator.textContent();

    this.runtime.record({
      type: "browser.read",
      at: new Date().toISOString(),
      detail: `Read text from ${selector}`
    });

    return {
      selector,
      text
    };
  }

  async inspect(label?: string): Promise<BrowserInspectionResult> {
    return this.capture({
      includeAccessibilityTree: true,
      label
    });
  }

  async capture(options: CaptureOptions = {}): Promise<BrowserInspectionResult> {
    const page = this.getPage();
    await this.runtime.ensureWorkspaceDirectories(this.basePath);

    const now = new Date().toISOString();
    const stamp = createArtifactStamp(options.label);
    const screenshotsDir = path.resolve(
      this.basePath,
      this.runtime.getOverview().workspace.directories.screenshots
    );
    const screenshotPath = path.join(screenshotsDir, `${stamp}.png`);

    await page.screenshot({ path: screenshotPath, fullPage: true });

    const dom = await page.content();
    const title = await page.title();
    const currentUrl = page.url();
    const accessibilityTree = options.includeAccessibilityTree
      ? await page.locator("body").ariaSnapshot()
      : undefined;
    const detectedElements = (await page.evaluate(() => {
      const selectors = [
        "button",
        "a",
        "input",
        "select",
        "textarea",
        "form",
        "[role='dialog']",
        "[role='tab']",
        "[role='menu']",
        "table"
      ];

      return Array.from(document.querySelectorAll(selectors.join(",")))
        .slice(0, 50)
        .map((element, index) => {
          const htmlElement = element as HTMLElement;
          const rect = htmlElement.getBoundingClientRect();
          const tag = htmlElement.tagName.toLowerCase();
          const role = htmlElement.getAttribute("role");
          const type: UIElementType =
            tag === "button"
              ? "button"
              : tag === "form"
                ? "form"
                : tag === "input" || tag === "textarea"
                  ? "input"
                  : tag === "select"
                    ? "dropdown"
                    : tag === "table"
                      ? "table"
                      : role === "dialog"
                        ? "dialog"
                        : role === "tab"
                          ? "tab"
                          : role === "menu"
                            ? "menu"
                            : tag === "a"
                              ? "link"
                              : "custom";

          const label =
            htmlElement.innerText?.trim() ||
            htmlElement.getAttribute("aria-label") ||
            htmlElement.getAttribute("name") ||
            undefined;

          return {
            id: `${type}-${index + 1}`,
            type,
            label,
            selector: htmlElement.id ? `#${htmlElement.id}` : tag,
            bounds: {
              x: rect.x,
              y: rect.y,
              width: rect.width,
              height: rect.height
            },
            actionable:
              tag === "button" ||
              tag === "a" ||
              tag === "input" ||
              tag === "select" ||
              tag === "textarea"
          };
        });
    })) as SerializedUIElement[];

    const consoleLogs = this.consoleLogs.slice(-50);
    const networkEvents = this.networkEvents.slice(-100);

    const snapshot: VisualSnapshot = {
      id: stamp,
      source: "browser",
      capturedAt: now,
      screenshotPath,
      dom,
      accessibilityTree,
      consoleLogs,
      networkEvents,
      label: options.label,
      url: currentUrl,
      detectedElements
    };

    this.runtime.addSnapshot(snapshot);
    this.runtime.record({
      type: "browser.captured",
      at: now,
      detail: `Captured ${currentUrl}`,
      artifactPath: screenshotPath
    });

    return {
      url: currentUrl,
      title,
      dom,
      accessibilityTree,
      screenshotPath,
      consoleLogs,
      networkEvents,
      snapshot
    };
  }

  async close(): Promise<void> {
    if (!this.closeBrowser) {
      this.status = "closed";
      this.runtime.setBrowserStatus("closed");
      return;
    }

    this.status = "closing";
    this.runtime.setBrowserStatus("closing");

    await this.closeBrowser().catch(() => undefined);
    this.closeBrowser = undefined;
    this.page = undefined;
    this.status = "closed";
    this.runtime.setBrowserStatus("closed");

    this.runtime.record({
      type: "browser.closed",
      at: new Date().toISOString(),
      detail: "Browser session closed"
    });
  }

  async shutdownGracefully(): Promise<void> {
    await this.close();
  }

  private async runAction(
    action: BrowserAction,
    context: ActionContext,
    executor: () => Promise<void>
  ): Promise<void> {
    this.ensureBrowserReady();

    const actionRecord = this.runtime.createActionRecord(action, context);

    if (actionRecord.status === "blocked") {
      throw new ActionBlockedError(
        actionRecord.id,
        actionRecord.blockedReason ?? "Action was blocked by steering policy."
      );
    }

    if (actionRecord.status === "pending") {
      throw new ActionApprovalRequiredError(
        actionRecord.id,
        "Action requires user approval before execution."
      );
    }

    this.runtime.setRuntimeStatus("acting");

    try {
      const beforeScreenshotPath = await this.captureActionEvidence(
        `${actionRecord.id}-before`
      );
      this.runtime.attachActionEvidence(actionRecord.id, { beforeScreenshotPath });
      await executor();
      const afterScreenshotPath = await this.captureActionEvidence(`${actionRecord.id}-after`);
      this.runtime.attachActionEvidence(actionRecord.id, { afterScreenshotPath });
      this.runtime.completeAction(actionRecord.id, "Executed successfully");
    } catch (error) {
      this.status = this.status === "disconnected" ? "disconnected" : "error";
      this.runtime.setBrowserStatus(this.status);
      const normalized = normalizeError(error, "Browser action failed.");
      this.runtime.failAction(actionRecord.id, normalized.message);
      throw normalized;
    }
  }

  private async captureActionEvidence(label: string): Promise<string | undefined> {
    if (this.options.evidenceScreenshots === false || !this.page) {
      return undefined;
    }

    const screenshotsDir = path.resolve(
      this.basePath,
      this.runtime.getOverview().workspace.directories.screenshots
    );
    const filePath = path.join(screenshotsDir, `${createArtifactStamp(label)}.png`);
    await this.page.screenshot({ path: filePath, fullPage: true }).catch(() => undefined);
    return filePath;
  }

  private attachPageListeners(page: Page): void {
    page.on("console", (message) => {
      this.consoleLogs.push({
        type: normalizeConsoleType(message.type()),
        text: message.text(),
        location: message.location().url || undefined,
        at: new Date().toISOString()
      });
    });
    page.on("request", (request) => {
      this.networkEvents.push({
        url: request.url(),
        method: request.method(),
        resourceType: request.resourceType(),
        outcome: "pending",
        at: new Date().toISOString()
      });
    });
    page.on("response", (response) => {
      this.networkEvents.push({
        url: response.url(),
        method: response.request().method(),
        resourceType: response.request().resourceType(),
        status: response.status(),
        outcome: response.ok() ? "ok" : "failed",
        at: new Date().toISOString()
      });
    });
    page.on("requestfailed", (request) => {
      this.networkEvents.push({
        url: request.url(),
        method: request.method(),
        resourceType: request.resourceType(),
        outcome: "failed",
        failureText: request.failure()?.errorText,
        at: new Date().toISOString()
      });
    });
    page.on("close", () => {
      this.status = "disconnected";
      this.runtime.setBrowserStatus("disconnected");
      this.runtime.record({
        type: "browser.disconnected",
        at: new Date().toISOString(),
        detail: "Browser page disconnected"
      });
    });
    page.on("crash", () => {
      this.status = "error";
      this.runtime.setBrowserStatus("error");
      this.runtime.record({
        type: "browser.crashed",
        at: new Date().toISOString(),
        detail: "Browser page crashed"
      });
    });
  }

  private async resolveLocator(selector: string): Promise<Locator> {
    const page = this.getPage();
    const candidates = buildLocatorCandidates(selector);

    for (const candidate of candidates) {
      const locator = page.locator(candidate).first();
      const count = await locator.count().catch(() => 0);

      if (count > 0) {
        return locator;
      }
    }

    throw new AgentPortalError(
      "ELEMENT_NOT_FOUND",
      `Unable to find an element for target "${selector}".`,
      "Try approving an edited action with a more specific selector."
    );
  }

  private async tryReadLabel(selector: string): Promise<string | undefined> {
    try {
      const locator = await this.resolveLocator(selector);
      const text = await locator.textContent();
      return text?.trim() || undefined;
    } catch {
      return undefined;
    }
  }

  private async tryReadInputType(selector: string): Promise<string | undefined> {
    try {
      const locator = await this.resolveLocator(selector);
      return (await locator.getAttribute("type")) ?? undefined;
    } catch {
      return undefined;
    }
  }

  private ensureBrowserReady(): void {
    if (this.status === "disconnected") {
      throw new AgentPortalError(
        "BROWSER_DISCONNECTED",
        "The browser session was disconnected. Start a new session and retry."
      );
    }

    if (this.status === "error") {
      throw new AgentPortalError(
        "BROWSER_ERROR",
        "The browser session is in an error state. Restart the runtime and retry."
      );
    }
  }

  private getPage(): Page {
    if (!this.page) {
      throw new AgentPortalError(
        "BROWSER_NOT_READY",
        "Browser session has not been launched yet."
      );
    }

    return this.page;
  }
}

export class VisionCore {
  analyze(context: VisionContext): ScreenUnderstanding {
    const { snapshot, goal } = context;
    const domText = `${snapshot.dom ?? ""} ${snapshot.accessibilityTree ?? ""}`.toLowerCase();
    const issues: string[] = [];
    const nextActions: string[] = [];
    const rootCauseHypotheses: RootCauseHypothesis[] = [];

    const pageCategory: ScreenUnderstanding["pageCategory"] = domText.includes("password")
      ? "login"
      : domText.includes("sign up") || domText.includes("create account")
        ? "signup"
        : domText.includes("dashboard")
          ? "dashboard"
          : domText.includes("pricing")
            ? "pricing"
            : domText.includes("docs") || domText.includes("documentation")
              ? "docs"
              : snapshot.detectedElements.some((element) => element.type === "form")
                ? "form"
                : "unknown";

    const consoleErrors = (snapshot.consoleLogs ?? []).filter((entry) => entry.type === "error");
    const failedNetwork = (snapshot.networkEvents ?? []).filter(
      (entry) => entry.outcome === "failed" || (entry.status !== undefined && entry.status >= 400)
    );

    if (consoleErrors.length > 0) {
      issues.push(`Console errors detected: ${consoleErrors.length}`);
      rootCauseHypotheses.push({
        label: "Frontend runtime issue",
        confidence: 0.72,
        evidence: consoleErrors.slice(0, 3).map((entry) => entry.text)
      });
    }

    if (failedNetwork.length > 0) {
      issues.push(`Network failures detected: ${failedNetwork.length}`);
      rootCauseHypotheses.push({
        label: "Backend or API route failure",
        confidence: 0.82,
        evidence: failedNetwork
          .slice(0, 3)
          .map((entry) => `${entry.status ?? "failed"} ${entry.url}`)
      });
    }

    if (pageCategory === "login") {
      nextActions.push("Fill email and password");
      nextActions.push("Submit authentication form");
      nextActions.push("Verify redirect or error response");
    } else if (pageCategory === "signup") {
      nextActions.push("Open account creation form");
      nextActions.push("Validate required fields");
      nextActions.push("Submit and verify onboarding state");
    } else if (pageCategory === "form") {
      nextActions.push("Fill detected inputs");
      nextActions.push("Submit the form");
      nextActions.push("Inspect confirmation or validation result");
    } else {
      nextActions.push("Inspect primary call-to-action");
      nextActions.push("Navigate through key visible links");
    }

    const summary = goal
      ? `Goal "${goal}" is being evaluated on a ${pageCategory} interface with ${snapshot.detectedElements.length} detected elements.`
      : `Detected a ${pageCategory} interface with ${snapshot.detectedElements.length} actionable or structural elements.`;

    return {
      pageCategory,
      summary,
      userIntent:
        pageCategory === "login"
          ? "Authenticate into an account"
          : pageCategory === "signup"
            ? "Create a new account"
            : pageCategory === "form"
              ? "Complete a structured workflow"
              : undefined,
      issues,
      likelyNextActions: nextActions,
      rootCauseHypotheses
    };
  }
}

export class GoalPlanner {
  createPlan(goal: GoalDefinition, understanding?: ScreenUnderstanding): GoalPlan {
    const title = goal.title.toLowerCase();
    const steps: GoalPlanStep[] = [];

    if (title.includes("sign") || title.includes("login") || title.includes("authenticate")) {
      steps.push(
        createPlanStep("open", "Open the authentication surface"),
        createPlanStep("find-form", "Locate the login form and primary submit action"),
        createPlanStep("fill-form", "Fill the required credentials or test data"),
        createPlanStep("submit", "Submit the form and observe the response"),
        createPlanStep("verify", "Verify redirect, session state, or failure evidence")
      );
    } else if (title.includes("test") || title.includes("qa")) {
      steps.push(
        createPlanStep("open", "Open the target page or workflow"),
        createPlanStep("explore", "Traverse the key interactive controls"),
        createPlanStep("edge-cases", "Try invalid, empty, and unexpected inputs"),
        createPlanStep("capture", "Capture visual and technical evidence"),
        createPlanStep("report", "Summarize issues, root causes, and next actions")
      );
    } else {
      steps.push(
        createPlanStep("understand", "Inspect the current interface and classify the flow"),
        createPlanStep("act", "Perform the most likely actions toward the goal"),
        createPlanStep("verify", "Check whether the intended outcome occurred"),
        createPlanStep("report", "Write the result into memory and reporting artifacts")
      );
    }

    if (understanding?.issues.length) {
      steps.unshift({
        id: "issue-triage",
        title: "issue triage",
        detail: `Review detected issues before execution: ${understanding.issues.join("; ")}`,
        status: "ready"
      });
    }

    return {
      goal,
      steps
    };
  }
}

export class PortalGraph {
  fromSnapshot(snapshot: VisualSnapshot, understanding: ScreenUnderstanding): PortalGraphNode {
    const links = snapshot.detectedElements
      .filter((element) => element.type === "link" && element.label)
      .map((element) => element.label as string);

    return {
      id: snapshot.id,
      label: snapshot.label ?? snapshot.id,
      pageCategory: understanding.pageCategory,
      url: snapshot.url,
      links
    };
  }
}

export function createDefaultWorkspace(name: string): WorkspaceDefinition {
  const root = `workspaces/${name}`;

  return {
    id: name.toLowerCase().replace(/\s+/g, "-"),
    name,
    rootPath: root,
    directories: {
      browserSessions: `${root}/browser-sessions`,
      documents: `${root}/documents`,
      reports: `${root}/reports`,
      screenshots: `${root}/screenshots`,
      logs: `${root}/logs`,
      agents: `${root}/agents`,
      tasks: `${root}/tasks`,
      workflows: `${root}/workflows`,
      memory: `${root}/memory`,
      settings: `${root}/settings`
    }
  };
}

export function resolveWorkspaceFileUrl(
  workspaceBasePath: string,
  relativeFilePath: string
): string {
  return pathToFileURL(path.resolve(workspaceBasePath, relativeFilePath)).toString();
}

export function validatePluginManifest(manifest: PluginManifest): string[] {
  const errors: string[] = [];

  if (!manifest.name) errors.push("Plugin manifest is missing a name.");
  if (!manifest.version) errors.push("Plugin manifest is missing a version.");
  if (!manifest.type) errors.push("Plugin manifest is missing a type.");
  if (!Array.isArray(manifest.permissions)) errors.push("Plugin permissions must be an array.");
  if (!Array.isArray(manifest.commands)) errors.push("Plugin commands must be an array.");

  return errors;
}

function evaluateActionPolicy(
  action: BrowserAction,
  context: ActionContext,
  steering: SteeringState
): ActionPolicyDecision {
  const matchedPolicies: string[] = [];

  if (steering.stopped) {
    return {
      riskLevel: "blocked",
      requiresApproval: false,
      blockedReason: "Agent execution is stopped.",
      matchedPolicies: ["steering:stopped"]
    };
  }

  if (steering.paused) {
    return {
      riskLevel: "medium",
      requiresApproval: true,
      blockedReason: undefined,
      matchedPolicies: ["steering:paused"]
    };
  }

  if (
    steering.lockedDomain &&
    action.kind === "open" &&
    action.target &&
    !domainMatches(action.target, steering.lockedDomain)
  ) {
    return {
      riskLevel: "blocked",
      requiresApproval: false,
      blockedReason: `Action is outside locked domain ${steering.lockedDomain}.`,
      matchedPolicies: ["steering:domain-lock"]
    };
  }

  if (
    steering.lockedTabUrl &&
    context.currentUrl &&
    context.currentUrl !== steering.lockedTabUrl &&
    action.kind !== "open"
  ) {
    return {
      riskLevel: "blocked",
      requiresApproval: false,
      blockedReason: "Agent is locked to the current tab.",
      matchedPolicies: ["steering:tab-lock"]
    };
  }

  let riskLevel: ActionRiskLevel = "low";

  if (action.kind === "inspect" || action.kind === "capture" || action.kind === "wait") {
    riskLevel = "safe";
    matchedPolicies.push("read-only");
  } else if (action.kind === "scroll" || action.kind === "hover" || action.kind === "open") {
    riskLevel = "low";
    matchedPolicies.push("navigation");
  } else if (action.kind === "type") {
    riskLevel = "low";
    matchedPolicies.push("typing");
  } else if (action.kind === "click") {
    riskLevel = "low";
    matchedPolicies.push("click");
  } else if (action.kind === "execute") {
    riskLevel = "medium";
    matchedPolicies.push("script-execution");
  }

  const candidateText = `${action.target ?? ""} ${context.candidateLabel ?? ""} ${context.reason}`.toLowerCase();

  if (context.targetFieldType === "password") {
    riskLevel = "blocked";
    matchedPolicies.push("password-protection");
  } else if (
    includesAny(candidateText, ["billing", "payment", "checkout", "subscribe", "card"])
  ) {
    riskLevel = "blocked";
    matchedPolicies.push("billing-protection");
  } else if (includesAny(candidateText, ["delete", "remove", "drop database", "destroy"])) {
    riskLevel = "high";
    matchedPolicies.push("destructive-action");
  } else if (includesAny(candidateText, ["send", "post publicly", "publish", "submit"])) {
    riskLevel = maxRiskLevel(riskLevel, "medium");
    matchedPolicies.push("submission");
  } else if (includesAny(candidateText, ["login", "sign in", "authenticate"])) {
    riskLevel = maxRiskLevel(riskLevel, "medium");
    matchedPolicies.push("authentication");
  } else if (includesAny(candidateText, ["settings", "admin"])) {
    riskLevel = maxRiskLevel(riskLevel, "high");
    matchedPolicies.push("settings-change");
  }

  if (riskLevel === "blocked") {
    return {
      riskLevel,
      requiresApproval: false,
      blockedReason: "This action is blocked until the user explicitly changes the steering policy.",
      matchedPolicies
    };
  }

  const requiresApproval =
    steering.stepByStepMode ||
    compareRiskLevel(riskLevel, steering.requireApprovalAtOrAbove) >= 0;

  return {
    riskLevel,
    requiresApproval,
    matchedPolicies
  };
}

function collectSuggestedFixes(
  actions: ActionQueueItem[],
  networkErrors: NetworkEvent[]
): string[] {
  const fixes = new Set<string>();

  if (actions.some((action) => action.status === "failed")) {
    fixes.add("Inspect the failed action targets and verify selectors still match the UI.");
  }

  if (actions.some((action) => action.status === "blocked")) {
    fixes.add("Review steering policy locks or approval thresholds before retrying blocked actions.");
  }

  if (networkErrors.length > 0) {
    fixes.add("Check backend routes or local development server health for failed network requests.");
  }

  if (fixes.size === 0) {
    fixes.add("No urgent fixes suggested from this session.");
  }

  return [...fixes];
}

function createArtifactStamp(label?: string): string {
  const suffix = label ? `-${label.replace(/[^a-z0-9-_]+/gi, "-").toLowerCase()}` : "";
  return `${Date.now()}${suffix}`;
}

function createActionId(kind: string): string {
  return `${kind}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function normalizeConsoleType(type: string): ConsoleLogEntry["type"] {
  if (type === "warning" || type === "error" || type === "info") {
    return type;
  }

  return "log";
}

function createPlanStep(id: string, detail: string): GoalPlanStep {
  return {
    id,
    title: id.replace(/-/g, " "),
    detail,
    status: "ready"
  };
}

function compareRiskLevel(left: ActionRiskLevel, right: ActionRiskLevel): number {
  const order: ActionRiskLevel[] = ["safe", "low", "medium", "high", "blocked"];
  return order.indexOf(left) - order.indexOf(right);
}

function maxRiskLevel(left: ActionRiskLevel, right: ActionRiskLevel): ActionRiskLevel {
  return compareRiskLevel(left, right) >= 0 ? left : right;
}

function includesAny(haystack: string, needles: string[]): boolean {
  return needles.some((needle) => {
    const escaped = needle.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
    const regex = new RegExp(`\\b${escaped}\\b`, "i");
    return regex.test(haystack);
  });
}

function domainMatches(target: string, domain: string): boolean {
  try {
    const url = new URL(target);
    return url.hostname === domain;
  } catch {
    return false;
  }
}

function buildLocatorCandidates(selector: string): string[] {
  const normalized = selector.replace(/^#/, "").trim();
  const escaped = normalized.replace(/"/g, '\\"');

  return [
    selector,
    `#${escaped}`,
    `[aria-label="${escaped}"]`,
    `[name="${escaped}"]`,
    `button:has-text("${escaped}")`,
    `a:has-text("${escaped}")`,
    `text="${escaped}"`
  ];
}

function normalizeError(error: unknown, fallbackMessage: string): AgentPortalError {
  if (error instanceof AgentPortalError) {
    return error;
  }

  if (error instanceof Error) {
    return new AgentPortalError("RUNTIME_ERROR", error.message || fallbackMessage);
  }

  return new AgentPortalError("RUNTIME_ERROR", fallbackMessage);
}
