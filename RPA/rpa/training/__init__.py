"""
RPA Training Module

Provides training, learning, and self-improvement capabilities.
"""

from rpa.training.self_improvement import (
    SelfImprovementOrchestrator,
    SelfImprovementConfig,
    ImprovementCycle,
    SystemHealth,
    create_self_improvement,
    run_improvement_cycle
)

__all__ = [
    'SelfImprovementOrchestrator',
    'SelfImprovementConfig',
    'ImprovementCycle',
    'SystemHealth',
    'create_self_improvement',
    'run_improvement_cycle'
]
