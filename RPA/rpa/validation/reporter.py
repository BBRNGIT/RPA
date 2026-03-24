"""
Consolidation Reporter for RPA system.

Provides detailed reporting on pattern consolidation outcomes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from rpa.core.graph import Node, PatternGraph
from rpa.memory.stm import ShortTermMemory
from rpa.memory.ltm import LongTermMemory
from rpa.validation.validator import Validator


@dataclass
class ConsolidationIssue:
    """Represents a consolidation issue."""
    issue_type: str
    description: str
    affected_nodes: List[str] = field(default_factory=list)
    severity: str = "medium"  # low, medium, high


class ConsolidationReporter:
    """
    Generates detailed reports on pattern consolidation.
    
    The ConsolidationReporter provides:
    - Detailed breakdown of consolidation outcomes
    - Rejection pattern analysis
    - Fix suggestions
    - Batch-level statistics
    """
    
    def __init__(self, validator: Optional[Validator] = None):
        """
        Initialize the ConsolidationReporter.
        
        Args:
            validator: Optional Validator instance (created if not provided)
        """
        self.validator = validator or Validator()
        self._reports: Dict[str, Dict[str, Any]] = {}
    
    def report_consolidation(
        self,
        batch_id: str,
        session_id: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> Dict[str, Any]:
        """
        Generate a detailed consolidation report for a batch.
        
        Args:
            batch_id: Identifier for the batch
            session_id: Session ID to report on
            stm: Short-Term Memory instance
            ltm: Long-Term Memory instance
            
        Returns:
            Detailed consolidation report dictionary
        """
        session = stm.get_session(session_id)
        if not session:
            return {
                "batch_id": batch_id,
                "session_id": session_id,
                "error": "Session not found",
                "total_patterns": 0,
                "consolidated": 0,
                "rejected": 0,
                "pending_review": 0,
                "breakdown": {},
                "details": [],
            }
        
        # Categorize patterns
        consolidated = []
        rejected = []
        pending = []
        
        for node_id in session.patterns_learned:
            node = stm.get_pattern(node_id)
            if not node:
                continue
            
            # Check if consolidated to LTM
            if ltm.has_pattern(node_id):
                consolidated.append(node_id)
            elif node_id in session.patterns_rejected:
                rejected.append(node_id)
            elif node_id in session.patterns_validated:
                # Validated but not yet in LTM
                pending.append(node_id)
            else:
                pending.append(node_id)
        
        # Get detailed breakdown
        breakdown = {
            "structural_valid": 0,
            "missing_references": 0,
            "circular_dependencies": 0,
            "incomplete_composition": 0,
            "other_issues": 0,
        }
        
        details = []
        
        # Analyze each pattern
        for node_id in session.patterns_learned:
            node = stm.get_pattern(node_id)
            if not node:
                continue
            
            # Get validation result
            result = self.validator.validate_pattern_structure_detailed(
                node_id, stm._graph
            )
            
            status = "pending_review"
            if node_id in consolidated:
                status = "consolidated"
                breakdown["structural_valid"] += 1
            elif node_id in rejected:
                status = "rejected"
                # Count issue types
                for issue in result.get("structural_issues", []):
                    issue_type = issue.get("issue_type", "other_issues")
                    if issue_type == "missing_reference":
                        breakdown["missing_references"] += 1
                    elif issue_type == "circular_dependency":
                        breakdown["circular_dependencies"] += 1
                    elif issue_type == "incomplete_composition":
                        breakdown["incomplete_composition"] += 1
                    else:
                        breakdown["other_issues"] += 1
            
            details.append({
                "node_id": node_id,
                "status": status,
                "issues": result.get("structural_issues", []),
                "is_valid": result.get("is_valid", False),
            })
        
        report = {
            "batch_id": batch_id,
            "session_id": session_id,
            "total_patterns": len(session.patterns_learned),
            "consolidated": len(consolidated),
            "rejected": len(rejected),
            "pending_review": len(pending),
            "breakdown": breakdown,
            "details": details,
            "generated_at": datetime.now().isoformat(),
        }
        
        # Store report
        self._reports[f"{batch_id}_{session_id}"] = report
        
        return report
    
    def identify_rejection_patterns(
        self,
        batch_id: str,
        stm: ShortTermMemory,
    ) -> Dict[str, Any]:
        """
        Identify common patterns in rejections.
        
        Args:
            batch_id: Batch identifier
            stm: Short-Term Memory instance
            
        Returns:
            Analysis of rejection patterns
        """
        # Find rejected patterns
        rejected_nodes = []
        for session in stm.list_sessions():
            for node_id in session.patterns_rejected:
                node = stm.get_pattern(node_id)
                if node:
                    rejected_nodes.append(node)
        
        # Group by issue type
        issues_by_type: Dict[str, List[Dict]] = {}
        
        for node in rejected_nodes:
            result = self.validator.validate_pattern_structure_detailed(
                node.node_id, stm._graph
            )
            
            for issue in result.get("structural_issues", []):
                issue_type = issue.get("issue_type", "unknown")
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = []
                
                issues_by_type[issue_type].append({
                    "node_id": node.node_id,
                    "description": issue.get("description", ""),
                    "affected_nodes": issue.get("affected_nodes", []),
                })
        
        return {
            "batch_id": batch_id,
            "total_rejections": len(rejected_nodes),
            "issues_by_type": issues_by_type,
            "most_common_issue": max(
                issues_by_type.keys(), 
                key=lambda k: len(issues_by_type[k])
            ) if issues_by_type else None,
            "analysis_timestamp": datetime.now().isoformat(),
        }
    
    def suggest_fixes(
        self,
        node_id: str,
        graph: PatternGraph,
    ) -> List[str]:
        """
        Suggest how to fix a rejected pattern.
        
        Args:
            node_id: ID of the rejected pattern
            graph: Pattern graph
            
        Returns:
            List of fix suggestions
        """
        return self.validator.suggest_fixes(node_id, graph)
    
    def get_batch_summary(
        self,
        batch_id: str,
        sessions: List[str],
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> Dict[str, Any]:
        """
        Get a summary of all sessions in a batch.
        
        Args:
            batch_id: Batch identifier
            sessions: List of session IDs
            stm: Short-Term Memory
            ltm: Long-Term Memory
            
        Returns:
            Batch summary
        """
        total_patterns = 0
        total_consolidated = 0
        total_rejected = 0
        total_pending = 0
        all_issues: Dict[str, int] = {}
        
        for session_id in sessions:
            report = self.report_consolidation(batch_id, session_id, stm, ltm)
            
            total_patterns += report["total_patterns"]
            total_consolidated += report["consolidated"]
            total_rejected += report["rejected"]
            total_pending += report["pending_review"]
            
            for issue_type, count in report["breakdown"].items():
                all_issues[issue_type] = all_issues.get(issue_type, 0) + count
        
        return {
            "batch_id": batch_id,
            "sessions_analyzed": len(sessions),
            "total_patterns": total_patterns,
            "consolidated": total_consolidated,
            "rejected": total_rejected,
            "pending_review": total_pending,
            "consolidation_rate": (
                total_consolidated / total_patterns * 100 
                if total_patterns > 0 else 0
            ),
            "issues_summary": all_issues,
            "generated_at": datetime.now().isoformat(),
        }
    
    def export_report(
        self,
        report_id: str,
        format: str = "json",
    ) -> Optional[str]:
        """
        Export a stored report.
        
        Args:
            report_id: ID of the report to export
            format: Export format (json, text)
            
        Returns:
            Report string or None if not found
        """
        report = self._reports.get(report_id)
        if not report:
            return None
        
        if format == "json":
            import json
            return json.dumps(report, indent=2)
        elif format == "text":
            lines = [
                f"Consolidation Report: {report['batch_id']}",
                f"Session: {report['session_id']}",
                f"Generated: {report.get('generated_at', 'N/A')}",
                "",
                f"Total Patterns: {report['total_patterns']}",
                f"Consolidated: {report['consolidated']}",
                f"Rejected: {report['rejected']}",
                f"Pending Review: {report['pending_review']}",
                "",
                "Breakdown:",
            ]
            for issue_type, count in report["breakdown"].items():
                lines.append(f"  - {issue_type}: {count}")
            
            return "\n".join(lines)
        
        return None
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a stored report by ID."""
        return self._reports.get(report_id)
    
    def list_reports(self) -> List[str]:
        """List all stored report IDs."""
        return list(self._reports.keys())
    
    def clear_reports(self) -> None:
        """Clear all stored reports."""
        self._reports.clear()
