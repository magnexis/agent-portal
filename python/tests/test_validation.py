"""Tests for input validation module."""

from __future__ import annotations

import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_portal.validation import (
    validate_url,
    validate_selector,
    validate_script,
    validate_action_type,
    validate_risk_level,
    validate_text_input,
    sanitize_text,
    validate_config,
    ValidationError,
)


class ValidationTests(unittest.TestCase):
    """Test cases for input validation functions."""

    def test_validate_url_valid_https(self) -> None:
        result = validate_url("https://example.com")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def test_validate_url_valid_http(self) -> None:
        result = validate_url("http://localhost:3000")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def test_validate_url_missing_protocol(self) -> None:
        result = validate_url("example.com")
        self.assertFalse(result.is_valid)
        self.assertIn("protocol", result.errors[0].lower())

    def test_validate_url_dangerous_protocol(self) -> None:
        result = validate_url("file:///etc/passwd")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("protocol" in err.lower() for err in result.errors))

    def test_validate_url_javascript(self) -> None:
        result = validate_url("javascript:alert('xss')")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("dangerous" in err.lower() for err in result.errors))

    def test_validate_url_empty(self) -> None:
        result = validate_url("")
        self.assertFalse(result.is_valid)

    def test_validate_url_localhost_blocked(self) -> None:
        result = validate_url("http://localhost:8080", allow_local=False)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("localhost" in err.lower() for err in result.errors))

    def test_validate_selector_valid_css(self) -> None:
        result = validate_selector("#submit-button")
        self.assertTrue(result.is_valid)

    def test_validate_selector_xss_pattern(self) -> None:
        result = validate_selector("<script>alert('xss')</script>")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("dangerous" in err.lower() for err in result.errors))

    def test_validate_selector_too_long(self) -> None:
        long_selector = "#" + "a" * 1001
        result = validate_selector(long_selector)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("too long" in err.lower() for err in result.errors))

    def test_validate_selector_none(self) -> None:
        result = validate_selector(None)
        self.assertTrue(result.is_valid)

    def test_validate_script_basic(self) -> None:
        result = validate_script("document.querySelector('div')")
        self.assertTrue(result.is_valid)

    def test_validate_script_dangerous_operations(self) -> None:
        result = validate_script("eval('malicious code')")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("dangerous" in err.lower() for err in result.errors))

    def test_validate_script_too_long(self) -> None:
        long_script = "console.log('" + "a" * 10001 + "')"
        result = validate_script(long_script)
        self.assertFalse(result.is_valid)

    def test_validate_action_type_valid(self) -> None:
        for action_type in ["click", "type", "open_url", "screenshot"]:
            result = validate_action_type(action_type)
            self.assertTrue(result.is_valid, f"Failed for {action_type}")

    def test_validate_action_type_invalid(self) -> None:
        result = validate_action_type("hacking")
        self.assertFalse(result.is_valid)
        self.assertIn("Unknown action type", result.errors[0])

    def test_validate_risk_level_valid(self) -> None:
        for level in ["safe", "low", "medium", "high", "blocked"]:
            result = validate_risk_level(level)
            self.assertTrue(result.is_valid, f"Failed for {level}")

    def test_validate_risk_level_invalid(self) -> None:
        result = validate_risk_level("critical")
        self.assertFalse(result.is_valid)

    def test_validate_text_input_valid(self) -> None:
        result = validate_text_input("Hello, World!")
        self.assertTrue(result.is_valid)

    def test_validate_text_input_too_long(self) -> None:
        result = validate_text_input("a" * 501, max_length=500)
        self.assertFalse(result.is_valid)

    def test_sanitize_text_basic(self) -> None:
        result = sanitize_text("  Hello  ")
        self.assertEqual(result, "Hello")

    def test_sanitize_text_null_bytes(self) -> None:
        result = sanitize_text("Hello\x00World")
        self.assertEqual(result, "HelloWorld")

    def test_sanitize_text_control_characters(self) -> None:
        result = sanitize_text("Hello\x01World")
        self.assertEqual(result, "HelloWorld")

    def test_sanitize_text_newlines_preserved(self) -> None:
        result = sanitize_text("Hello\nWorld")
        self.assertEqual(result, "Hello\nWorld")

    def test_sanitize_text_none(self) -> None:
        result = sanitize_text(None)
        self.assertEqual(result, "")

    def test_validate_config_valid(self) -> None:
        config = {
            "runtime_host": "127.0.0.1",
            "runtime_port": 8765,
            "action_mode": "assisted",
            "approval_policy": "medium",
        }
        result = validate_config(config)
        self.assertTrue(result.is_valid)

    def test_validate_config_invalid_host(self) -> None:
        config = {"runtime_host": "0.0.0.0"}
        result = validate_config(config)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("security" in err.lower() or "0.0.0.0" in err for err in result.errors))

    def test_validate_config_invalid_port(self) -> None:
        config = {"runtime_port": 80}
        result = validate_config(config)
        self.assertFalse(result.is_valid)

    def test_validate_config_invalid_action_mode(self) -> None:
        config = {"action_mode": "dangerous"}
        result = validate_config(config)
        self.assertFalse(result.is_valid)


if __name__ == "__main__":
    unittest.main()