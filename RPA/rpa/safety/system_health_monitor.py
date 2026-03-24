"""
System Health Monitor - Track system health metrics.

This module provides comprehensive health monitoring for the RPA system,
tracking various metrics and generating health reports.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import time
import threading
from collections import defaultdict


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"      # All systems operational
    DEGRADED = "degraded"    # Some issues, but operational
    UNHEALTHY = "unhealthy"  # Critical issues detected
    UNKNOWN = "unknown"      # Unable to determine status


@dataclass
class HealthMetric:
    """A single health metric measurement."""
    metric_id: str
    name: str
    value: Any
    unit: str
    status: HealthStatus
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "details": self.details,
        }


@dataclass
class HealthReport:
    """A comprehensive health report."""
    report_id: str
    overall_status: HealthStatus
    metrics: List[HealthMetric]
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    uptime_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "report_id": self.report_id,
            "overall_status": self.overall_status.value,
            "metrics": [m.to_dict() for m in self.metrics],
            "issues": self.issues,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at,
            "uptime_seconds": self.uptime_seconds,
        }


class SystemHealthMonitor:
    """
    Monitor system health and generate reports.

    This class provides:
    - Memory usage monitoring
    - Pattern count tracking
    - Error rate tracking
    - Performance metrics
    - Custom metric collection
    """

    # Default thresholds
    DEFAULT_THRESHOLDS = {
        "memory_usage_percent": {"warning": 80, "critical": 95},
        "pattern_count": {"warning": 9000, "critical": 10000},
        "error_rate_percent": {"warning": 5, "critical": 10},
        "consolidation_rate_percent": {"warning": 50, "critical": 30},
        "inquiry_backlog": {"warning": 100, "critical": 500},
        "response_time_ms": {"warning": 1000, "critical": 5000},
    }

    def __init__(self, thresholds: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Initialize the health monitor.

        Args:
            thresholds: Custom thresholds for metrics.
        """
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        self._start_time = datetime.now()
        self._metrics_history: Dict[str, List[HealthMetric]] = defaultdict(list)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._operation_counts: Dict[str, int] = defaultdict(int)
        self._custom_collectors: Dict[str, Callable[[], Any]] = {}
        self._lock = threading.Lock()
        self._monitoring_stats: Dict[str, int] = {
            "reports_generated": 0,
            "issues_detected": 0,
            "alerts_sent": 0,
        }

    def collect_memory_metrics(self) -> HealthMetric:
        """
        Collect memory-related metrics.

        Returns:
            HealthMetric with memory usage information.
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            value = memory_info.rss / (1024 * 1024)  # MB
            memory_percent = process.memory_percent()

            status = HealthStatus.HEALTHY
            if memory_percent >= self.thresholds["memory_usage_percent"]["critical"]:
                status = HealthStatus.UNHEALTHY
            elif memory_percent >= self.thresholds["memory_usage_percent"]["warning"]:
                status = HealthStatus.DEGRADED

            return HealthMetric(
                metric_id=f"mem_{int(time.time())}",
                name="Memory Usage",
                value=round(value, 2),
                unit="MB",
                status=status,
                threshold_warning=self.thresholds["memory_usage_percent"]["warning"],
                threshold_critical=self.thresholds["memory_usage_percent"]["critical"],
                details={
                    "rss_mb": round(value, 2),
                    "percent": round(memory_percent, 2),
                },
            )
        except ImportError:
            # psutil not available
            return HealthMetric(
                metric_id=f"mem_{int(time.time())}",
                name="Memory Usage",
                value=0,
                unit="MB",
                status=HealthStatus.UNKNOWN,
                details={"error": "psutil not available"},
            )

    def collect_pattern_metrics(
        self,
        stm_count: int = 0,
        ltm_count: int = 0,
        episodic_count: int = 0,
    ) -> HealthMetric:
        """
        Collect pattern-related metrics.

        Args:
            stm_count: Number of patterns in short-term memory.
            ltm_count: Number of patterns in long-term memory.
            episodic_count: Number of episodic memory entries.

        Returns:
            HealthMetric with pattern count information.
        """
        total_patterns = stm_count + ltm_count + episodic_count

        status = HealthStatus.HEALTHY
        if total_patterns >= self.thresholds["pattern_count"]["critical"]:
            status = HealthStatus.UNHEALTHY
        elif total_patterns >= self.thresholds["pattern_count"]["warning"]:
            status = HealthStatus.DEGRADED

        return HealthMetric(
            metric_id=f"pat_{int(time.time())}",
            name="Pattern Count",
            value=total_patterns,
            unit="patterns",
            status=status,
            threshold_warning=self.thresholds["pattern_count"]["warning"],
            threshold_critical=self.thresholds["pattern_count"]["critical"],
            details={
                "stm_count": stm_count,
                "ltm_count": ltm_count,
                "episodic_count": episodic_count,
            },
        )

    def collect_error_metrics(self) -> HealthMetric:
        """
        Collect error-related metrics.

        Returns:
            HealthMetric with error rate information.
        """
        total_ops = sum(self._operation_counts.values()) or 1
        total_errors = sum(self._error_counts.values()) or 0
        error_rate = (total_errors / total_ops) * 100

        status = HealthStatus.HEALTHY
        if error_rate >= self.thresholds["error_rate_percent"]["critical"]:
            status = HealthStatus.UNHEALTHY
        elif error_rate >= self.thresholds["error_rate_percent"]["warning"]:
            status = HealthStatus.DEGRADED

        return HealthMetric(
            metric_id=f"err_{int(time.time())}",
            name="Error Rate",
            value=round(error_rate, 2),
            unit="percent",
            status=status,
            threshold_warning=self.thresholds["error_rate_percent"]["warning"],
            threshold_critical=self.thresholds["error_rate_percent"]["critical"],
            details={
                "total_operations": total_ops,
                "total_errors": total_errors,
                "errors_by_type": dict(self._error_counts),
            },
        )

    def collect_consolidation_metrics(
        self,
        total_attempted: int = 0,
        total_consolidated: int = 0,
    ) -> HealthMetric:
        """
        Collect consolidation rate metrics.

        Args:
            total_attempted: Total consolidation attempts.
            total_consolidated: Successfully consolidated patterns.

        Returns:
            HealthMetric with consolidation rate information.
        """
        rate = (total_consolidated / total_attempted * 100) if total_attempted > 0 else 100

        status = HealthStatus.HEALTHY
        if rate < self.thresholds["consolidation_rate_percent"]["critical"]:
            status = HealthStatus.UNHEALTHY
        elif rate < self.thresholds["consolidation_rate_percent"]["warning"]:
            status = HealthStatus.DEGRADED

        return HealthMetric(
            metric_id=f"cons_{int(time.time())}",
            name="Consolidation Rate",
            value=round(rate, 2),
            unit="percent",
            status=status,
            threshold_warning=self.thresholds["consolidation_rate_percent"]["warning"],
            threshold_critical=self.thresholds["consolidation_rate_percent"]["critical"],
            details={
                "total_attempted": total_attempted,
                "total_consolidated": total_consolidated,
            },
        )

    def collect_inquiry_metrics(self, pending_inquiries: int = 0) -> HealthMetric:
        """
        Collect inquiry backlog metrics.

        Args:
            pending_inquiries: Number of unanswered inquiries.

        Returns:
            HealthMetric with inquiry backlog information.
        """
        status = HealthStatus.HEALTHY
        if pending_inquiries >= self.thresholds["inquiry_backlog"]["critical"]:
            status = HealthStatus.UNHEALTHY
        elif pending_inquiries >= self.thresholds["inquiry_backlog"]["warning"]:
            status = HealthStatus.DEGRADED

        return HealthMetric(
            metric_id=f"inq_{int(time.time())}",
            name="Inquiry Backlog",
            value=pending_inquiries,
            unit="inquiries",
            status=status,
            threshold_warning=self.thresholds["inquiry_backlog"]["warning"],
            threshold_critical=self.thresholds["inquiry_backlog"]["critical"],
        )

    def collect_performance_metrics(self, avg_response_time_ms: float = 0) -> HealthMetric:
        """
        Collect performance metrics.

        Args:
            avg_response_time_ms: Average response time in milliseconds.

        Returns:
            HealthMetric with performance information.
        """
        status = HealthStatus.HEALTHY
        if avg_response_time_ms >= self.thresholds["response_time_ms"]["critical"]:
            status = HealthStatus.UNHEALTHY
        elif avg_response_time_ms >= self.thresholds["response_time_ms"]["warning"]:
            status = HealthStatus.DEGRADED

        return HealthMetric(
            metric_id=f"perf_{int(time.time())}",
            name="Response Time",
            value=round(avg_response_time_ms, 2),
            unit="ms",
            status=status,
            threshold_warning=self.thresholds["response_time_ms"]["warning"],
            threshold_critical=self.thresholds["response_time_ms"]["critical"],
        )

    def register_custom_collector(
        self,
        metric_name: str,
        collector: Callable[[], Any],
    ) -> None:
        """
        Register a custom metric collector.

        Args:
            metric_name: Name of the metric.
            collector: Function that returns the metric value.
        """
        self._custom_collectors[metric_name] = collector

    def unregister_custom_collector(self, metric_name: str) -> bool:
        """Unregister a custom metric collector."""
        if metric_name in self._custom_collectors:
            del self._custom_collectors[metric_name]
            return True
        return False

    def collect_custom_metrics(self) -> List[HealthMetric]:
        """Collect all custom metrics."""
        metrics = []
        for name, collector in self._custom_collectors.items():
            try:
                value = collector()
                metrics.append(HealthMetric(
                    metric_id=f"custom_{name}_{int(time.time())}",
                    name=name,
                    value=value,
                    unit="custom",
                    status=HealthStatus.HEALTHY,
                ))
            except Exception as e:
                metrics.append(HealthMetric(
                    metric_id=f"custom_{name}_{int(time.time())}",
                    name=name,
                    value=None,
                    unit="custom",
                    status=HealthStatus.UNKNOWN,
                    details={"error": str(e)},
                ))
        return metrics

    def record_operation(self, operation: str, count: int = 1) -> None:
        """Record an operation for metrics."""
        with self._lock:
            self._operation_counts[operation] += count

    def record_error(self, error_type: str, count: int = 1) -> None:
        """Record an error for metrics."""
        with self._lock:
            self._error_counts[error_type] += count

    def generate_report(
        self,
        stm_count: int = 0,
        ltm_count: int = 0,
        episodic_count: int = 0,
        pending_inquiries: int = 0,
        consolidation_attempted: int = 0,
        consolidation_success: int = 0,
        avg_response_time_ms: float = 0,
    ) -> HealthReport:
        """
        Generate a comprehensive health report.

        Returns:
            HealthReport with all collected metrics.
        """
        with self._lock:
            metrics = []

            # Collect standard metrics
            metrics.append(self.collect_memory_metrics())
            metrics.append(self.collect_pattern_metrics(stm_count, ltm_count, episodic_count))
            metrics.append(self.collect_error_metrics())
            metrics.append(self.collect_consolidation_metrics(
                consolidation_attempted, consolidation_success
            ))
            metrics.append(self.collect_inquiry_metrics(pending_inquiries))
            metrics.append(self.collect_performance_metrics(avg_response_time_ms))

            # Collect custom metrics
            metrics.extend(self.collect_custom_metrics())

            # Store metrics in history
            for metric in metrics:
                self._metrics_history[metric.name].append(metric)

            # Determine overall status
            overall_status = HealthStatus.HEALTHY
            for metric in metrics:
                if metric.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                    break
                elif metric.status == HealthStatus.DEGRADED:
                    overall_status = HealthStatus.DEGRADED

            # Identify issues
            issues = []
            for metric in metrics:
                if metric.status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED):
                    issues.append({
                        "metric": metric.name,
                        "status": metric.status.value,
                        "value": metric.value,
                        "unit": metric.unit,
                    })

            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, issues)

            # Calculate uptime
            uptime = (datetime.now() - self._start_time).total_seconds()

            # Update stats
            self._monitoring_stats["reports_generated"] += 1
            self._monitoring_stats["issues_detected"] += len(issues)

            return HealthReport(
                report_id=f"report_{int(time.time())}",
                overall_status=overall_status,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                uptime_seconds=uptime,
            )

    def _generate_recommendations(
        self,
        metrics: List[HealthMetric],
        issues: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []

        if not issues:
            recommendations.append("All systems are operating normally.")
            return recommendations

        for issue in issues:
            metric_name = issue["metric"]

            if metric_name == "Memory Usage":
                recommendations.append(
                    "Consider reducing pattern cache size or running garbage collection."
                )
            elif metric_name == "Pattern Count":
                recommendations.append(
                    "Pattern storage approaching limits. Consider archiving old patterns."
                )
            elif metric_name == "Error Rate":
                recommendations.append(
                    "High error rate detected. Review recent changes and error logs."
                )
            elif metric_name == "Consolidation Rate":
                recommendations.append(
                    "Low consolidation rate. Review pattern validation criteria."
                )
            elif metric_name == "Inquiry Backlog":
                recommendations.append(
                    "Large inquiry backlog. Consider prioritizing or auto-resolving inquiries."
                )
            elif metric_name == "Response Time":
                recommendations.append(
                    "Slow response times. Consider performance optimization or scaling."
                )

        return recommendations

    def get_metric_history(self, metric_name: str, limit: int = 100) -> List[HealthMetric]:
        """Get historical data for a metric."""
        history = self._metrics_history.get(metric_name, [])
        return history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            **self._monitoring_stats,
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
            "custom_collectors": len(self._custom_collectors),
            "metrics_tracked": len(self._metrics_history),
        }

    def reset_stats(self) -> None:
        """Reset monitoring statistics."""
        with self._lock:
            self._monitoring_stats = {
                "reports_generated": 0,
                "issues_detected": 0,
                "alerts_sent": 0,
            }
            self._error_counts.clear()
            self._operation_counts.clear()
            self._metrics_history.clear()

    def set_threshold(
        self,
        metric_name: str,
        warning: float,
        critical: float,
    ) -> None:
        """Set custom thresholds for a metric."""
        self.thresholds[metric_name] = {
            "warning": warning,
            "critical": critical,
        }
