# Agent Portal Architecture

## Product Shape

Agent Portal is best treated as a platform, not a single app. The architecture needs to support:

- local-first execution
- visual awareness
- controlled actions
- multi-agent coordination
- replayable sessions
- durable memory
- explicit permissions

## Core Layers

### 1. Desktop Shell

Responsibilities:

- native window management
- embedded browser surfaces
- agent console UI
- session inspector
- settings and permissions

Recommended implementation path:

- start with Electron for speed and ecosystem reach
- evaluate Tauri later if footprint becomes a major constraint

### 2. Agent Runtime

Responsibilities:

- spawn and isolate agents
- manage task state
- coordinate multi-agent execution
- stream events to the UI
- attach tools and permissions

Key concepts:

- agent definitions
- task queue
- execution policies
- event bus
- cancellation and recovery

### 3. Vision Pipeline

Responsibilities:

- capture screenshots
- read DOM structure
- parse accessibility trees
- run OCR
- detect actionable UI elements
- emit state diffs over time

Output contract:

- normalized `VisualSnapshot`
- element list with labels, selectors, roles, and bounds
- changed/appeared/disappeared annotations

### 3.5 Vision Core

Responsibilities:

- fuse screenshots, DOM, accessibility, console, and network evidence
- classify the current interface
- infer likely user intent
- generate root-cause hypotheses when flows fail
- hand structured context to goal planning and memory

Initial implementation path:

- heuristics and typed contracts first
- model-assisted reasoning layer second
- confidence scoring and self-healing action selection third

### 4. Browser Control Layer

Responsibilities:

- navigation
- clicking
- typing
- waiting
- file upload and download
- script execution
- trace capture

Recommended implementation path:

- Playwright as the first execution backend
- adapter abstraction so Selenium or remote browsers can be added later

### 5. Desktop Control Layer

Responsibilities:

- window discovery
- input simulation
- native app inspection
- application-specific adapters

Recommended implementation path:

- define the abstraction now
- ship browser-first before broad desktop automation
- add Windows-first adapters for VS Code, Terminal, and File Explorer

### 6. Memory Engine

Responsibilities:

- persist project context
- store recent findings
- keep reusable workflows
- retain user and team preferences

Storage model:

- workspace metadata
- task history
- vector or semantic memory later
- durable file-backed logs immediately

### 6.5 Portal Graph

Responsibilities:

- map pages, links, and recurring flows
- keep a remembered topology of the app
- support self-healing navigation when selectors change
- provide reusable structure for future agents

### 7. Session Recorder

Responsibilities:

- append action timeline
- attach screenshots and console logs
- reconstruct replay views
- generate bug reports

Initial storage approach:

- append-only event log
- screenshot references
- per-session manifest JSON

### 8. Security Manager

Responsibilities:

- tool permissions
- file and network boundaries
- secrets handling
- action approvals
- auditability

This is a product boundary, not a bolt-on feature.

## Monorepo Strategy

`packages/core`

- shared contracts
- runtime state shapes
- orchestration primitives

`packages/sdk`

- external developer API
- stable ergonomic wrapper over runtime actions

`packages/mcp-server`

- tool-facing surface for agent frameworks
- command validation
- capability exposure

`apps/desktop`

- first-party desktop operator experience
- live state inspection
- future visual workspace UI

## Suggested First Vertical Slice

Build the smallest end-to-end system that proves the concept:

1. Launch desktop shell
2. Open browser page
3. Capture screenshot and DOM
4. Detect clickable elements
5. Execute one click or type action
6. Record the session timeline
7. Generate a simple report

If this loop feels great, the rest of the platform has a solid foundation.

## Phase 3 Direction

The next platform shift is from action execution to understanding:

1. Capture multimodal evidence
2. Classify the interface and workflow
3. Generate a goal plan from intent
4. Write understanding into memory
5. Reuse graph and memory across future sessions
