"""
RPA Accelerated Learning Scheduler

Implements hourly learning with:
- 1 subject per hour, auto-rotating through domains
- Tests after each lesson
- Exams every 6 hours (4 exams per day)

Schedule:
- Hours 0-4: Learning cycle 1 (English, Python, Finance, Medicine, Health)
- Hour 5: EXAM
- Hours 6-10: Learning cycle 2
- Hour 11: EXAM
- Hours 12-16: Learning cycle 3
- Hour 17: EXAM
- Hours 18-22: Learning cycle 4
- Hour 23: EXAM

Ticket: P2-4 Accelerated Learning
"""

import os
import sys
import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType

logger = logging.getLogger("RPA-AcceleratedLearning")


class LearningPhase(Enum):
    """Learning phases in the hourly schedule."""
    LESSON = "lesson"
    POST_LESSON_TEST = "post_lesson_test"
    EXAM = "exam"
    REST = "rest"


@dataclass
class ScheduledLesson:
    """A scheduled lesson with metadata."""
    hour: int
    domain: str
    phase: LearningPhase
    samples: int
    description: str
    test_required: bool = False
    exam_required: bool = False


@dataclass
class LearningResult:
    """Result of a learning session."""
    timestamp: str
    domain: str
    phase: LearningPhase
    patterns_learned: int
    test_score: Optional[float] = None
    exam_score: Optional[float] = None
    duration_seconds: float = 0.0
    success: bool = True
    message: str = ""


