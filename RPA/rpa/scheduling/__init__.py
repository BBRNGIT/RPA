"""
RPA Scheduling Module

Provides scheduling systems for learning:
- DailyTimetable: Daily learning schedule
- AcceleratedLearningScheduler: Hourly learning with tests and exams
"""

from rpa.scheduling.daily_timetable import (
    TimetableScheduler,
    DailyJobExecutor,
    ScheduledTask,
    TaskType,
    TaskPriority,
)

from rpa.scheduling.accelerated_learning import (
    AcceleratedLearningScheduler,
    ScheduledLesson,
    LearningResult,
    LearningPhase,
)

__all__ = [
    # Daily Timetable
    "TimetableScheduler",
    "DailyJobExecutor",
    "ScheduledTask",
    "TaskType",
    "TaskPriority",
    # Accelerated Learning
    "AcceleratedLearningScheduler",
    "ScheduledLesson",
    "LearningResult",
    "LearningPhase",
]
