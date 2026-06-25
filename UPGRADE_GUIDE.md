# Upgrade Guide: v0.0.2 to v0.1.0

This guide helps you upgrade from Agent Portal v0.0.2 to v0.1.0.

## What's New in v0.1.0

### Security Enhancements

**Input Validation**
The runtime now validates all inputs by default to prevent security issues:

```python
from agent_portal.validation import validate_url, validate_selector, validate_script

# URLs are automatically validated
result = validate_url("https://example.com")
if not result.is_valid:
    print(f"Validation failed: {result.errors}")

# Selectors are checked for XSS patterns
result = validate_selector("#submit-button")
if not result.is_valid:
    print(f"Unsafe selector: {result.errors}")

# Scripts are validated for dangerous operations
result = validate_script("document.querySelector('div')")
if not result.is_valid:
    print(f"Unsafe script: {result.errors}")
```

**Rate Limiting**
The server now includes rate limiting to prevent abuse:

```python
from agent_portal import RateLimiter, RateLimitConfig

# Configure rate limits
config = RateLimitConfig(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_limit=10,
    burst_window_seconds=1.0
)

limiter = RateLimiter(config)

# Check if a request is allowed
allowed, error = limiter.check_rate_limit("client-123")
if not allowed:
    print(f"Rate limited: {error}")
```

**Action Throttling**
Specific actions have stricter limits:

```python
from agent_portal import ActionThrottler

throttler = ActionThrottler()

# Execute actions are limited to 5 per minute
allowed, error = throttler.check_action_allowed("execute", "client-123")
if not allowed:
    print(f"Action throttled: {error}")
```

### Observability

**Metrics Collection**
Track runtime operations with built-in metrics:

```python
from agent_portal import MetricsCollector, get_metrics

# Get the global metrics collector
metrics = get_metrics()

# Track actions
metrics.increment("actions.completed", tags={"action": "click"})
metrics.increment("actions.failed", tags={"action": "navigate"})

# Track browser operations
metrics.set_gauge("runtime.browser_connected", 1.0)
metrics.increment("browser.screenshots")

# Time operations
with metrics.start_timer("operation.duration", tags={"type": "navigate"}):
    # Your operation here
    pass

# View statistics
print(metrics.get_timer_stats("operation.duration"))
print(metrics.get_histogram("action.sizes"))
```

**Export Metrics**
Export metrics to JSON files for analysis:

```python
from pathlib import Path

metrics.export_to_file(Path("metrics.json"))
```

## Migration Steps

### 1. Update Dependencies

```bash
pip install --upgrade agent-portal
```

### 2. Review Rate Limits

The default rate limits are:
- 60 requests per minute
- 1000 requests per hour
- 10 burst requests per second

Customize these in your server configuration if needed:

```python
from agent_portal.server import build_server
from agent_portal import RateLimiter, RateLimitConfig

# Custom rate limits
rate_config = RateLimitConfig(
    requests_per_minute=120,
    requests_per_hour=5000,
    burst_limit=20
)

# Note: You'll need to integrate this with your server setup
# See the documentation for full integration details
```

### 3. Validate Your Code

The new validation may reject previously accepted inputs. Test your workflows:

```python
# Test your URLs
from agent_portal.validation import validate_url

test_urls = [
    "https://your-app.com",
    "http://localhost:3000",
]

for url in test_urls:
    result = validate_url(url)
    if not result.is_valid:
        print(f"URL validation failed for {url}: {result.errors}")
```

### 4. Monitor Metrics

Enable metrics monitoring in your workflows:

```python
from agent_portal import get_metrics

metrics = get_metrics()

# Check key metrics
print(f"Total actions: {metrics.get_counter('actions.total')}")
print(f"Completed: {metrics.get_counter('actions.completed')}")
print(f"Failed: {metrics.get_counter('actions.failed')}")
print(f"Browser connected: {metrics.get_gauge('runtime.browser_connected')}")
```

## Breaking Changes

**None** - This release maintains full backward compatibility.

All existing workflows should continue to work without modification.

## New Configuration Options

### Rate Limiting Configuration

Add to your `agent-portal.config.json`:

```json
{
  "rateLimiting": {
    "enabled": true,
    "requestsPerMinute": 60,
    "requestsPerHour": 1000,
    "burstLimit": 10,
    "burstWindowSeconds": 1.0
  }
}
```

### Metrics Configuration

```json
{
  "metrics": {
    "enabled": true,
    "maxSamples": 10000,
    "exportPath": "workspaces/runtime/metrics"
  }
}
```

## Security Considerations

### URL Validation
The runtime now blocks:
- JavaScript URLs (`javascript:`)
- Data URLs (`data:`)
- File URLs (`file:`)
- VBScript URLs (`vbscript:`)

### Selector Validation
Selectors containing the following patterns are rejected:
- `<script`
- `javascript:`
- `onerror=`, `onload=`, `onclick=`
- `fromCharCode`
- `eval(`

### Script Validation
Scripts with these operations are flagged:
- `document.cookie`
- `localStorage`, `sessionStorage`
- `window.location`
- `eval()`, `Function()`
- `document.write`
- `XMLHttpRequest`, `fetch()`

## Testing Your Upgrade

Run the test suite to ensure everything works:

```bash
# Run all tests
npm test

# Run Python tests only
python -m unittest discover -s python/tests -v

# Run specific test modules
python -m unittest tests.test_validation -v
python -m unittest tests.test_rate_limit -v
python -m unittest tests.test_metrics -v
```

## Troubleshooting

### Rate Limit Errors

If you see rate limit errors:
1. Increase limits in configuration
2. Implement exponential backoff in your client
3. Use batch operations when possible

### Validation Errors

If validation fails:
1. Review the error messages
2. Update your inputs to meet validation requirements
3. Use `sanitize_text()` to clean inputs if needed

### Metrics Not Working

If metrics aren't being collected:
1. Check that the metrics module is imported
2. Ensure you're using the global collector via `get_metrics()`
3. Verify no exceptions are being swallowed

## Getting Help

- 📖 **Documentation**: See the full [README.md](README.md)
- 🐛 **Issues**: Report bugs at [GitHub Issues](https://github.com/magnexis/agent-portal/issues)
- 💬 **Discussions**: Ask questions in [GitHub Discussions](https://github.com/magnexis/agent-portal/discussions)

## What's Next

Future releases will include:
- Advanced vision core for page understanding
- Multi-agent coordination
- Desktop application control
- Enhanced reporting capabilities

Stay tuned for more updates!