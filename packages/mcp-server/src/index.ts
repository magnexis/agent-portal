import { BrowserAction } from "@agent-portal/core";

export interface ToolRequest {
  tool: string;
  args: Record<string, unknown>;
}

export interface ToolResponse {
  ok: boolean;
  message: string;
}

const supportedTools = new Set([
  "portal.open",
  "portal.click",
  "portal.type",
  "portal.hover",
  "portal.scroll",
  "portal.wait",
  "portal.execute",
  "portal.capture",
  "portal.inspect",
  "portal.agent.start",
  "portal.agent.block",
  "portal.agent.complete",
  "portal.agent.reset"
]);

export function handleToolRequest(request: ToolRequest): ToolResponse {
  if (!supportedTools.has(request.tool)) {
    return {
      ok: false,
      message: `Unsupported tool: ${request.tool}`
    };
  }

  const action = mapToolToAction(request);

  return {
    ok: true,
    message: `Accepted ${action.kind}${action.target ? ` for ${action.target}` : ""}`
  };
}

function mapToolToAction(request: ToolRequest): BrowserAction {
  const target =
    typeof request.args.target === "string" ? request.args.target : undefined;
  const payload =
    typeof request.args.payload === "string" ? request.args.payload : undefined;

  switch (request.tool) {
    case "portal.open":
      return { kind: "open", target };
    case "portal.click":
      return { kind: "click", target };
    case "portal.type":
      return { kind: "type", target, payload };
    case "portal.hover":
      return { kind: "hover", target };
    case "portal.scroll":
      return { kind: "scroll", target, payload };
    case "portal.wait":
      return { kind: "wait", target };
    case "portal.execute":
      return { kind: "execute", payload };
    case "portal.capture":
      return { kind: "capture" };
    case "portal.inspect":
      return { kind: "inspect", target };
    default:
      return { kind: "inspect" };
  }
}
