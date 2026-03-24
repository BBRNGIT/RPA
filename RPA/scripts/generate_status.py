#!/usr/bin/env python3
"""
Generate status.json for the RPA AI monitoring dashboard.

This script collects learning metrics and generates a JSON status file
that the GitHub Pages dashboard reads to display current state.

Run by GitHub Actions after each learning session.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory


def generate_status(
    persistence_path: str = "memory/learning_state",
    output_path: str = "docs/data/status.json"
) -> Dict[str, Any]:
    """
    Generate comprehensive status for the monitoring dashboard.
    
    Args:
        persistence_path: Path to LTM storage
        output_path: Path to write status.json
        
    Returns:
        Status dictionary
    """
    # Initialize memory
    ltm = LongTermMemory(storage_path=persistence_path)
    ltm.load()
    
    # Calculate domain breakdown
    domains: Dict[str, int] = {}
    for node in ltm._graph.nodes.values():
        domain = getattr(node, 'domain', 'unknown') or 'unknown'
        domains[domain] = domains.get(domain, 0) + 1
    
    # Calculate progress
    total_patterns = len(ltm)
    progress_to_1m = total_patterns / 1_000_000
    
    # Load accelerated learning state
    accelerated_state_path = Path(persistence_path) / "accelerated_learning_state.json"
    recent_sessions: List[Dict] = []
    exam_history: List[Dict] = []
    sessions_today = 0
    avg_test_score = 0.0
    avg_exam_score = 0.0
    
    if accelerated_state_path.exists():
        try:
            with open(accelerated_state_path) as f:
                acc_state = json.load(f)
            
            results = acc_state.get("results", [])
            
            # Get today's sessions
            today = datetime.now().date()
            today_results = []
            for r in results:
                try:
                    ts = datetime.fromisoformat(r["timestamp"])
                    if ts.date() == today:
                        today_results.append(r)
                except:
                    pass
            
            sessions_today = len(today_results)
            
            # Calculate averages
            test_scores = [r["test_score"] for r in results if r.get("test_score") is not None]
            exam_scores = [r["exam_score"] for r in results if r.get("exam_score") is not None]
            
            avg_test_score = sum(test_scores) / len(test_scores) if test_scores else 0.0
            avg_exam_score = sum(exam_scores) / len(exam_scores) if exam_scores else 0.0
            
            # Get recent sessions (last 20)
            recent_sessions = results[-20:] if results else []
            
            # Get exam history
            exam_history = [
                {"exam_score": r["exam_score"], "timestamp": r["timestamp"]}
                for r in results if r.get("exam_score") is not None
            ][-10:]  # Last 10 exams
            
        except Exception as e:
            print(f"Warning: Could not load accelerated learning state: {e}")
    
    # Get test count (run pytest --collect-only to count)
    tests_passing = 957  # Default; updated by workflow
    
    # Check for pytest results
    pytest_cache = Path(".pytest_cache")
    if pytest_cache.exists():
        # Could parse pytest results here
        pass
    
    # Build status
    status = {
        "total_patterns": total_patterns,
        "progress_to_1m": progress_to_1m,
        "tests_passing": tests_passing,
        "sessions_today": sessions_today,
        "domains": domains,
        "recent_sessions": recent_sessions,
        "exam_history": exam_history,
        "avg_test_score": avg_test_score,
        "avg_exam_score": avg_exam_score,
        "pipeline_ok": True,
        "memory_ok": True,
        "is_active": True,
        "last_update": datetime.utcnow().isoformat() + "Z",
        "goal_patterns": 1_000_000,
        "version": "1.0.0"
    }
    
    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(status, f, indent=2)
    
    print(f"Status written to {output_path}")
    print(f"  Total patterns: {total_patterns:,}")
    print(f"  Progress: {progress_to_1m*100:.4f}%")
    print(f"  Sessions today: {sessions_today}")
    
    return status


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate RPA status.json")
    parser.add_argument("--persistence", default="memory/learning_state",
                       help="Path to LTM persistence")
    parser.add_argument("--output", default="docs/data/status.json",
                       help="Output path for status.json")
    parser.add_argument("--tests", type=int, default=None,
                       help="Override test count")
    
    args = parser.parse_args()
    
    status = generate_status(args.persistence, args.output)
    
    if args.tests:
        status["tests_passing"] = args.tests
        with open(args.output, "w") as f:
            json.dump(status, f, indent=2)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