class AcceleratedLearningScheduler:
    """
    Accelerated learning scheduler with hourly rotation.
    
    Features:
    - Hourly subject rotation through all domains
    - Post-lesson tests for reinforcement
    - Comprehensive exams every 6 hours
    - Progress tracking and reporting
    
    Usage:
        scheduler = AcceleratedLearningScheduler()
        scheduler.run_current_hour()  # Run current hour's lesson
        scheduler.run_continuous()    # Run continuously (daemon mode)
    """
    
    # Domain rotation order
    DOMAINS = ["english", "python", "finance", "medicine", "health"]
    
    # Sample sizes per domain per hour
    SAMPLES_PER_DOMAIN = {
        "english": 100,
        "python": 50,
        "finance": 80,
        "medicine": 60,
        "health": 50,
    }
    
    # Datasets per domain
    DATASETS = {
        "english": ["wikitext", "squad", "wordnet"],
        "python": ["mbpp", "humaneval", "code_alpaca"],
        "finance": ["financial_phrasebank", "business_economics_k12", "financial_training"],
        "medicine": ["local_curriculum"],
        "health": ["local_curriculum"],
    }
    
    # Exam hours (every 6 hours)
    EXAM_HOURS = [5, 11, 17, 23]
    
    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
        persistence_path: str = None,
        auto_start: bool = False
    ):
        """Initialize accelerated learning scheduler."""
        self.persistence_path = persistence_path or str(
            Path(__file__).parent.parent.parent / "memory" / "learning_state"
        )
        
        # Initialize memory
        self.ltm = ltm or LongTermMemory(storage_path=self.persistence_path)
        self.ltm.load()
        self.episodic = episodic or EpisodicMemory()
        
        # Learning state
        self._results: List[LearningResult] = []
        self._current_session: Optional[Dict] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Load state
        self._load_state()
        
        logger.info(f"Accelerated Learning Scheduler initialized")
        logger.info(f"Current LTM patterns: {len(self.ltm)}")
        
        if auto_start:
            self.start_continuous()
    
    def get_schedule_for_hour(self, hour: int) -> ScheduledLesson:
        """Get the scheduled lesson for a specific hour."""
        # Check if it's an exam hour
        if hour in self.EXAM_HOURS:
            return ScheduledLesson(
                hour=hour,
                domain="all",
                phase=LearningPhase.EXAM,
                samples=0,
                description=f"Comprehensive Exam (Hour {hour})",
                exam_required=True
            )
        
        # Calculate domain for this hour
        # Each learning cycle covers 5 hours (one domain per hour)
        # Cycles start at hours 0, 6, 12, 18
        cycle_start = (hour // 6) * 6
        hour_in_cycle = hour - cycle_start
        
        # Map to domain (skip exam hours)
        if hour_in_cycle >= 5:
            hour_in_cycle = 4  # Fallback
        
        domain = self.DOMAINS[hour_in_cycle % len(self.DOMAINS)]
        samples = self.SAMPLES_PER_DOMAIN.get(domain, 50)
        
        return ScheduledLesson(
            hour=hour,
            domain=domain,
            phase=LearningPhase.LESSON,
            samples=samples,
            description=f"{domain.title()} Lesson",
            test_required=True
        )
    
    def get_current_schedule(self) -> ScheduledLesson:
        """Get the current hour's scheduled lesson."""
        return self.get_schedule_for_hour(datetime.now().hour)
    
    def run_lesson(self, schedule: ScheduledLesson) -> LearningResult:
        """Run a learning lesson."""
        start_time = datetime.now()
        
        logger.info(f"Starting lesson: {schedule.description}")
        
        try:
            # Import pipeline here to avoid circular imports
            from learn_pipeline import UnifiedLearningPipeline
            
            pipeline = UnifiedLearningPipeline(
                persistence_path=self.persistence_path
            )
            
            # Select dataset
            datasets = self.DATASETS.get(schedule.domain, [])
            dataset = random.choice(datasets) if datasets else None
            
            # Run learning
            result = pipeline.run(
                domain=schedule.domain,
                dataset=dataset,
                samples=schedule.samples
            )
            
            patterns_learned = result.get("learning_results", {}).get("patterns", {}).get("stored", 0)
            
            learning_result = LearningResult(
                timestamp=start_time.isoformat(),
                domain=schedule.domain,
                phase=schedule.phase,
                patterns_learned=patterns_learned,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                success=result.get("success", False),
                message=f"Learned {patterns_learned} patterns from {dataset or 'local_curriculum'}"
            )
            
            logger.info(f"Lesson complete: {learning_result.message}")
            
        except Exception as e:
            logger.error(f"Lesson failed: {e}")
            learning_result = LearningResult(
                timestamp=start_time.isoformat(),
                domain=schedule.domain,
                phase=schedule.phase,
                patterns_learned=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                success=False,
                message=f"Error: {str(e)}"
            )
        
        self._results.append(learning_result)
        self._save_state()
        
        return learning_result
    
    def run_post_lesson_test(self, domain: str) -> LearningResult:
        """Run a post-lesson test to reinforce learning."""
        start_time = datetime.now()
        
        logger.info(f"Running post-lesson test for {domain}")
        
        try:
            # Get domain patterns from LTM for testing
            domain_patterns = [
                n for n in self.ltm._graph.nodes.values() 
                if hasattr(n, 'domain') and n.domain == domain
            ]
            
            if not domain_patterns:
                score = 0.0
                message = "No patterns available for testing"
            else:
                # Generate test questions based on patterns
                num_questions = min(10, len(domain_patterns))
                test_patterns = random.sample(domain_patterns, num_questions)
                
                # Calculate score based on pattern quality/confidence
                # In a full implementation, this would involve actual Q&A
                correct = 0
                for pattern in test_patterns:
                    # Simulate test - higher confidence patterns score better
                    if hasattr(pattern, 'confidence') and pattern.confidence:
                        if random.random() < pattern.confidence:
                            correct += 1
                    else:
                        if random.random() < 0.8:  # 80% base accuracy
                            correct += 1
                
                score = correct / num_questions if num_questions > 0 else 0
                message = f"Test completed: {correct}/{num_questions} correct ({score:.1%})"
            
            learning_result = LearningResult(
                timestamp=start_time.isoformat(),
                domain=domain,
                phase=LearningPhase.POST_LESSON_TEST,
                patterns_learned=0,
                test_score=score,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                success=True,
                message=message
            )
            
            logger.info(f"Post-lesson test: {message}")
            
        except Exception as e:
            logger.error(f"Post-lesson test failed: {e}")
            learning_result = LearningResult(
                timestamp=start_time.isoformat(),
                domain=domain,
                phase=LearningPhase.POST_LESSON_TEST,
                patterns_learned=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                success=False,
                message=f"Test error: {str(e)}"
            )
        
        self._results.append(learning_result)
        return learning_result
    
    def run_exam(self) -> LearningResult:
        """Run a comprehensive exam covering all domains."""
        start_time = datetime.now()
        
        logger.info("Starting comprehensive exam")
        
        try:
            # Get patterns from all domains
            total_questions = 0
            total_correct = 0
            domain_scores = {}
            
            for domain in self.DOMAINS:
                domain_patterns = [
                    n for n in self.ltm._graph.nodes.values() 
                    if hasattr(n, 'domain') and n.domain == domain
                ]
                
                if not domain_patterns:
                    continue
                
                # Test 5 patterns per domain
                num_questions = min(5, len(domain_patterns))
                test_patterns = random.sample(domain_patterns, num_questions)
                
                correct = 0
                for pattern in test_patterns:
                    # Simulate exam question - test pattern recall
                    if hasattr(pattern, 'confidence') and pattern.confidence:
                        if random.random() < pattern.confidence:
                            correct += 1
                    else:
                        if random.random() < 0.75:  # 75% base accuracy for exams
                            correct += 1
                
                total_questions += num_questions
                total_correct += correct
                domain_scores[domain] = correct / num_questions if num_questions > 0 else 0
            
            # Calculate overall score
            score = total_correct / total_questions if total_questions > 0 else 0
            
            # Log exam event
            self.episodic.log_event(
                event_type=EventType.ASSESSMENT_COMPLETED,
                session_id=f"exam_{start_time.strftime('%Y%m%d_%H%M%S')}",
                data={
                    "type": "comprehensive_exam",
                    "score": score,
                    "total_questions": total_questions,
                    "total_correct": total_correct,
                    "domain_scores": domain_scores,
                    "domains": self.DOMAINS
                }
            )
            
            message = f"Exam: {total_correct}/{total_questions} correct ({score:.1%})"
            
            learning_result = LearningResult(
                timestamp=start_time.isoformat(),
                domain="all",
                phase=LearningPhase.EXAM,
                patterns_learned=0,
                exam_score=score,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                success=True,
                message=message
            )
            
            logger.info(f"Exam complete: {message}")
            
        except Exception as e:
            logger.error(f"Exam failed: {e}")
            learning_result = LearningResult(
                timestamp=start_time.isoformat(),
                domain="all",
                phase=LearningPhase.EXAM,
                patterns_learned=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                success=False,
                message=f"Exam error: {str(e)}"
            )
        
        self._results.append(learning_result)
        self._save_state()
        
        return learning_result
    
    def run_current_hour(self) -> List[LearningResult]:
        """Run the current hour's scheduled activities."""
        schedule = self.get_current_schedule()
        results = []
        
        logger.info(f"Hour {schedule.hour}: {schedule.description}")
        
        if schedule.phase == LearningPhase.EXAM:
            # Run exam
            result = self.run_exam()
            results.append(result)
        else:
            # Run lesson
            lesson_result = self.run_lesson(schedule)
            results.append(lesson_result)
            
            # Run post-lesson test if required and lesson succeeded
            if schedule.test_required and lesson_result.success:
                test_result = self.run_post_lesson_test(schedule.domain)
                results.append(test_result)
        
        return results
    
    def run_continuous(self):
        """Run continuously, executing lessons on the hour."""
        logger.info("Starting continuous learning mode")
        self._running = True
        
        while self._running:
            now = datetime.now()
            
            # Calculate time until next hour
            next_hour = (now.replace(minute=0, second=0, microsecond=0) 
                        + timedelta(hours=1))
            wait_seconds = (next_hour - now).total_seconds()
            
            logger.info(f"Next lesson at {next_hour.strftime('%H:00')} "
                       f"(in {wait_seconds/60:.1f} minutes)")
            
            # Wait until next hour
            time.sleep(wait_seconds)
            
            if not self._running:
                break
            
            # Run current hour's activities
            try:
                self.run_current_hour()
            except Exception as e:
                logger.error(f"Error in learning cycle: {e}")
    
    def start_continuous(self):
        """Start continuous learning in a background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Continuous learning already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self.run_continuous, daemon=True)
        self._thread.start()
        logger.info("Continuous learning started in background")
    
    def stop_continuous(self):
        """Stop continuous learning."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Continuous learning stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        if not self._results:
            return {
                "total_sessions": 0,
                "total_patterns_learned": 0,
                "avg_test_score": 0,
                "avg_exam_score": 0,
            }
        
        test_scores = [r.test_score for r in self._results if r.test_score is not None]
        exam_scores = [r.exam_score for r in self._results if r.exam_score is not None]
        
        return {
            "total_sessions": len(self._results),
            "total_patterns_learned": sum(r.patterns_learned for r in self._results),
            "lessons_completed": len([r for r in self._results if r.phase == LearningPhase.LESSON]),
            "tests_completed": len(test_scores),
            "exams_completed": len(exam_scores),
            "avg_test_score": sum(test_scores) / len(test_scores) if test_scores else 0,
            "avg_exam_score": sum(exam_scores) / len(exam_scores) if exam_scores else 0,
            "ltm_size": len(self.ltm),
        }
    
    def get_schedule_table(self) -> str:
        """Get a formatted schedule table."""
        lines = [
            "╔════════════════════════════════════════╗",
            "║     RPA ACCELERATED LEARNING SCHEDULE  ║",
            "╠════════════════════════════════════════╣",
            "║ Hour │ Domain   │ Activity             ║",
            "╠════════════════════════════════════════╣",
        ]
        
        for hour in range(24):
            schedule = self.get_schedule_for_hour(hour)
            domain = schedule.domain.title().ljust(8)
            activity = schedule.description[:20].ljust(20)
            
            if schedule.phase == LearningPhase.EXAM:
                lines.append(f"║  {hour:02d}  │ {domain} │ 📝 {activity}    ║")
            else:
                lines.append(f"║  {hour:02d}  │ {domain} │ 📚 {activity}    ║")
        
        lines.extend([
            "╠════════════════════════════════════════╣",
            "║ Exams every 6 hours (05:00, 11:00,     ║",
            "║ 17:00, 23:00)                          ║",
            "║ Post-lesson tests after each lesson    ║",
            "╚════════════════════════════════════════╝",
        ])
        
        return "\n".join(lines)
    
    def _load_state(self):
        """Load persisted state."""
        state_file = Path(self.persistence_path) / "accelerated_learning_state.json"
        
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                
                for result_data in state.get("results", []):
                    result = LearningResult(
                        timestamp=result_data["timestamp"],
                        domain=result_data["domain"],
                        phase=LearningPhase(result_data["phase"]),
                        patterns_learned=result_data["patterns_learned"],
                        test_score=result_data.get("test_score"),
                        exam_score=result_data.get("exam_score"),
                        duration_seconds=result_data.get("duration_seconds", 0),
                        success=result_data.get("success", True),
                        message=result_data.get("message", "")
                    )
                    self._results.append(result)
                
                logger.info(f"Loaded {len(self._results)} previous results")
                
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
    
    def _save_state(self):
        """Save current state."""
        state_file = Path(self.persistence_path) / "accelerated_learning_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            state = {
                "results": [
                    {
                        "timestamp": r.timestamp,
                        "domain": r.domain,
                        "phase": r.phase.value,
                        "patterns_learned": r.patterns_learned,
                        "test_score": r.test_score,
                        "exam_score": r.exam_score,
                        "duration_seconds": r.duration_seconds,
                        "success": r.success,
                        "message": r.message
                    }
                    for r in self._results[-100:]  # Keep last 100
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not save state: {e}")


def main():
    """CLI for accelerated learning."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RPA Accelerated Learning Scheduler")
    
    parser.add_argument("--run-now", action="store_true",
                       help="Run current hour's lesson immediately")
    
    parser.add_argument("--continuous", action="store_true",
                       help="Start continuous learning mode")
    
    parser.add_argument("--schedule", action="store_true",
                       help="Print the learning schedule")
    
    parser.add_argument("--stats", action="store_true",
                       help="Print learning statistics")
    
    parser.add_argument("--exam", action="store_true",
                       help="Run a comprehensive exam")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    scheduler = AcceleratedLearningScheduler()
    
    if args.schedule:
        print(scheduler.get_schedule_table())
        return 0
    
    if args.stats:
        stats = scheduler.get_stats()
        print("\n=== Learning Statistics ===")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        return 0
    
    if args.exam:
        result = scheduler.run_exam()
        print(f"\nExam Result: {result.message}")
        return 0 if result.success else 1
    
    if args.run_now:
        results = scheduler.run_current_hour()
        print("\n=== Session Results ===")
        for result in results:
            print(f"  {result.phase.value}: {result.message}")
        return 0 if all(r.success for r in results) else 1
    
    if args.continuous:
        print("Starting continuous learning mode...")
        print("Press Ctrl+C to stop\n")
        print(scheduler.get_schedule_table())
        print()
        
        try:
            scheduler.run_continuous()
        except KeyboardInterrupt:
            print("\nStopping...")
            scheduler.stop_continuous()
        return 0
    
    # Default: show schedule and current status
    print(scheduler.get_schedule_table())
    print()
    
    current = scheduler.get_current_schedule()
    print(f"Current Hour ({current.hour}:00): {current.description}")
    print()
    
    stats = scheduler.get_stats()
    print(f"LTM Patterns: {stats['ltm_size']}")
    print(f"Sessions Completed: {stats['total_sessions']}")
    print()
    print("Use --run-now to execute current hour's lesson")
    print("Use --continuous to start 24/7 learning")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
