"""
Tests for GitHub Actions Workflow Integration.

Tests the workflow manager, webhook handler, and API integration.
"""

import pytest
from datetime import datetime
import json

from rpa.workflows import (
    WorkflowManager, WorkflowType, WorkflowStatus, WorkflowSchedule,
    WorkflowConfig, WorkflowRun, ScheduleType, workflow_manager
)
from rpa.workflows.webhook_handler import (
    GitHubWebhookHandler, WebhookEvent, webhook_handler
)


class TestWorkflowEnums:
    """Test workflow enums."""
    
    def test_workflow_type_values(self):
        """Test WorkflowType enum values."""
        assert WorkflowType.CI.value == "ci"
        assert WorkflowType.VOCABULARY_REVIEW.value == "vocabulary_review"
        assert WorkflowType.DAILY_REPORT.value == "daily_report"
        assert WorkflowType.MEMORY_CLEANUP.value == "memory_cleanup"
        assert WorkflowType.LEARNING_SESSION.value == "learning_session"
    
    def test_workflow_status_values(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.SUCCESS.value == "success"
        assert WorkflowStatus.FAILURE.value == "failure"
        assert WorkflowStatus.CANCELLED.value == "cancelled"
    
    def test_schedule_type_values(self):
        """Test ScheduleType enum values."""
        assert ScheduleType.CRON.value == "cron"
        assert ScheduleType.INTERVAL.value == "interval"
        assert ScheduleType.MANUAL.value == "manual"


class TestWorkflowSchedule:
    """Test WorkflowSchedule dataclass."""
    
    def test_create_schedule(self):
        """Test creating a workflow schedule."""
        schedule = WorkflowSchedule(
            schedule_id="test_schedule",
            workflow_type=WorkflowType.VOCABULARY_REVIEW,
            schedule_type=ScheduleType.CRON,
            cron_expression="0 */6 * * *",
        )
        
        assert schedule.schedule_id == "test_schedule"
        assert schedule.workflow_type == WorkflowType.VOCABULARY_REVIEW
        assert schedule.enabled is True
        assert schedule.domain == "english"
    
    def test_schedule_to_dict(self):
        """Test schedule serialization."""
        schedule = WorkflowSchedule(
            schedule_id="test",
            workflow_type=WorkflowType.CI,
            schedule_type=ScheduleType.INTERVAL,
            interval_hours=6,
        )
        
        data = schedule.to_dict()
        
        assert data["schedule_id"] == "test"
        assert data["workflow_type"] == "ci"
        assert data["interval_hours"] == 6


class TestWorkflowRun:
    """Test WorkflowRun dataclass."""
    
    def test_create_run(self):
        """Test creating a workflow run."""
        run = WorkflowRun(
            run_id="run_123",
            workflow_type=WorkflowType.CI,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(),
        )
        
        assert run.run_id == "run_123"
        assert run.status == WorkflowStatus.RUNNING
        assert run.success is False
    
    def test_run_to_dict(self):
        """Test run serialization."""
        run = WorkflowRun(
            run_id="run_456",
            workflow_type=WorkflowType.VOCABULARY_REVIEW,
            status=WorkflowStatus.SUCCESS,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            success=True,
            items_processed=50,
        )
        
        data = run.to_dict()
        
        assert data["run_id"] == "run_456"
        assert data["success"] is True
        assert data["items_processed"] == 50


class TestWorkflowManager:
    """Test WorkflowManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh workflow manager."""
        return WorkflowManager()
    
    def test_manager_initialization(self, manager):
        """Test manager initializes with default schedules."""
        assert len(manager.schedules) == 3
        assert len(manager.configs) == 2
    
    def test_get_schedule(self, manager):
        """Test getting a schedule."""
        schedule = manager.get_schedule("vocab_review_6h")
        assert schedule is not None
        assert schedule.workflow_type == WorkflowType.VOCABULARY_REVIEW
    
    def test_list_schedules(self, manager):
        """Test listing schedules."""
        schedules = manager.list_schedules()
        assert len(schedules) == 3
        
        enabled = manager.list_schedules(enabled_only=True)
        assert len(enabled) == 3
    
    def test_add_schedule(self, manager):
        """Test adding a schedule."""
        new_schedule = WorkflowSchedule(
            schedule_id="new_test",
            workflow_type=WorkflowType.LEARNING_SESSION,
            schedule_type=ScheduleType.MANUAL,
        )
        
        result = manager.add_schedule(new_schedule)
        assert result.schedule_id == "new_test"
        assert manager.get_schedule("new_test") is not None
    
    def test_remove_schedule(self, manager):
        """Test removing a schedule."""
        manager.add_schedule(WorkflowSchedule(
            schedule_id="to_remove",
            workflow_type=WorkflowType.CI,
            schedule_type=ScheduleType.MANUAL,
        ))
        
        assert manager.remove_schedule("to_remove") is True
        assert manager.get_schedule("to_remove") is None
        assert manager.remove_schedule("nonexistent") is False
    
    def test_toggle_schedule(self, manager):
        """Test toggling schedule enabled state."""
        schedule = manager.toggle_schedule("vocab_review_6h", False)
        assert schedule.enabled is False
        
        schedule = manager.toggle_schedule("vocab_review_6h", True)
        assert schedule.enabled is True
    
    def test_create_run(self, manager):
        """Test creating a workflow run."""
        run = manager.create_run(
            workflow_type=WorkflowType.VOCABULARY_REVIEW,
            github_run_id="gh_123",
            github_actor="testuser",
        )
        
        assert run.run_id is not None
        assert run.status == WorkflowStatus.PENDING
        assert run.github_run_id == "gh_123"
        assert manager.get_run(run.run_id) is not None
    
    def test_start_run(self, manager):
        """Test starting a run."""
        run = manager.create_run(WorkflowType.CI)
        started = manager.start_run(run.run_id)
        
        assert started.status == WorkflowStatus.RUNNING
    
    def test_complete_run(self, manager):
        """Test completing a run."""
        run = manager.create_run(WorkflowType.VOCABULARY_REVIEW)
        manager.start_run(run.run_id)
        
        completed = manager.complete_run(
            run.run_id,
            success=True,
            items_processed=25,
            output={"reviewed": 25}
        )
        
        assert completed.status == WorkflowStatus.SUCCESS
        assert completed.success is True
        assert completed.items_processed == 25
        assert completed.duration_seconds > 0
    
    def test_fail_run(self, manager):
        """Test failing a run."""
        run = manager.create_run(WorkflowType.CI)
        manager.start_run(run.run_id)
        
        failed = manager.fail_run(run.run_id, ["Error 1", "Error 2"])
        
        assert failed.status == WorkflowStatus.FAILURE
        assert failed.success is False
        assert len(failed.errors) == 2
    
    def test_list_runs(self, manager):
        """Test listing runs."""
        # Create some runs
        manager.create_run(WorkflowType.CI)
        manager.create_run(WorkflowType.VOCABULARY_REVIEW)
        manager.create_run(WorkflowType.DAILY_REPORT)
        
        all_runs = manager.list_runs()
        assert len(all_runs) == 3
        
        ci_runs = manager.list_runs(workflow_type=WorkflowType.CI)
        assert len(ci_runs) == 1
    
    def test_get_status(self, manager):
        """Test getting workflow status."""
        manager.create_run(WorkflowType.CI)
        
        status = manager.get_status()
        
        assert "total_schedules" in status
        assert "total_runs" in status
        assert "recent_success_rate" in status
    
    def test_get_workflow_stats(self, manager):
        """Test getting workflow statistics."""
        run = manager.create_run(WorkflowType.CI)
        manager.complete_run(run.run_id, success=True, items_processed=10)
        
        stats = manager.get_workflow_stats(WorkflowType.CI)
        
        assert stats["workflow_type"] == "ci"
        assert stats["total_runs"] >= 1
        assert stats["success_rate"] > 0
    
    def test_export_import_config(self, manager):
        """Test exporting and importing configuration."""
        config_json = manager.export_config()
        
        assert "schedules" in config_json
        assert "configs" in config_json
        
        # Import should work
        assert manager.import_config(config_json) is True


class TestWebhookEvent:
    """Test WebhookEvent dataclass."""
    
    def test_create_webhook_event(self):
        """Test creating a webhook event."""
        event = WebhookEvent(
            event_type="workflow_run",
            action="completed",
            repository="owner/repo",
            sender="testuser",
            timestamp=datetime.now(),
            payload={"test": "data"},
        )
        
        assert event.event_type == "workflow_run"
        assert event.repository == "owner/repo"


class TestGitHubWebhookHandler:
    """Test GitHubWebhookHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create a webhook handler."""
        return GitHubWebhookHandler(secret="test_secret")
    
    def test_verify_signature_valid(self, handler):
        """Test signature verification with valid signature."""
        payload = b'{"test": "data"}'
        
        # Calculate expected signature
        import hmac
        import hashlib
        expected = "sha256=" + hmac.new(
            b"test_secret", payload, hashlib.sha256
        ).hexdigest()
        
        assert handler.verify_signature(payload, expected) is True
    
    def test_verify_signature_invalid(self, handler):
        """Test signature verification with invalid signature."""
        payload = b'{"test": "data"}'
        
        assert handler.verify_signature(payload, "sha256=invalid") is False
    
    def test_parse_workflow_run_event(self, handler):
        """Test parsing workflow_run event."""
        payload = {
            "repository": {"full_name": "owner/repo"},
            "sender": {"login": "testuser"},
            "workflow_run": {
                "id": 12345,
                "run_number": 42,
                "name": "RPA CI Pipeline",
                "status": "completed",
                "conclusion": "success",
            }
        }
        
        event = handler.parse_event("workflow_run", payload)
        
        assert event is not None
        assert event.event_type == "workflow_run"
        assert event.repository == "owner/repo"
        assert event.workflow_run_id == "12345"
        assert event.workflow_conclusion == "success"
    
    def test_parse_push_event(self, handler):
        """Test parsing push event."""
        payload = {
            "repository": {"full_name": "owner/repo"},
            "sender": {"login": "testuser"},
            "ref": "refs/heads/main",
            "commits": [{"id": "abc123"}],
        }
        
        event = handler.parse_event("push", payload)
        
        assert event is not None
        assert event.event_type == "push"
    
    def test_parse_ignored_event(self, handler):
        """Test parsing an ignored event type."""
        payload = {"repository": {"full_name": "owner/repo"}}
        
        event = handler.parse_event("issues", payload)
        
        assert event is None
    
    def test_map_workflow_name(self, handler):
        """Test mapping workflow names to types."""
        assert handler._map_workflow_name("RPA CI Pipeline") == WorkflowType.CI
        assert handler._map_workflow_name("Vocabulary Review") == WorkflowType.VOCABULARY_REVIEW
        assert handler._map_workflow_name("Daily Report") == WorkflowType.DAILY_REPORT
        assert handler._map_workflow_name("Memory Cleanup") == WorkflowType.MEMORY_CLEANUP
    
    def test_map_status(self, handler):
        """Test mapping GitHub status to WorkflowStatus."""
        assert handler._map_status("queued", None) == WorkflowStatus.PENDING
        assert handler._map_status("in_progress", None) == WorkflowStatus.RUNNING
        assert handler._map_status("completed", "success") == WorkflowStatus.SUCCESS
        assert handler._map_status("completed", "failure") == WorkflowStatus.FAILURE
        assert handler._map_status("completed", "cancelled") == WorkflowStatus.CANCELLED


class TestGlobalInstances:
    """Test global instances."""
    
    def test_global_workflow_manager(self):
        """Test global workflow manager exists."""
        assert workflow_manager is not None
        assert isinstance(workflow_manager, WorkflowManager)
    
    def test_global_webhook_handler(self):
        """Test global webhook handler exists."""
        assert webhook_handler is not None
        assert isinstance(webhook_handler, GitHubWebhookHandler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
