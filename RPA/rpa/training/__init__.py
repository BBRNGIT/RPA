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

from rpa.training.si_config import (
    SIConfiguration,
    ConfidenceConfig,
    MutationConfig,
    ReinforcementConfig,
    RetryConfigData,
    CycleConfig,
    PersistenceConfig,
    GapDetectionConfig,
    MonitoringConfig,
    SafetyConfig,
    get_si_config,
    create_self_improvement_config_from_yaml
)

__all__ = [
    # Self-improvement orchestrator
    'SelfImprovementOrchestrator',
    'SelfImprovementConfig',
    'ImprovementCycle',
    'SystemHealth',
    'create_self_improvement',
    'run_improvement_cycle',
    
    # Configuration
    'SIConfiguration',
    'ConfidenceConfig',
    'MutationConfig',
    'ReinforcementConfig',
    'RetryConfigData',
    'CycleConfig',
    'PersistenceConfig',
    'GapDetectionConfig',
    'MonitoringConfig',
    'SafetyConfig',
    'get_si_config',
    'create_self_improvement_config_from_yaml'
]
