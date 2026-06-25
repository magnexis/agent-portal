# Changelog

All notable changes to Agent Portal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-XX

### Added
- **Security Features**
  - Input validation module (`validation.py`) with comprehensive validation for URLs, selectors, scripts, action types, risk levels, and configurations
  - Rate limiting system (`rate_limit.py`) with configurable per-minute, per-hour, and burst limits
  - Action throttling to prevent abuse of specific operations (execute, click, type, screenshot)
  - Thread-safe metrics and telemetry system (`metrics.py`) for observability
  - Automatic XSS pattern detection in selectors and URLs
  - Dangerous protocol blocking (javascript:, data:, file:, vbscript:, etc.)
  
- **Runtime Improvements**
  - Metrics collection for actions (total, completed, failed, blocked, approved, rejected)
  - Browser operation metrics (navigations, screenshots, errors)
  - Network metrics (requests, failures, console errors)
  - Timer context manager for performance tracking
  - Histogram statistics for value distributions
  - Export metrics to JSON files

- **Testing**
  - Comprehensive test suite for validation module (29 tests)
  - Test suite for rate limiting module
  - Test suite for metrics collection module
  - All tests pass successfully

- **Enhancements**
  - Better error handling with structured error messages
  - Improved security posture with input sanitization
  - Performance monitoring and observability
  - Memory-safe sample limiting in metrics

### Security
- Added URL scheme validation to prevent dangerous protocols
- Blocked JavaScript execution in page context from untrusted sources
- Added selector injection protection
- Implemented rate limiting to prevent DoS
- Configurable action throttling for high-risk operations
- Sanitization of text inputs to remove control characters

### Performance
- Optimized metrics storage with automatic cleanup
- Sliding window rate limiting algorithm
- Sample limits to prevent memory leaks
- Efficient client-based rate tracking

### Documentation
- Added comprehensive docstrings for all new modules
- Updated README with security features
- Added inline documentation for validation rules

---

## [0.0.2] - Previous Release
- Initial stable release with Python runtime
- Browser control via Playwright
- HTTP API server
- VS Code extension
- Basic action approval workflow
- Report generation

---

## [0.0.1] - Initial Release
- Project scaffolding
- Basic runtime structure
- Plugin system foundation