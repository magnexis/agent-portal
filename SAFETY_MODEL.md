# Safety Model

Agent Portal uses a policy engine to classify actions into:

- `safe`
- `low`
- `medium`
- `high`
- `blocked`

## Protected Actions

- typing into password fields
- billing and payment actions
- cross-domain navigation when domain lock is enabled
- leaving the locked tab when tab lock is enabled

## Runtime Protections

- duplicate browser launch prevention
- graceful browser shutdown
- browser disconnect detection
- blocked and pending action queue states
- user-facing runtime errors
