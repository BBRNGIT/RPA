"""
RPA Self-Improvement Metrics API

Provides REST endpoints for self-improvement metrics and monitoring.
Used by the Next.js dashboard for visualization.

Ticket: SI-006
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SIMetricsAPI:
    """
    API for self-improvement metrics.
    
    Provides endpoints for:
    - System health metrics
    - Cycle statistics
    - Pattern mutation history
    - Gap closure progress
    - Confidence trends
    - Learning velocity
    
    Usage:
        api = SIMetricsAPI(storage_path)
        
        # Get dashboard data
        health = api.get_system_health()
        cycles = api.get_cycle_stats()
        trends = api.get_confidence_trends()
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        orchestrator: Any = None
    ):
        """
        Initialize the SI Metrics API.
        
        Args:
            storage_path: Path to self-improvement state storage
            orchestrator: SelfImprovementOrchestrator instance (optional, lazy-loaded)
        """
        self.storage_path = storage_path or Path.home() / ".rpa" / "memory"
        self._orchestrator = orchestrator
        self._metrics_cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 60  # Cache for 1 minute
    
    @property
    def orchestrator(self):
        """Lazy-load the orchestrator if needed."""
        if self._orchestrator is None:
            try:
                from rpa.training.self_improvement import SelfImprovementOrchestrator
                self._orchestrator = SelfImprovementOrchestrator(
                    storage_path=self.storage_path
                )
            except Exception as e:
                logger.warning(f"Could not load orchestrator: {e}")
        return self._orchestrator
    
    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid."""
        if self._cache_timestamp is None:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl_seconds
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if valid."""
        if self._is_cache_valid() and key in self._metrics_cache:
            return self._metrics_cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set cached value."""
        self._metrics_cache[key] = value
        self._cache_timestamp = datetime.now()
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive dashboard summary.
        
        Returns:
            Dict with all dashboard metrics in one call
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "health": self.get_system_health(),
            "cycle_stats": self.get_cycle_stats(),
            "recent_cycles": self.get_recent_cycles(limit=10),
            "mutation_stats": self.get_mutation_stats(),
            "gap_stats": self.get_gap_stats(),
            "trends": self.get_confidence_trends(),
            "learning_velocity": self.get_learning_velocity(),
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health metrics.
        
        Returns:
            Dict with health metrics including pattern counts and success rates
        """
        cached = self._get_cached("health")
        if cached:
            return cached
        
        health = {
            "status": "unknown",
            "total_patterns": 0,
            "strong_patterns": 0,
            "weak_patterns": 0,
            "deprecated_patterns": 0,
            "avg_pattern_strength": 0.0,
            "avg_confidence": 0.0,
            "pending_mutations": 0,
            "open_gaps": 0,
            "recent_success_rate": 0.0,
            "learning_velocity": 0.0,
            "last_cycle_time": None,
        }
        
        try:
            if self.orchestrator:
                sys_health = self.orchestrator.get_system_health()
                health = {
                    "status": "healthy" if sys_health.avg_confidence >= 0.5 else "degraded",
                    "total_patterns": sys_health.total_patterns,
                    "strong_patterns": sys_health.strong_patterns,
                    "weak_patterns": sys_health.weak_patterns,
                    "deprecated_patterns": sys_health.deprecated_patterns,
                    "avg_pattern_strength": round(sys_health.avg_pattern_strength, 3),
                    "avg_confidence": round(sys_health.avg_confidence, 3),
                    "pending_mutations": sys_health.pending_mutations,
                    "open_gaps": sys_health.open_gaps,
                    "recent_success_rate": round(sys_health.recent_success_rate, 3),
                    "learning_velocity": round(sys_health.learning_velocity, 2),
                    "last_cycle_time": sys_health.last_cycle_time.isoformat() if sys_health.last_cycle_time else None,
                }
        except Exception as e:
            logger.warning(f"Error getting system health: {e}")
            health["status"] = "error"
            health["error"] = str(e)
        
        self._set_cache("health", health)
        return health
    
    def get_cycle_stats(self) -> Dict[str, Any]:
        """
        Get cycle statistics.
        
        Returns:
            Dict with aggregate cycle statistics
        """
        cached = self._get_cached("cycle_stats")
        if cached:
            return cached
        
        stats = {
            "total_cycles": 0,
            "total_patterns_evaluated": 0,
            "total_patterns_reinforced": 0,
            "total_patterns_decayed": 0,
            "total_patterns_mutated": 0,
            "total_successful_mutations": 0,
            "total_gaps_detected": 0,
            "total_gaps_closed": 0,
            "avg_cycle_duration": 0.0,
        }
        
        try:
            if self.orchestrator:
                cycle_stats = self.orchestrator.get_cycle_stats(last_n=100)
                stats = {
                    "total_cycles": cycle_stats.get("total_cycles", 0),
                    "total_patterns_evaluated": cycle_stats.get("total_patterns_evaluated", 0),
                    "total_patterns_reinforced": cycle_stats.get("total_patterns_reinforced", 0),
                    "total_patterns_decayed": cycle_stats.get("total_patterns_decayed", 0),
                    "total_patterns_mutated": cycle_stats.get("total_patterns_mutated", 0),
                    "total_successful_mutations": cycle_stats.get("total_successful_mutations", 0),
                    "total_gaps_detected": cycle_stats.get("total_gaps_detected", 0),
                    "total_gaps_closed": cycle_stats.get("total_gaps_closed", 0),
                    "avg_cycle_duration": round(cycle_stats.get("avg_cycle_duration", 0.0), 3),
                }
        except Exception as e:
            logger.warning(f"Error getting cycle stats: {e}")
            stats["error"] = str(e)
        
        self._set_cache("cycle_stats", stats)
        return stats
    
    def get_recent_cycles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent improvement cycles.
        
        Args:
            limit: Maximum number of cycles to return
            
        Returns:
            List of cycle records
        """
        cycles = []
        
        try:
            if self.orchestrator and hasattr(self.orchestrator, 'cycle_history'):
                for cycle in self.orchestrator.cycle_history[-limit:]:
                    cycles.append(cycle.to_dict())
        except Exception as e:
            logger.warning(f"Error getting recent cycles: {e}")
        
        return cycles
    
    def get_mutation_stats(self) -> Dict[str, Any]:
        """
        Get pattern mutation statistics.
        
        Returns:
            Dict with mutation statistics
        """
        cached = self._get_cached("mutation_stats")
        if cached:
            return cached
        
        stats = {
            "total_mutations": 0,
            "successful_mutations": 0,
            "by_type": {},
            "patterns_versioned": 0,
            "patterns_deprecated": 0,
            "patterns_restored": 0,
            "recent_mutations": [],
        }
        
        try:
            if self.orchestrator and hasattr(self.orchestrator, 'mutator'):
                mutator_stats = self.orchestrator.mutator.get_stats()
                stats = {
                    "total_mutations": mutator_stats.get("total_mutations", 0),
                    "successful_mutations": mutator_stats.get("successful_fixes", 0),
                    "by_type": mutator_stats.get("by_type", {}),
                    "patterns_versioned": mutator_stats.get("patterns_versioned", 0),
                    "patterns_deprecated": mutator_stats.get("patterns_deprecated", 0),
                    "patterns_restored": mutator_stats.get("patterns_restored", 0),
                    "recent_mutations": [
                        m.to_dict() for m in self.orchestrator.mutator.get_mutation_history(limit=5)
                    ],
                }
        except Exception as e:
            logger.warning(f"Error getting mutation stats: {e}")
            stats["error"] = str(e)
        
        self._set_cache("mutation_stats", stats)
        return stats
    
    def get_gap_stats(self) -> Dict[str, Any]:
        """
        Get gap detection and closure statistics.
        
        Returns:
            Dict with gap statistics
        """
        cached = self._get_cached("gap_stats")
        if cached:
            return cached
        
        stats = {
            "total_gaps_detected": 0,
            "total_goals_created": 0,
            "total_goals_completed": 0,
            "pending_goals": 0,
            "in_progress_goals": 0,
            "completed_goals": 0,
            "success_rate": 0.0,
        }
        
        try:
            if self.orchestrator and hasattr(self.orchestrator, 'gap_closure_loop'):
                if self.orchestrator.gap_closure_loop:
                    status = self.orchestrator.gap_closure_loop.get_status()
                    total_attempts = status.get("total_closure_attempts", 0)
                    successful = status.get("successful_closures", 0)
                    
                    stats = {
                        "total_gaps_detected": status.get("total_gaps_detected", 0),
                        "total_goals_created": status.get("total_goals_created", 0),
                        "total_goals_completed": status.get("total_goals_completed", 0),
                        "pending_goals": status.get("pending_goals", 0),
                        "in_progress_goals": status.get("in_progress_goals", 0),
                        "completed_goals": status.get("completed_goals", 0),
                        "success_rate": round(successful / max(1, total_attempts), 3),
                    }
        except Exception as e:
            logger.warning(f"Error getting gap stats: {e}")
            stats["error"] = str(e)
        
        self._set_cache("gap_stats", stats)
        return stats
    
    def get_confidence_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Get confidence trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with trend data
        """
        cached = self._get_cached("trends")
        if cached:
            return cached
        
        trends = {
            "period_days": days,
            "data_points": [],
            "trend_direction": "stable",
            "avg_change_per_day": 0.0,
        }
        
        try:
            if self.orchestrator and hasattr(self.orchestrator, 'cycle_history'):
                history = self.orchestrator.cycle_history
                
                # Sample cycles for trend data
                sample_size = min(days * 3, len(history))  # ~3 cycles per day
                if sample_size > 0:
                    sampled = history[-sample_size:]
                    
                    data_points = []
                    for cycle in sampled:
                        if cycle.end_time:
                            # Calculate cycle success rate
                            total = max(1, cycle.patterns_evaluated)
                            success_rate = cycle.patterns_reinforced / total
                            
                            data_points.append({
                                "timestamp": cycle.end_time.isoformat(),
                                "success_rate": round(success_rate, 3),
                                "patterns_evaluated": cycle.patterns_evaluated,
                                "patterns_reinforced": cycle.patterns_reinforced,
                                "patterns_mutated": cycle.patterns_mutated,
                                "gaps_detected": cycle.gaps_detected,
                                "gaps_closed": cycle.gaps_closed,
                            })
                    
                    trends["data_points"] = data_points
                    
                    # Calculate trend direction
                    if len(data_points) >= 2:
                        first_half = data_points[:len(data_points)//2]
                        second_half = data_points[len(data_points)//2:]
                        
                        first_avg = sum(p["success_rate"] for p in first_half) / max(1, len(first_half))
                        second_avg = sum(p["success_rate"] for p in second_half) / max(1, len(second_half))
                        
                        if second_avg > first_avg + 0.05:
                            trends["trend_direction"] = "improving"
                        elif second_avg < first_avg - 0.05:
                            trends["trend_direction"] = "declining"
                        else:
                            trends["trend_direction"] = "stable"
                        
                        trends["avg_change_per_day"] = round(
                            (second_avg - first_avg) / max(1, days), 4
                        )
        except Exception as e:
            logger.warning(f"Error getting confidence trends: {e}")
            trends["error"] = str(e)
        
        self._set_cache("trends", trends)
        return trends
    
    def get_learning_velocity(self) -> Dict[str, Any]:
        """
        Get learning velocity metrics.
        
        Returns:
            Dict with velocity metrics
        """
        cached = self._get_cached("velocity")
        if cached:
            return cached
        
        velocity = {
            "patterns_per_hour": 0.0,
            "mutations_per_hour": 0.0,
            "gap_closures_per_hour": 0.0,
            "improvement_rate": 0.0,
        }
        
        try:
            if self.orchestrator:
                health = self.orchestrator.get_system_health()
                velocity["patterns_per_hour"] = round(health.learning_velocity, 2)
                
                # Calculate other velocities from cycle history
                if hasattr(self.orchestrator, 'cycle_history'):
                    history = self.orchestrator.cycle_history[-10:]  # Last 10 cycles
                    
                    if history:
                        total_time = sum(c.duration_seconds for c in history)
                        if total_time > 0:
                            hours = total_time / 3600
                            velocity["mutations_per_hour"] = round(
                                sum(c.patterns_mutated for c in history) / max(0.1, hours), 2
                            )
                            velocity["gap_closures_per_hour"] = round(
                                sum(c.gaps_closed for c in history) / max(0.1, hours), 2
                            )
                            velocity["improvement_rate"] = round(
                                sum(c.patterns_reinforced for c in history) / max(0.1, hours), 2
                            )
        except Exception as e:
            logger.warning(f"Error getting learning velocity: {e}")
            velocity["error"] = str(e)
        
        self._set_cache("velocity", velocity)
        return velocity
    
    def get_priorities(self) -> Dict[str, Any]:
        """
        Get learning priorities.
        
        Returns:
            Dict with priority lists
        """
        priorities = {
            "weak_patterns": [],
            "needs_fix": [],
            "problematic": [],
            "needs_attention": [],
            "gaps": [],
        }
        
        try:
            if self.orchestrator:
                priorities = self.orchestrator.get_learning_priorities()
        except Exception as e:
            logger.warning(f"Error getting priorities: {e}")
            priorities["error"] = str(e)
        
        return priorities
    
    def trigger_improvement_cycle(self) -> Dict[str, Any]:
        """
        Manually trigger an improvement cycle.
        
        Returns:
            Dict with cycle results
        """
        result = {
            "success": False,
            "cycle_id": None,
            "message": "",
        }
        
        try:
            if self.orchestrator:
                cycle = self.orchestrator.run_improvement_cycle()
                result = {
                    "success": True,
                    "cycle_id": cycle.cycle_id,
                    "patterns_evaluated": cycle.patterns_evaluated,
                    "patterns_reinforced": cycle.patterns_reinforced,
                    "patterns_decayed": cycle.patterns_decayed,
                    "patterns_mutated": cycle.patterns_mutated,
                    "gaps_detected": cycle.gaps_detected,
                    "gaps_closed": cycle.gaps_closed,
                    "duration_seconds": cycle.duration_seconds,
                    "errors": cycle.errors,
                }
                
                # Invalidate cache
                self._metrics_cache = {}
                self._cache_timestamp = None
            else:
                result["message"] = "Orchestrator not available"
        except Exception as e:
            logger.error(f"Error triggering improvement cycle: {e}")
            result["message"] = str(e)
        
        return result
    
    def to_json(self) -> str:
        """Get all metrics as JSON string."""
        return json.dumps(self.get_dashboard_summary(), indent=2, default=str)


# Flask endpoint handlers
def create_si_metrics_endpoints(app, metrics_api: SIMetricsAPI):
    """
    Add SI metrics endpoints to a Flask app.
    
    Args:
        app: Flask application
        metrics_api: SIMetricsAPI instance
    """
    try:
        from flask import jsonify, request
        
        @app.route("/si/dashboard", methods=["GET"])
        def si_dashboard():
            """Get complete dashboard data."""
            return jsonify(metrics_api.get_dashboard_summary())
        
        @app.route("/si/health", methods=["GET"])
        def si_health():
            """Get system health."""
            return jsonify(metrics_api.get_system_health())
        
        @app.route("/si/cycles", methods=["GET"])
        def si_cycles():
            """Get cycle statistics."""
            limit = request.args.get("limit", 10, type=int)
            return jsonify({
                "stats": metrics_api.get_cycle_stats(),
                "recent": metrics_api.get_recent_cycles(limit)
            })
        
        @app.route("/si/mutations", methods=["GET"])
        def si_mutations():
            """Get mutation statistics."""
            return jsonify(metrics_api.get_mutation_stats())
        
        @app.route("/si/gaps", methods=["GET"])
        def si_gaps():
            """Get gap statistics."""
            return jsonify(metrics_api.get_gap_stats())
        
        @app.route("/si/trends", methods=["GET"])
        def si_trends():
            """Get confidence trends."""
            days = request.args.get("days", 7, type=int)
            return jsonify(metrics_api.get_confidence_trends(days))
        
        @app.route("/si/velocity", methods=["GET"])
        def si_velocity():
            """Get learning velocity."""
            return jsonify(metrics_api.get_learning_velocity())
        
        @app.route("/si/priorities", methods=["GET"])
        def si_priorities():
            """Get learning priorities."""
            return jsonify(metrics_api.get_priorities())
        
        @app.route("/si/trigger", methods=["POST"])
        def si_trigger():
            """Trigger improvement cycle."""
            return jsonify(metrics_api.trigger_improvement_cycle())
        
        logger.info("SI metrics endpoints added to Flask app")
        
    except ImportError:
        logger.warning("Flask not available, endpoints not added")


def add_si_endpoints_to_simple_handler(handler_class, metrics_api: SIMetricsAPI):
    """
    Add SI metrics endpoints to simple HTTP handler.
    
    Args:
        handler_class: SimpleHTTPRequestHandler class
        metrics_api: SIMetricsAPI instance
    """
    original_do_get = handler_class.do_GET
    original_do_post = handler_class.do_POST
    
    def new_do_get(self):
        path = self.path.split('?')[0]
        
        if path == "/si/dashboard":
            self._send_json_response(metrics_api.get_dashboard_summary())
            return
        elif path == "/si/health":
            self._send_json_response(metrics_api.get_system_health())
            return
        elif path == "/si/cycles":
            self._send_json_response({
                "stats": metrics_api.get_cycle_stats(),
                "recent": metrics_api.get_recent_cycles(10)
            })
            return
        elif path == "/si/mutations":
            self._send_json_response(metrics_api.get_mutation_stats())
            return
        elif path == "/si/gaps":
            self._send_json_response(metrics_api.get_gap_stats())
            return
        elif path == "/si/trends":
            self._send_json_response(metrics_api.get_confidence_trends(7))
            return
        elif path == "/si/velocity":
            self._send_json_response(metrics_api.get_learning_velocity())
            return
        elif path == "/si/priorities":
            self._send_json_response(metrics_api.get_priorities())
            return
        
        original_do_get(self)
    
    def new_do_post(self):
        path = self.path.split('?')[0]
        
        if path == "/si/trigger":
            self._send_json_response(metrics_api.trigger_improvement_cycle())
            return
        
        original_do_post(self)
    
    handler_class.do_GET = new_do_get
    handler_class.do_POST = new_do_post
    
    logger.info("SI metrics endpoints added to simple HTTP handler")
