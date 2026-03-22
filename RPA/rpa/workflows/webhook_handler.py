"""
GitHub Webhook Handler for Workflow Events.

Receives and processes GitHub Actions workflow events.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
import hashlib
import hmac
import json
import logging

from . import WorkflowType, WorkflowStatus, workflow_manager

logger = logging.getLogger(__name__)


@dataclass
class WebhookEvent:
    """Parsed GitHub webhook event."""
    event_type: str
    action: Optional[str]
    repository: str
    sender: str
    timestamp: datetime
    payload: Dict[str, Any]
    
    # Workflow specific
    workflow_name: Optional[str] = None
    workflow_run_id: Optional[str] = None
    workflow_run_number: Optional[int] = None
    workflow_status: Optional[str] = None
    workflow_conclusion: Optional[str] = None


class GitHubWebhookHandler:
    """
    Handler for GitHub webhook events.
    
    Processes workflow run events and updates internal tracking.
    """
    
    # Events we handle
    HANDLED_EVENTS = {
        "workflow_run",
        "workflow_dispatch",
        "push",
        "pull_request",
        "schedule",
    }
    
    def __init__(self, secret: Optional[str] = None):
        """
        Initialize webhook handler.
        
        Args:
            secret: GitHub webhook secret for signature verification
        """
        self.secret = secret
        self.event_handlers = {
            "workflow_run": self._handle_workflow_run,
            "workflow_dispatch": self._handle_workflow_dispatch,
            "push": self._handle_push,
            "pull_request": self._handle_pull_request,
        }
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify GitHub webhook signature.
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        if not self.secret:
            return True  # No verification if no secret configured
        
        expected = "sha256=" + hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    def parse_event(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Optional[WebhookEvent]:
        """
        Parse a GitHub webhook event.
        
        Args:
            event_type: X-GitHub-Event header value
            payload: Parsed JSON payload
            
        Returns:
            WebhookEvent or None if not handled
        """
        if event_type not in self.HANDLED_EVENTS:
            return None
        
        # Extract common fields
        repository = payload.get("repository", {}).get("full_name", "unknown")
        sender = payload.get("sender", {}).get("login", "unknown")
        action = payload.get("action")
        
        # Extract workflow-specific fields
        workflow_run = payload.get("workflow_run", {})
        
        return WebhookEvent(
            event_type=event_type,
            action=action,
            repository=repository,
            sender=sender,
            timestamp=datetime.now(),
            payload=payload,
            workflow_name=workflow_run.get("name"),
            workflow_run_id=str(workflow_run.get("id", "")),
            workflow_run_number=workflow_run.get("run_number"),
            workflow_status=workflow_run.get("status"),
            workflow_conclusion=workflow_run.get("conclusion"),
        )
    
    def handle_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Handle a webhook event.
        
        Args:
            event: Parsed webhook event
            
        Returns:
            Result dictionary
        """
        handler = self.event_handlers.get(event.event_type)
        
        if handler:
            try:
                result = handler(event)
                logger.info(f"Handled {event.event_type} event: {result}")
                return result
            except Exception as e:
                logger.error(f"Error handling {event.event_type}: {e}")
                return {"error": str(e)}
        else:
            return {"status": "ignored", "event_type": event.event_type}
    
    def _handle_workflow_run(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle workflow_run event."""
        workflow_name = event.workflow_name or "unknown"
        status = event.workflow_status
        conclusion = event.workflow_conclusion
        
        # Map workflow name to type
        workflow_type = self._map_workflow_name(workflow_name)
        
        # Map GitHub status to our status
        our_status = self._map_status(status, conclusion)
        
        # Find or create run
        runs = workflow_manager.list_runs(workflow_type=workflow_type, limit=10)
        run = None
        
        for r in runs:
            if r.github_run_id == event.workflow_run_id:
                run = r
                break
        
        if not run:
            # Create new run
            run = workflow_manager.create_run(
                workflow_type=workflow_type,
                github_run_id=event.workflow_run_id,
                github_run_number=event.workflow_run_number,
                github_actor=event.sender,
            )
        
        # Update status
        if status == "in_progress":
            workflow_manager.start_run(run.run_id)
        elif status == "completed":
            workflow_manager.complete_run(
                run.run_id,
                success=conclusion == "success",
                output={"github_conclusion": conclusion},
            )
        
        return {
            "status": "processed",
            "workflow_type": workflow_type.value,
            "run_id": run.run_id,
            "github_status": status,
            "conclusion": conclusion,
        }
    
    def _handle_workflow_dispatch(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle workflow_dispatch event."""
        workflow = event.payload.get("workflow", "unknown")
        inputs = event.payload.get("inputs", {})
        
        # Determine workflow type from inputs
        job_type = inputs.get("job_type", "vocabulary_review")
        workflow_type = self._map_job_type(job_type)
        
        # Create run record
        run = workflow_manager.create_run(
            workflow_type=workflow_type,
            github_actor=event.sender,
        )
        
        return {
            "status": "processed",
            "workflow": workflow,
            "run_id": run.run_id,
            "job_type": job_type,
            "inputs": inputs,
        }
    
    def _handle_push(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle push event."""
        ref = event.payload.get("ref", "")
        commits = event.payload.get("commits", [])
        
        # If pushing to main, might want to trigger CI
        if ref == "refs/heads/main":
            logger.info(f"Push to main by {event.sender}: {len(commits)} commits")
        
        return {
            "status": "processed",
            "ref": ref,
            "commits": len(commits),
        }
    
    def _handle_pull_request(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle pull_request event."""
        action = event.action
        pr_number = event.payload.get("pull_request", {}).get("number")
        
        return {
            "status": "processed",
            "action": action,
            "pr_number": pr_number,
        }
    
    def _map_workflow_name(self, name: str) -> WorkflowType:
        """Map GitHub workflow name to WorkflowType."""
        name_lower = name.lower()
        
        if "ci" in name_lower or "test" in name_lower:
            return WorkflowType.CI
        elif "vocab" in name_lower:
            return WorkflowType.VOCABULARY_REVIEW
        elif "report" in name_lower or "daily" in name_lower:
            return WorkflowType.DAILY_REPORT
        elif "cleanup" in name_lower or "memory" in name_lower:
            return WorkflowType.MEMORY_CLEANUP
        elif "learn" in name_lower or "session" in name_lower:
            return WorkflowType.LEARNING_SESSION
        else:
            return WorkflowType.CI  # Default
    
    def _map_status(self, status: Optional[str], conclusion: Optional[str]) -> WorkflowStatus:
        """Map GitHub status/conclusion to WorkflowStatus."""
        if status == "queued":
            return WorkflowStatus.PENDING
        elif status == "in_progress":
            return WorkflowStatus.RUNNING
        elif status == "completed":
            if conclusion == "success":
                return WorkflowStatus.SUCCESS
            elif conclusion == "failure":
                return WorkflowStatus.FAILURE
            elif conclusion == "cancelled":
                return WorkflowStatus.CANCELLED
            elif conclusion == "skipped":
                return WorkflowStatus.SKIPPED
        
        return WorkflowStatus.PENDING
    
    def _map_job_type(self, job_type: str) -> WorkflowType:
        """Map job_type input to WorkflowType."""
        mapping = {
            "vocabulary_review": WorkflowType.VOCABULARY_REVIEW,
            "learning_session": WorkflowType.LEARNING_SESSION,
            "system_report": WorkflowType.DAILY_REPORT,
            "memory_cleanup": WorkflowType.MEMORY_CLEANUP,
            "curriculum_update": WorkflowType.CURRICULUM_UPDATE,
        }
        return mapping.get(job_type, WorkflowType.VOCABULARY_REVIEW)


# Default handler instance
webhook_handler = GitHubWebhookHandler()
