"""
Workflow Configuration Module for GitHub Actions Integration.

Provides workflow management, scheduling configuration, and status tracking
for automated learning jobs and CI/CD pipelines.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Types of GitHub Actions workflows."""
    CI = "ci"
    VOCABULARY_REVIEW = "vocabulary_review"
    DAILY_REPORT = "daily_report"
    MEMORY_CLEANUP = "memory_cleanup"
    LEARNING_SESSION = "learning_session"
    CURRICULUM_UPDATE = "curriculum_update"


class WorkflowStatus(str, Enum):
    """Workflow run status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class ScheduleType(str, Enum):
    """Types of workflow schedules."""
    INTERVAL = "interval"  # Every X hours
    CRON = "cron"          # Cron expression
    MANUAL = "manual"      # Manual trigger only
    EVENT = "event"        # Event-triggered (push, PR)


@dataclass
class WorkflowSchedule:
    """Workflow schedule configuration."""
    schedule_id: str
    workflow_type: WorkflowType
    schedule_type: ScheduleType
    cron_expression: Optional[str] = None
    interval_hours: Optional[int] = None
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    # Job parameters
    domain: str = "english"
    limit: int = 20
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schedule_id": self.schedule_id,
            "workflow_type": self.workflow_type.value,
            "schedule_type": self.schedule_type.value,
            "cron_expression": self.cron_expression,
            "interval_hours": self.interval_hours,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "domain": self.domain,
            "limit": self.limit,
            "parameters": self.parameters,
        }


@dataclass
class WorkflowRun:
    """Record of a workflow execution."""
    run_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Results
    success: bool = False
    items_processed: int = 0
    errors: List[str] = field(default_factory=list)
    
    # Metrics
    duration_seconds: float = 0.0
    
    # GitHub Actions specific
    github_run_id: Optional[str] = None
    github_run_number: Optional[int] = None
    github_actor: Optional[str] = None
    
    # Output
    output: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "workflow_type": self.workflow_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success": self.success,
            "items_processed": self.items_processed,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
            "github_run_id": self.github_run_id,
            "github_run_number": self.github_run_number,
            "github_actor": self.github_actor,
            "output": self.output,
        }


@dataclass
class WorkflowConfig:
    """Complete workflow configuration."""
    config_id: str
    name: str
    description: str
    enabled: bool = True
    
    # Schedules
    schedules: List[WorkflowSchedule] = field(default_factory=list)
    
    # Settings
    max_concurrent_runs: int = 3
    retry_on_failure: bool = True
    retry_count: int = 2
    timeout_minutes: int = 30
    
    # Notifications
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_channels: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "schedules": [s.to_dict() for s in self.schedules],
            "max_concurrent_runs": self.max_concurrent_runs,
            "retry_on_failure": self.retry_on_failure,
            "retry_count": self.retry_count,
            "timeout_minutes": self.timeout_minutes,
            "notify_on_success": self.notify_on_success,
            "notify_on_failure": self.notify_on_failure,
            "notification_channels": self.notification_channels,
        }


class WorkflowManager:
    """
    Manager for GitHub Actions workflow integration.
    
    Handles workflow configuration, scheduling, and status tracking
    for automated learning jobs.
    """
    
    # Default schedules
    DEFAULT_SCHEDULES: Dict[str, WorkflowSchedule] = {
        "vocab_review_6h": WorkflowSchedule(
            schedule_id="vocab_review_6h",
            workflow_type=WorkflowType.VOCABULARY_REVIEW,
            schedule_type=ScheduleType.CRON,
            cron_expression="0 */6 * * *",  # Every 6 hours
            domain="english",
            limit=50,
        ),
        "daily_report": WorkflowSchedule(
            schedule_id="daily_report",
            workflow_type=WorkflowType.DAILY_REPORT,
            schedule_type=ScheduleType.CRON,
            cron_expression="0 8 * * *",  # Daily at 8 AM UTC
        ),
        "weekly_cleanup": WorkflowSchedule(
            schedule_id="weekly_cleanup",
            workflow_type=WorkflowType.MEMORY_CLEANUP,
            schedule_type=ScheduleType.CRON,
            cron_expression="0 2 * * 0",  # Weekly on Sunday at 2 AM UTC
        ),
    }
    
    def __init__(self):
        """Initialize workflow manager."""
        self.schedules: Dict[str, WorkflowSchedule] = dict(self.DEFAULT_SCHEDULES)
        self.runs: Dict[str, WorkflowRun] = {}
        self.configs: Dict[str, WorkflowConfig] = {}
        
        # Initialize default config
        self._init_default_configs()
        
        logger.info("WorkflowManager initialized")
    
    def _init_default_configs(self):
        """Initialize default workflow configurations."""
        # Learning jobs config
        learning_config = WorkflowConfig(
            config_id="learning_jobs",
            name="RPA Learning Jobs",
            description="Automated vocabulary review and learning sessions",
            schedules=list(self.schedules.values()),
            max_concurrent_runs=3,
            retry_on_failure=True,
            retry_count=2,
            timeout_minutes=30,
        )
        self.configs["learning_jobs"] = learning_config
        
        # CI config
        ci_config = WorkflowConfig(
            config_id="ci_pipeline",
            name="RPA CI Pipeline",
            description="Continuous integration tests and checks",
            enabled=True,
            max_concurrent_runs=1,
            retry_on_failure=False,
            timeout_minutes=60,
        )
        self.configs["ci_pipeline"] = ci_config
    
    # ========================================================================
    # SCHEDULE MANAGEMENT
    # ========================================================================
    
    def get_schedule(self, schedule_id: str) -> Optional[WorkflowSchedule]:
        """Get a schedule by ID."""
        return self.schedules.get(schedule_id)
    
    def list_schedules(
        self,
        workflow_type: Optional[WorkflowType] = None,
        enabled_only: bool = False
    ) -> List[WorkflowSchedule]:
        """List schedules, optionally filtered."""
        schedules = list(self.schedules.values())
        
        if workflow_type:
            schedules = [s for s in schedules if s.workflow_type == workflow_type]
        
        if enabled_only:
            schedules = [s for s in schedules if s.enabled]
        
        return schedules
    
    def add_schedule(self, schedule: WorkflowSchedule) -> WorkflowSchedule:
        """Add or update a schedule."""
        self.schedules[schedule.schedule_id] = schedule
        logger.info(f"Added/updated schedule: {schedule.schedule_id}")
        return schedule
    
    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a schedule."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            logger.info(f"Removed schedule: {schedule_id}")
            return True
        return False
    
    def toggle_schedule(self, schedule_id: str, enabled: bool) -> Optional[WorkflowSchedule]:
        """Enable or disable a schedule."""
        schedule = self.schedules.get(schedule_id)
        if schedule:
            schedule.enabled = enabled
            logger.info(f"Schedule {schedule_id} {'enabled' if enabled else 'disabled'}")
            return schedule
        return None
    
    # ========================================================================
    # RUN TRACKING
    # ========================================================================
    
    def create_run(
        self,
        workflow_type: WorkflowType,
        github_run_id: Optional[str] = None,
        github_run_number: Optional[int] = None,
        github_actor: Optional[str] = None,
    ) -> WorkflowRun:
        """Create a new workflow run record."""
        import uuid
        
        run = WorkflowRun(
            run_id=str(uuid.uuid4()),
            workflow_type=workflow_type,
            status=WorkflowStatus.PENDING,
            started_at=datetime.now(),
            github_run_id=github_run_id,
            github_run_number=github_run_number,
            github_actor=github_actor,
        )
        
        self.runs[run.run_id] = run
        logger.info(f"Created workflow run: {run.run_id} ({workflow_type.value})")
        
        return run
    
    def start_run(self, run_id: str) -> Optional[WorkflowRun]:
        """Mark a run as started."""
        run = self.runs.get(run_id)
        if run:
            run.status = WorkflowStatus.RUNNING
            run.started_at = datetime.now()
            logger.info(f"Started workflow run: {run_id}")
        return run
    
    def complete_run(
        self,
        run_id: str,
        success: bool,
        items_processed: int = 0,
        errors: Optional[List[str]] = None,
        output: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkflowRun]:
        """Mark a run as completed."""
        run = self.runs.get(run_id)
        if run:
            run.completed_at = datetime.now()
            run.status = WorkflowStatus.SUCCESS if success else WorkflowStatus.FAILURE
            run.success = success
            run.items_processed = items_processed
            run.errors = errors or []
            run.output = output or {}
            run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
            
            # Update last_run for schedule
            for schedule in self.schedules.values():
                if schedule.workflow_type == run.workflow_type:
                    schedule.last_run = run.completed_at
            
            logger.info(f"Completed workflow run: {run_id} (success={success})")
        return run
    
    def fail_run(
        self,
        run_id: str,
        errors: List[str],
    ) -> Optional[WorkflowRun]:
        """Mark a run as failed."""
        return self.complete_run(run_id, success=False, errors=errors)
    
    def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        """Get a run by ID."""
        return self.runs.get(run_id)
    
    def list_runs(
        self,
        workflow_type: Optional[WorkflowType] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
    ) -> List[WorkflowRun]:
        """List runs, optionally filtered."""
        runs = list(self.runs.values())
        
        if workflow_type:
            runs = [r for r in runs if r.workflow_type == workflow_type]
        
        if status:
            runs = [r for r in runs if r.status == status]
        
        # Sort by started_at descending
        runs.sort(key=lambda r: r.started_at, reverse=True)
        
        return runs[:limit]
    
    def get_recent_runs(self, hours: int = 24) -> List[WorkflowRun]:
        """Get runs from the last N hours."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=hours)
        return [r for r in self.runs.values() if r.started_at >= cutoff]
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def get_config(self, config_id: str) -> Optional[WorkflowConfig]:
        """Get a configuration by ID."""
        return self.configs.get(config_id)
    
    def list_configs(self) -> List[WorkflowConfig]:
        """List all configurations."""
        return list(self.configs.values())
    
    def update_config(self, config: WorkflowConfig) -> WorkflowConfig:
        """Add or update a configuration."""
        self.configs[config.config_id] = config
        logger.info(f"Updated config: {config.config_id}")
        return config
    
    # ========================================================================
    # STATUS & REPORTING
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall workflow system status."""
        recent_runs = self.get_recent_runs(24)
        
        return {
            "total_schedules": len(self.schedules),
            "enabled_schedules": len([s for s in self.schedules.values() if s.enabled]),
            "total_runs": len(self.runs),
            "recent_runs_24h": len(recent_runs),
            "recent_success_rate": (
                len([r for r in recent_runs if r.success]) / len(recent_runs) * 100
                if recent_runs else 0
            ),
            "active_runs": len([r for r in self.runs.values() if r.status == WorkflowStatus.RUNNING]),
            "configs": len(self.configs),
        }
    
    def get_workflow_stats(self, workflow_type: WorkflowType) -> Dict[str, Any]:
        """Get statistics for a specific workflow type."""
        runs = [r for r in self.runs.values() if r.workflow_type == workflow_type]
        
        if not runs:
            return {
                "workflow_type": workflow_type.value,
                "total_runs": 0,
                "success_rate": 0,
                "avg_duration": 0,
            }
        
        successful = [r for r in runs if r.success]
        
        return {
            "workflow_type": workflow_type.value,
            "total_runs": len(runs),
            "successful_runs": len(successful),
            "failed_runs": len(runs) - len(successful),
            "success_rate": len(successful) / len(runs) * 100,
            "avg_duration": sum(r.duration_seconds for r in runs) / len(runs),
            "total_items_processed": sum(r.items_processed for r in runs),
        }
    
    def export_config(self) -> str:
        """Export all configuration as JSON."""
        config = {
            "schedules": {k: v.to_dict() for k, v in self.schedules.items()},
            "configs": {k: v.to_dict() for k, v in self.configs.items()},
        }
        return json.dumps(config, indent=2)
    
    def import_config(self, json_str: str) -> bool:
        """Import configuration from JSON."""
        try:
            config = json.loads(json_str)
            
            # Import schedules
            for schedule_id, schedule_data in config.get("schedules", {}).items():
                schedule = WorkflowSchedule(
                    schedule_id=schedule_id,
                    workflow_type=WorkflowType(schedule_data["workflow_type"]),
                    schedule_type=ScheduleType(schedule_data["schedule_type"]),
                    cron_expression=schedule_data.get("cron_expression"),
                    interval_hours=schedule_data.get("interval_hours"),
                    enabled=schedule_data.get("enabled", True),
                    domain=schedule_data.get("domain", "english"),
                    limit=schedule_data.get("limit", 20),
                    parameters=schedule_data.get("parameters", {}),
                )
                self.schedules[schedule_id] = schedule
            
            logger.info("Imported workflow configuration")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False


# Global instance
workflow_manager = WorkflowManager()
