"""Metrics and telemetry system for Agent Portal."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """A single metric value."""
    name: str
    value: float
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class HistogramBucket:
    """A histogram bucket for tracking distributions."""
    count: int = 0
    sum: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")


class MetricsCollector:
    """
    Thread-safe metrics collector for runtime observability.
    """
    
    def __init__(self, max_samples: int = 10000) -> None:
        self.max_samples = max_samples
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, HistogramBucket] = defaultdict(HistogramBucket)
        self._timers: dict[str, list[float]] = defaultdict(list)
        self._samples: list[MetricValue] = []
        self._lock = Lock()
        
        # Initialize built-in metrics
        self.init_builtin_metrics()
    
    def init_builtin_metrics(self) -> None:
        """Initialize built-in runtime metrics."""
        with self._lock:
            # Runtime metrics
            self._gauges["runtime.uptime_seconds"] = 0.0
            self._gauges["runtime.active_sessions"] = 0.0
            self._gauges["runtime.browser_connected"] = 0.0
            
            # Action metrics
            self._counters["actions.total"] = 0.0
            self._counters["actions.completed"] = 0.0
            self._counters["actions.failed"] = 0.0
            self._counters["actions.blocked"] = 0.0
            self._counters["actions.approved"] = 0.0
            self._counters["actions.rejected"] = 0.0
            
            # Browser metrics
            self._counters["browser.navigations"] = 0.0
            self._counters["browser.screenshots"] = 0.0
            self._counters["browser.errors"] = 0.0
            
            # Network metrics
            self._counters["network.requests"] = 0.0
            self._counters["network.failures"] = 0.0
            self._counters["network.console_errors"] = 0.0
    
    def increment(self, name: str, value: float = 1.0, tags: dict[str, str] | None = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Amount to increment by
            tags: Optional tags for the metric
        """
        with self._lock:
            self._counters[name] += value
            self._add_sample(name, value, MetricType.COUNTER, tags or {})
    
    def set_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Value to set
            tags: Optional tags for the metric
        """
        with self._lock:
            self._gauges[name] = value
            self._add_sample(name, value, MetricType.GAUGE, tags or {})
    
    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """
        Record a value in a histogram.
        
        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags for the metric
        """
        with self._lock:
            bucket = self._histograms[name]
            bucket.count += 1
            bucket.sum += value
            bucket.min = min(bucket.min, value)
            bucket.max = max(bucket.max, value)
            self._add_sample(name, value, MetricType.HISTOGRAM, tags or {})
    
    def start_timer(self, name: str) -> TimerContext:
        """
        Start a timer for a metric.
        
        Args:
            name: Metric name
            
        Returns:
            TimerContext that will record the elapsed time when exited
        """
        return TimerContext(self, name)
    
    def record_timer(self, name: str, duration_seconds: float, tags: dict[str, str] | None = None) -> None:
        """
        Record a timer value.
        
        Args:
            name: Metric name
            duration_seconds: Duration in seconds
            tags: Optional tags for the metric
        """
        with self._lock:
            self._timers[name].append(duration_seconds)
            # Keep only last 1000 timer samples per name
            if len(self._timers[name]) > 1000:
                self._timers[name] = self._timers[name][-1000:]
            self._add_sample(name, duration_seconds, MetricType.TIMER, tags or {})
    
    def get_counter(self, name: str) -> float:
        """Get the current value of a counter."""
        with self._lock:
            return self._counters.get(name, 0.0)
    
    def get_gauge(self, name: str) -> float:
        """Get the current value of a gauge."""
        with self._lock:
            return self._gauges.get(name, 0.0)
    
    def get_histogram(self, name: str) -> dict[str, Any]:
        """Get histogram statistics."""
        with self._lock:
            bucket = self._histograms.get(name)
            if not bucket or bucket.count == 0:
                return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
            
            return {
                "count": bucket.count,
                "sum": bucket.sum,
                "min": bucket.min,
                "max": bucket.max,
                "avg": bucket.sum / bucket.count,
            }
    
    def get_timer_stats(self, name: str) -> dict[str, Any]:
        """Get timer statistics."""
        with self._lock:
            times = self._timers.get(name, [])
            if not times:
                return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
            
            sorted_times = sorted(times)
            count = len(sorted_times)
            
            return {
                "count": count,
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / count,
                "p50": sorted_times[int(count * 0.5)] if count > 0 else 0.0,
                "p95": sorted_times[int(count * 0.95)] if count > 0 else 0.0,
                "p99": sorted_times[int(count * 0.99)] if count > 0 else 0.0,
            }
    
    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get all current metrics.
        
        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram(name)
                    for name in self._histograms
                },
                "timers": {
                    name: self.get_timer_stats(name)
                    for name in self._timers
                },
            }
    
    def _add_sample(self, name: str, value: float, metric_type: MetricType, tags: dict[str, str]) -> None:
        """Add a sample to the samples list."""
        self._samples.append(MetricValue(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags,
            metric_type=metric_type
        ))
        
        # Keep only recent samples to prevent memory issues
        if len(self._samples) > self.max_samples:
            self._samples = self._samples[-(self.max_samples // 2):]
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._samples.clear()
            self.init_builtin_metrics()
    
    def export_to_file(self, path: Path) -> None:
        """Export metrics to a JSON file."""
        metrics = self.get_all_metrics()
        metrics["exported_at"] = time.time()
        path.write_text(json.dumps(metrics, indent=2), encoding="utf8")
    
    def get_recent_samples(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent metric samples."""
        with self._lock:
            samples = self._samples[-limit:] if self._samples else []
            return [
                {
                    "name": s.name,
                    "value": s.value,
                    "timestamp": s.timestamp,
                    "tags": s.tags,
                    "type": s.metric_type.value,
                }
                for s in samples
            ]


class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: dict[str, str] | None = None) -> None:
        self.collector = collector
        self.name = name
        self.tags = tags or {}
        self.start_time: float | None = None
    
    def __enter__(self) -> TimerContext:
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.record_timer(self.name, duration, self.tags)


# Global metrics instance
_global_metrics: MetricsCollector | None = None
_metrics_lock = Lock()


def get_metrics() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _global_metrics
    
    if _global_metrics is None:
        with _metrics_lock:
            if _global_metrics is None:
                _global_metrics = MetricsCollector()
    
    return _global_metrics


def reset_metrics() -> None:
    """Reset the global metrics collector."""
    global _global_metrics
    with _metrics_lock:
        if _global_metrics is not None:
            _global_metrics.reset()