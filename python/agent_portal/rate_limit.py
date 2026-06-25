"""Rate limiting and throttling for Agent Portal server."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Callable


@dataclass(frozen=True)
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    burst_window_seconds: float = 1.0


@dataclass
class ClientInfo:
    """Information about a client for rate limiting."""
    request_times: list[float]
    burst_request_times: list[float]
    is_blocked: bool = False
    blocked_until: float = 0.0


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window algorithm.
    """
    
    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self.config = config or RateLimitConfig()
        self.clients: dict[str, ClientInfo] = {}
        self._lock = Lock()
    
    def check_rate_limit(self, client_id: str) -> tuple[bool, str | None]:
        """
        Check if a client is within rate limits.
        
        Args:
            client_id: Unique identifier for the client (IP address or token)
            
        Returns:
            Tuple of (allowed, error_message)
        """
        with self._lock:
            now = time.time()
            
            # Get or create client info
            if client_id not in self.clients:
                self.clients[client_id] = ClientInfo(request_times=[], burst_request_times=[])
            
            client = self.clients[client_id]
            
            # Check if client is currently blocked
            if client.is_blocked:
                if now < client.blocked_until:
                    remaining = int(client.blocked_until - now)
                    return False, f"Rate limit exceeded. Try again in {remaining} seconds."
                else:
                    # Unblock the client
                    client.is_blocked = False
                    client.blocked_until = 0.0
            
            # Clean up old request times (older than 1 hour)
            one_hour_ago = now - 3600
            client.request_times = [t for t in client.request_times if t > one_hour_ago]
            
            # Clean up burst times
            burst_window = now - self.config.burst_window_seconds
            client.burst_request_times = [t for t in client.burst_request_times if t > burst_window]
            
            # Check burst limit
            if len(client.burst_request_times) >= self.config.burst_limit:
                client.is_blocked = True
                client.blocked_until = now + 60  # Block for 1 minute
                return False, f"Burst limit exceeded ({self.config.burst_limit} requests in {self.config.burst_window_seconds}s). Blocked for 60 seconds."
            
            # Check per-minute limit
            one_minute_ago = now - 60
            requests_last_minute = sum(1 for t in client.request_times if t > one_minute_ago)
            if requests_last_minute >= self.config.requests_per_minute:
                return False, f"Rate limit exceeded: {self.config.requests_per_minute} requests per minute."
            
            # Check per-hour limit
            if len(client.request_times) >= self.config.requests_per_hour:
                return False, f"Rate limit exceeded: {self.config.requests_per_hour} requests per hour."
            
            # Record this request
            client.request_times.append(now)
            client.burst_request_times.append(now)
            
            return True, None
    
    def record_request(self, client_id: str) -> None:
        """Record a request for rate limiting (should be called after successful response)."""
        with self._lock:
            now = time.time()
            if client_id not in self.clients:
                self.clients[client_id] = ClientInfo(request_times=[], burst_request_times=[])
            
            self.clients[client_id].request_times.append(now)
            self.clients[client_id].burst_request_times.append(now)
    
    def reset_client(self, client_id: str) -> None:
        """Reset rate limit state for a specific client."""
        with self._lock:
            if client_id in self.clients:
                del self.clients[client_id]
    
    def cleanup_old_clients(self, max_age_hours: float = 24.0) -> int:
        """
        Remove clients that haven't made requests in a while.
        
        Returns:
            Number of clients removed
        """
        with self._lock:
            now = time.time()
            cutoff = now - (max_age_hours * 3600)
            
            to_remove = [
                client_id
                for client_id, client in self.clients.items()
                if not client.request_times or client.request_times[-1] < cutoff
            ]
            
            for client_id in to_remove:
                del self.clients[client_id]
            
            return len(to_remove)


class ActionThrottler:
    """
    Throttles specific action types to prevent abuse.
    """
    
    def __init__(self) -> None:
        self._action_counts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
        
        # Configure throttling limits per action type
        self._limits = {
            "execute": {"max_per_minute": 5, "max_per_hour": 50},
            "open_url": {"max_per_minute": 20, "max_per_hour": 200},
            "type": {"max_per_minute": 30, "max_per_hour": 300},
            "click": {"max_per_minute": 60, "max_per_hour": 600},
            "screenshot": {"max_per_minute": 10, "max_per_hour": 100},
        }
    
    def check_action_allowed(
        self,
        action_type: str,
        client_id: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Check if an action is allowed based on throttling rules.
        
        Args:
            action_type: The type of action being performed
            client_id: Optional client identifier for per-client limits
            
        Returns:
            Tuple of (allowed, error_message)
        """
        with self._lock:
            now = time.time()
            key = f"{action_type}:{client_id}" if client_id else action_type
            
            # Get or create action times list
            if key not in self._action_counts:
                self._action_counts[key] = []
            
            times = self._action_counts[key]
            
            # Clean up old times (older than 1 hour)
            one_hour_ago = now - 3600
            times[:] = [t for t in times if t > one_hour_ago]
            
            # Get limits for this action type
            limits = self._limits.get(action_type, {"max_per_minute": 60, "max_per_hour": 600})
            
            # Check per-minute limit
            one_minute_ago = now - 60
            requests_last_minute = sum(1 for t in times if t > one_minute_ago)
            if requests_last_minute >= limits["max_per_minute"]:
                return False, f"Action '{action_type}' throttled: {limits['max_per_minute']} per minute."
            
            # Check per-hour limit
            if len(times) >= limits["max_per_hour"]:
                return False, f"Action '{action_type}' throttled: {limits['max_per_hour']} per hour."
            
            # Record this action
            times.append(now)
            
            return True, None
    
    def cleanup_old_entries(self, max_age_hours: float = 24.0) -> int:
        """Remove old entries to prevent memory leaks."""
        with self._lock:
            now = time.time()
            cutoff = now - (max_age_hours * 3600)
            
            keys_to_remove = []
            for key, times in self._action_counts.items():
                times[:] = [t for t in times if t > cutoff]
                if not times:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._action_counts[key]
            
            return len(keys_to_remove)


# Decorator for rate limiting functions
def rate_limited(
    rate_limiter: RateLimiter,
    client_id_func: Callable[..., str]
):
    """
    Decorator to apply rate limiting to a function.
    
    Args:
        rate_limiter: RateLimiter instance to use
        client_id_func: Function to extract client_id from function arguments
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            client_id = client_id_func(*args, **kwargs)
            allowed, error = rate_limiter.check_rate_limit(client_id)
            
            if not allowed:
                from .exceptions import AgentPortalError
                raise AgentPortalError(
                    error or "Rate limit exceeded",
                    module="agent_portal.rate_limit",
                    likely_cause="Too many requests from this client",
                    suggested_fix="Wait and retry, or contact administrator",
                    can_continue=True,
                )
            
            result = func(*args, **kwargs)
            rate_limiter.record_request(client_id)
            return result
        
        return wrapper
    return decorator