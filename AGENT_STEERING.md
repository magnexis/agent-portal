# Agent Steering

Agent Steering is the control system that governs what the agent can do.

## Current Controls

- pause agent
- resume agent
- stop agent
- step-by-step mode
- redirect goal
- lock to domain
- lock to current tab
- approve next action
- reject next action
- edit queued action

## Current Policy Rules

- password field typing is blocked
- billing and payment actions are blocked
- destructive actions are high risk
- settings changes are high risk
- submissions and authentication are medium risk
- safe and low risk actions can auto-run unless step-by-step mode is enabled

## Action Queue Fields

- action type
- target
- reason
- risk level
- timestamp
- result
- screenshot before
- screenshot after
