"""Tests for rate limiting module."""

from __future__ import annotations

import time
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_portal.rate_limit import (
    RateLimiter,
    RateLimitConfig,
    ActionThrottler,
    ClientInfo,
)


class RateLimiterTests(unittest.TestCase):
    """Test cases for the RateLimiter class."""

    def test_basic_request_allowed(self) -> None:
        limiter = RateLimiter()
        allowed, error = limiter.check_rate_limit("client1")
        self.assertTrue(allowed)
        self.assertIsNone(error)

    def test_request_within_limits(self) -> None:
        config = RateLimitConfig(requests_per_minute=10, burst_limit=5)
        limiter = RateLimiter(config)
        
        # Should allow up to burst limit
        for i in range(5):
            allowed, error = limiter.check_rate_limit("client1")
            self.assertTrue(allowed, f"Request {i} should be allowed")
            self.assertIsNone(error)

    def test_burst_limit_exceeded(self) -> None:
        config = RateLimitConfig(requests_per_minute=100, burst_limit=3)
        limiter = RateLimiter(config)
        
        # Exhaust burst limit
        for i in range(3):
            allowed, _ = limiter.check_rate_limit("client1")
            self.assertTrue(allowed)
        
        # Next request should be blocked
        allowed, error = limiter.check_rate_limit("client1")
        self.assertFalse(allowed)
        self.assertIn("Burst limit exceeded", error or "")

    def test_per_minute_limit(self) -> None:
        config = RateLimitConfig(requests_per_minute=5, burst_limit=10)
        limiter = RateLimiter(config)
        
        # This should be within burst but hit per-minute limit
        for i in range(6):
            allowed, _ = limiter.check_rate_limit("client1")
        
        # Should be blocked due to per-minute limit
        allowed, error = limiter.check_rate_limit("client1")
        self.assertFalse(allowed)
        self.assertIn("per minute", error or "")

    def test_different_clients_independent(self) -> None:
        config = RateLimitConfig(requests_per_minute=2, burst_limit=2)
        limiter = RateLimiter(config)
        
        # Client 1 makes 2 requests
        for _ in range(2):
            limiter.check_rate_limit("client1")
        
        # Client 1 should be blocked on third request
        allowed, _ = limiter.check_rate_limit("client1")
        self.assertFalse(allowed)
        
        # Client 2 should still be allowed
        allowed, _ = limiter.check_rate_limit("client2")
        self.assertTrue(allowed)

    def test_block_timeout(self) -> None:
        config = RateLimitConfig(
            requests_per_minute=10,
            burst_limit=2,
            burst_window_seconds=0.5
        )
        limiter = RateLimiter(config)
        
        # Exhaust burst limit
        for _ in range(2):
            limiter.check_rate_limit("client1")
        
        # Should be blocked
        allowed, _ = limiter.check_rate_limit("client1")
        self.assertFalse(allowed)
        
        # Wait for block to expire
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, _ = limiter.check_rate_limit("client1")
        self.assertTrue(allowed)

    def test_reset_client(self) -> None:
        config = RateLimitConfig(requests_per_minute=2, burst_limit=2)
        limiter = RateLimiter(config)
        
        # Exhaust limits
        for _ in range(2):
            limiter.check_rate_limit("client1")
        
        # Should be blocked
        allowed, _ = limiter.check_rate_limit("client1")
        self.assertFalse(allowed)
        
        # Reset client
        limiter.reset_client("client1")
        
        # Should be allowed again
        allowed, _ = limiter.check_rate_limit("client1")
        self.assertTrue(allowed)

    def test_cleanup_old_clients(self) -> None:
        limiter = RateLimiter()
        
        # Add some clients
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client2")
        
        # They should exist
        self.assertIn("client1", limiter.clients)
        self.assertIn("client2", limiter.clients)
        
        # Cleanup with max age of 0 hours (should remove all)
        removed = limiter.cleanup_old_clients(max_age_hours=0)
        self.assertGreater(removed, 0)
        
        # Clients should be removed
        self.assertNotIn("client1", limiter.clients)

    def test_default_config(self) -> None:
        limiter = RateLimiter()
        config = limiter.config
        
        self.assertEqual(config.requests_per_minute, 60)
        self.assertEqual(config.requests_per_hour, 1000)
        self.assertEqual(config.burst_limit, 10)
        self.assertEqual(config.burst_window_seconds, 1.0)


class ActionThrottlerTests(unittest.TestCase):
    """Test cases for the ActionThrottler class."""

    def setUp(self) -> None:
        self.throttler = ActionThrottler()

    def test_click_action_allowed(self) -> None:
        allowed, error = self.throttler.check_action_allowed("click")
        self.assertTrue(allowed)
        self.assertIsNone(error)

    def test_execute_action_stricter_limits(self) -> None:
        # Execute action has stricter limits (5 per minute)
        for _ in range(5):
            allowed, _ = self.throttler.check_action_allowed("execute")
            self.assertTrue(allowed)
        
        # 6th request should be blocked
        allowed, error = self.throttler.check_action_allowed("execute")
        self.assertFalse(allowed)
        self.assertIn("execute", error or "")

    def test_different_actions_independent(self) -> None:
        # Exhaust execute limit
        for _ in range(6):
            self.throttler.check_action_allowed("execute")
        
        # Execute should be blocked
        allowed, _ = self.throttler.check_action_allowed("execute")
        self.assertFalse(allowed)
        
        # Click should still be allowed
        allowed, _ = self.throttler.check_action_allowed("click")
        self.assertTrue(allowed)

    def test_per_client_throttling(self) -> None:
        # Exhaust execute for client1
        for _ in range(6):
            self.throttler.check_action_allowed("execute", "client1")
        
        # Client1 should be blocked
        allowed, _ = self.throttler.check_action_allowed("execute", "client1")
        self.assertFalse(allowed)
        
        # Client2 should still be allowed
        allowed, _ = self.throttler.check_action_allowed("execute", "client2")
        self.assertTrue(allowed)

    def test_cleanup_old_entries(self) -> None:
        self.throttler.check_action_allowed("click", "client1")
        self.throttler.check_action_allowed("type", "client1")
        
        # Should have entries
        self.assertGreater(len(self.throttler._action_counts), 0)
        
        # Cleanup with max age 0
        removed = self.throttler.cleanup_old_entries(max_age_hours=0)
        
        # Entries should be removed
        self.assertEqual(removed, 2)

    def test_unknown_action_type_defaults(self) -> None:
        # Unknown actions should get default limits
        for _ in range(70):
            allowed, _ = self.throttler.check_action_allowed("unknown_action")
        
        # Should be blocked at default 60/min limit
        allowed, _ = self.throttler.check_action_allowed("unknown_action")
        self.assertFalse(allowed)

    def test_screenshot_stricter_than_click(self) -> None:
        # Screenshot has limit of 10 per minute, click has 60
        for _ in range(11):
            self.throttler.check_action_allowed("screenshot")
        
        allowed, _ = self.throttler.check_action_allowed("screenshot")
        self.assertFalse(allowed)
        
        # Click should still be allowed
        allowed, _ = self.throttler.check_action_allowed("click")
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()