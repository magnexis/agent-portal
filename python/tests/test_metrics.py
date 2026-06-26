"""Tests for metrics and telemetry module."""

from __future__ import annotations

import time
import unittest
import tempfile
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_portal.metrics import (
    MetricsCollector,
    TimerContext,
    MetricType,
    get_metrics,
    reset_metrics,
)


class MetricsCollectorTests(unittest.TestCase):
    """Test cases for the MetricsCollector class."""

    def setUp(self) -> None:
        """Reset metrics before each test."""
        reset_metrics()
        self.metrics = MetricsCollector()

    def test_increment_counter(self) -> None:
        self.metrics.increment("test.counter", 5.0)
        self.assertEqual(self.metrics.get_counter("test.counter"), 5.0)
        
        self.metrics.increment("test.counter", 3.0)
        self.assertEqual(self.metrics.get_counter("test.counter"), 8.0)

    def test_set_gauge(self) -> None:
        self.metrics.set_gauge("test.gauge", 42.0)
        self.assertEqual(self.metrics.get_gauge("test.gauge"), 42.0)
        
        self.metrics.set_gauge("test.gauge", 99.0)
        self.assertEqual(self.metrics.get_gauge("test.gauge"), 99.0)

    def test_record_histogram(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for value in values:
            self.metrics.record_histogram("test.histogram", value)
        
        stats = self.metrics.get_histogram("test.histogram")
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["sum"], 15.0)
        self.assertEqual(stats["min"], 1.0)
        self.assertEqual(stats["max"], 5.0)
        self.assertEqual(stats["avg"], 3.0)

    def test_record_timer(self) -> None:
        durations = [0.1, 0.2, 0.3, 0.4, 0.5]
        for duration in durations:
            self.metrics.record_timer("test.timer", duration)
        
        stats = self.metrics.get_timer_stats("test.timer")
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["min"], 0.1)
        self.assertEqual(stats["max"], 0.5)
        self.assertAlmostEqual(stats["avg"], 0.3, places=2)

    def test_timer_context(self) -> None:
        with self.metrics.start_timer("test.context"):
            time.sleep(0.05)
        
        stats = self.metrics.get_timer_stats("test.context")
        self.assertEqual(stats["count"], 1)
        self.assertGreater(stats["min"], 0.04)
        self.assertLess(stats["max"], 0.15)

    def test_percentiles(self) -> None:
        durations = list(range(100))  # 0 to 99
        for duration in durations:
            self.metrics.record_timer("test.percentiles", float(duration))
        
        stats = self.metrics.get_timer_stats("test.percentiles")
        self.assertEqual(stats["count"], 100)
        self.assertAlmostEqual(stats["p50"], 49.0, places=0)
        self.assertAlmostEqual(stats["p95"], 94.0, places=0)
        self.assertAlmostEqual(stats["p99"], 98.0, places=0)

    def test_get_all_metrics(self) -> None:
        self.metrics.increment("test.counter", 1.0)
        self.metrics.set_gauge("test.gauge", 42.0)
        self.metrics.record_histogram("test.histogram", 5.0)
        
        all_metrics = self.metrics.get_all_metrics()
        self.assertIn("counters", all_metrics)
        self.assertIn("gauges", all_metrics)
        self.assertIn("histograms", all_metrics)
        self.assertIn("timers", all_metrics)
        
        self.assertEqual(all_metrics["counters"]["test.counter"], 1.0)
        self.assertEqual(all_metrics["gauges"]["test.gauge"], 42.0)

    def test_reset(self) -> None:
        self.metrics.increment("test.counter", 100.0)
        self.assertEqual(self.metrics.get_counter("test.counter"), 100.0)
        
        self.metrics.reset()
        self.assertEqual(self.metrics.get_counter("test.counter"), 0.0)

    def test_export_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.metrics.increment("test.counter", 42.0)
            
            export_path = Path(temp_dir) / "metrics.json"
            self.metrics.export_to_file(export_path)
            
            self.assertTrue(export_path.exists())
            
            import json
            content = json.loads(export_path.read_text(encoding="utf8"))
            self.assertIn("counters", content)
            self.assertIn("exported_at", content)

    def test_get_recent_samples(self) -> None:
        self.metrics.increment("test.counter", 1.0)
        self.metrics.set_gauge("test.gauge", 42.0)
        
        samples = self.metrics.get_recent_samples(limit=10)
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0]["name"], "test.counter")
        self.assertEqual(samples[1]["name"], "test.gauge")

    def test_builtin_metrics(self) -> None:
        """Check that built-in metrics are initialized."""
        self.assertIsNotNone(self.metrics.get_counter("actions.total"))
        self.assertIsNotNone(self.metrics.get_counter("actions.completed"))
        self.assertIsNotNone(self.metrics.get_gauge("runtime.uptime_seconds"))

    def test_histogram_empty(self) -> None:
        stats = self.metrics.get_histogram("nonexistent")
        self.assertEqual(stats["count"], 0)
        self.assertEqual(stats["sum"], 0.0)

    def test_timer_empty(self) -> None:
        stats = self.metrics.get_timer_stats("nonexistent")
        self.assertEqual(stats["count"], 0)

    def test_max_samples_limit(self) -> None:
        """Test that samples don't grow beyond max_samples."""
        small_metrics = MetricsCollector(max_samples=100)
        
        for i in range(200):
            small_metrics.increment("test", 1.0)
        
        samples = small_metrics.get_recent_samples(limit=1000)
        self.assertLessEqual(len(samples), 100)


class GlobalMetricsTests(unittest.TestCase):
    """Test cases for global metrics functions."""

    def test_get_metrics_singleton(self) -> None:
        reset_metrics()
        m1 = get_metrics()
        m2 = get_metrics()
        self.assertIs(m1, m2)

    def test_reset_metrics(self) -> None:
        reset_metrics()
        metrics = get_metrics()
        
        metrics.increment("test", 100.0)
        self.assertEqual(metrics.get_counter("test"), 100.0)
        
        reset_metrics()
        new_metrics = get_metrics()
        self.assertEqual(new_metrics.get_counter("test"), 0.0)


if __name__ == "__main__":
    unittest.main()