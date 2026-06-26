"""Input validation and sanitization utilities for Agent Portal."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: list[str]


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


# URL validation patterns
SAFE_PROTOCOLS = {"http", "https"}
DOMAIN_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-_.]*\.[a-zA-Z]{2,}$")
LOCALHOST_PATTERNS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
}


def validate_url(url: str, allow_local: bool = True) -> ValidationResult:
    """
    Validate a URL for safety and structure.
    
    Args:
        url: The URL to validate
        allow_local: Whether to allow localhost/local network addresses
        
    Returns:
        ValidationResult indicating if the URL is valid
    """
    errors: list[str] = []
    
    if not url or not isinstance(url, str):
        errors.append("URL must be a non-empty string")
        return ValidationResult(False, errors)
    
    # Check for dangerous patterns first (before parsing)
    url_lower = url.lower()
    if any(pattern in url_lower for pattern in ["javascript:", "data:", "file:", "ftp:", "vbscript:"]):
        errors.append("Potentially dangerous URL pattern detected")
        return ValidationResult(False, errors)
    
    try:
        parsed = urlparse(url)
    except Exception as exc:
        errors.append(f"Invalid URL format: {exc}")
        return ValidationResult(False, errors)
    
    if not parsed.scheme:
        errors.append("URL must include a protocol (http:// or https://)")
    elif parsed.scheme not in SAFE_PROTOCOLS:
        errors.append(f"Unsupported protocol: {parsed.scheme}. Only http:// and https:// are allowed")
    
    if not parsed.netloc:
        errors.append("URL must include a hostname")
        return ValidationResult(False, errors)
    
    # Check for localhost if not explicitly allowed
    if not allow_local:
        if parsed.hostname in LOCALHOST_PATTERNS or parsed.hostname == "0.0.0.0":
            errors.append("Localhost addresses are not allowed in this mode")
    
    return ValidationResult(len(errors) == 0, errors)


def validate_selector(selector: str | None) -> ValidationResult:
    """
    Validate a CSS selector for injection safety.
    
    Args:
        selector: The CSS selector to validate
        
    Returns:
        ValidationResult indicating if the selector is safe
    """
    errors: list[str] = []
    
    if not selector:
        return ValidationResult(True, errors)
    
    if not isinstance(selector, str):
        errors.append("Selector must be a string")
        return ValidationResult(False, errors)
    
    if len(selector) > 1000:
        errors.append("Selector is too long (max 1000 characters)")
    
    # Check for potential XSS patterns
    xss_patterns = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "onclick=",
        "fromCharCode",
        "eval(",
    ]
    
    selector_lower = selector.lower()
    if any(pattern in selector_lower for pattern in xss_patterns):
        errors.append("Selector contains potentially dangerous patterns")
    
    return ValidationResult(len(errors) == 0, errors)


def validate_script(script: str) -> ValidationResult:
    """
    Validate a JavaScript script for basic safety.
    
    Args:
        script: The JavaScript code to validate
        
    Returns:
        ValidationResult indicating if the script passes basic checks
    """
    errors: list[str] = []
    
    if not script or not isinstance(script, str):
        errors.append("Script must be a non-empty string")
        return ValidationResult(False, errors)
    
    if len(script) > 10000:
        errors.append("Script is too long (max 10000 characters)")
    
    # Check for obviously dangerous operations
    dangerous_patterns = [
        "document.cookie",
        "localStorage",
        "sessionStorage",
        "window.location",
        "eval(",
        "Function(",
        "document.write",
        "XMLHttpRequest",
        "fetch(",
    ]
    
    script_lower = script.lower()
    matches = [pattern for pattern in dangerous_patterns if pattern.lower() in script_lower]
    
    if matches:
        errors.append(f"Script contains potentially dangerous operations: {', '.join(matches)}")
    
    return ValidationResult(len(errors) == 0, errors)


def validate_action_type(action_type: str) -> ValidationResult:
    """
    Validate that an action type is supported.
    
    Args:
        action_type: The action type to validate
        
    Returns:
        ValidationResult indicating if the action type is valid
    """
    errors: list[str] = []
    
    valid_types = {
        "open_url", "click", "type", "scroll", "hover", "wait",
        "screenshot", "inspect", "read_text", "execute",
        "browser_close", "browser_refresh", "browser_back", "browser_forward",
    }
    
    if not action_type or not isinstance(action_type, str):
        errors.append("Action type must be a non-empty string")
        return ValidationResult(False, errors)
    
    if action_type not in valid_types:
        errors.append(f"Unknown action type: {action_type}. Valid types: {', '.join(sorted(valid_types))}")
    
    return ValidationResult(len(errors) == 0, errors)


def validate_risk_level(risk_level: str) -> ValidationResult:
    """
    Validate that a risk level is within the allowed range.
    
    Args:
        risk_level: The risk level to validate
        
    Returns:
        ValidationResult indicating if the risk level is valid
    """
    errors: list[str] = []
    
    valid_levels = {"safe", "low", "medium", "high", "blocked"}
    
    if not risk_level or not isinstance(risk_level, str):
        errors.append("Risk level must be a non-empty string")
        return ValidationResult(False, errors)
    
    if risk_level not in valid_levels:
        errors.append(f"Invalid risk level: {risk_level}. Valid levels: {', '.join(sorted(valid_levels))}")
    
    return ValidationResult(len(errors) == 0, errors)


def validate_text_input(value: str, max_length: int = 500, field_name: str = "value") -> ValidationResult:
    """
    Validate a general text input field.
    
    Args:
        value: The text value to validate
        max_length: Maximum allowed length
        field_name: Name of the field for error messages
        
    Returns:
        ValidationResult indicating if the input is valid
    """
    errors: list[str] = []
    
    if not isinstance(value, str):
        errors.append(f"{field_name} must be a string")
        return ValidationResult(False, errors)
    
    if len(value) > max_length:
        errors.append(f"{field_name} is too long (max {max_length} characters)")
    
    return ValidationResult(len(errors) == 0, errors)


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing or escaping potentially harmful characters.
    
    Args:
        text: The text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove null bytes and other control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def validate_config(config: dict[str, Any]) -> ValidationResult:
    """
    Validate runtime configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        ValidationResult indicating if the configuration is valid
    """
    errors: list[str] = []
    
    # Validate host
    if "runtime_host" in config:
        host = config["runtime_host"]
        if not isinstance(host, str):
            errors.append("runtime_host must be a string")
        elif host == "0.0.0.0":
            errors.append("runtime_host cannot be 0.0.0.0 for security reasons")
    
    # Validate port
    if "runtime_port" in config:
        port = config["runtime_port"]
        if not isinstance(port, int) or not (1024 <= port <= 65535):
            errors.append("runtime_port must be an integer between 1024 and 65535")
    
    # Validate action_mode
    if "action_mode" in config:
        mode = config["action_mode"]
        valid_modes = {"read-only", "assisted", "autonomous", "manual-override"}
        if mode not in valid_modes:
            errors.append(f"action_mode must be one of: {', '.join(sorted(valid_modes))}")
    
    # Validate approval_policy
    if "approval_policy" in config:
        policy = config["approval_policy"]
        valid_policies = {"safe", "low", "medium", "high", "blocked"}
        if policy not in valid_policies:
            errors.append(f"approval_policy must be one of: {', '.join(sorted(valid_policies))}")
    
    return ValidationResult(len(errors) == 0, errors)