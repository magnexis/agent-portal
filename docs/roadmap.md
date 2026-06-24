# Agent Portal Roadmap

## Phase 1: Foundation

Goal:
Ship a browser-first local runtime that can observe, act, and report.

Deliverables:

- desktop shell scaffold
- agent runtime contracts
- browser adapter abstraction
- Playwright integration
- session event log
- screenshot capture
- simple report generation

Success criteria:

- an agent can open a local app, inspect it, perform a small workflow, and produce a replayable action history

## Phase 2: Visual Intelligence

Goal:
Make the agent reliably understand what it sees.

Deliverables:

- DOM and accessibility tree fusion
- OCR pipeline
- UI element classification
- visual diffing
- confidence scoring for actions

Success criteria:

- the agent can explain what changed on screen and choose the right target more consistently than raw selectors alone

## Phase 3: Agent Intelligence Layer

Codename:
Project Aperture

Goal:
Move from browser control to interface understanding, goal planning, and durable project memory.

Deliverables:

- `VisionCore` for unified page understanding
- `GoalPlanner` for turning intent into execution steps
- `PortalGraph` for remembered application structure
- memory records for previous findings and plans
- project awareness detection for frameworks and services
- root-cause hypothesis generation from console and network evidence

Success criteria:

- the agent can explain what page it is on, what the user is trying to do, what likely failed, and what to do next

## Phase 4: Multi-Agent Collaboration

Goal:
Allow specialized agents to work together inside one project workspace.

Deliverables:

- shared task board
- agent-to-agent event bus
- role-specific permission sets
- shared memory context
- result handoff model

Success criteria:

- a QA agent can find an issue, a frontend agent can fix it, and a reporter agent can summarize the result in one session

## Phase 5: Desktop Control

Goal:
Expand beyond browser-only automation.

Deliverables:

- window discovery
- native input dispatch
- app adapters for VS Code, Terminal, and File Explorer
- screenshot plus accessibility inspection for desktop apps

Success criteria:

- agents can complete a mixed workflow spanning editor, terminal, browser, and local files

## Phase 6: Platform Surface

Goal:
Turn Agent Portal into an ecosystem others can build on.

Deliverables:

- public SDKs
- MCP server
- CLI tools
- plugin marketplace
- API and WebSocket surfaces

Success criteria:

- third-party developers can create agents, plugins, and workflows without modifying the core app

## Phase 7: Enterprise and Reality Mode

Goal:
Differentiate with trust, resilience, and adversarial testing.

Deliverables:

- shared team workspaces
- permissions and audit logs
- SSO and deployment modes
- reality mode stress behaviors
- policy-driven autonomous QA

Success criteria:

- teams can safely run persistent agents against real products with clear oversight and reproducible evidence
