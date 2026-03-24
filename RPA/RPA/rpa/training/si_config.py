"""
RPA Self-Improvement Configuration Loader

Loads and validates configuration from YAML file.
Provides domain-specific overrides and runtime updates.

Ticket: SI-003
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "self_improvement.yaml"


@dataclass
class ConfidenceConfig:
    """Confidence threshold configuration."""
    default_threshold: float = 0.7
    low_confidence_threshold: float = 0.3
    high_confidence_threshold: float = 0.8
    execution_threshold: float = 0.5
    success_boost: float = 0.05
    failure_penalty: float = 0.1


@dataclass
class MutationConfig:
    """Mutation behavior configuration."""
    rate: float = 0.1
    max_per_cycle: int = 10
    auto_enabled: bool = True
    min_failures_for_mutation: int = 2
    strategy_weights: Dict[str, float] = field(default_factory=lambda: {
        'parameter_tweak': 0.4,
        'structure_rearrange': 0.3,
        'cross_pattern_merge': 0.2,
        'fix': 0.1
    })
    history_retention_days: int = 30
    max_versions: int = 10


@dataclass
class ReinforcementConfig:
    """Reinforcement tracking configuration."""
    decay_rate: float = 0.05
    min_strength_threshold: float = 0.2
    strong_pattern_threshold: float = 0.7
    reinforce_amount: float = 0.1
    max_strength: float = 1.0
    min_strength_floor: float = 0.1
    stability_threshold: int = 5


@dataclass
class RetryConfigData:
    """Retry behavior configuration."""
    max_attempts: int = 3
    backoff_multiplier: float = 1.5
    initial_delay: float = 1.0
    max_delay: float = 30.0
    mutate_on_retry: bool = True


@dataclass
class CycleConfig:
    """Cycle execution configuration."""
    patterns_per_cycle: int = 50
    gap_closure_priority: bool = True
    cycles_per_day: int = 3
    schedule_morning: int = 6
    schedule_midday: int = 12
    schedule_evening: int = 22
    max_duration: int = 300


@dataclass
class PersistenceConfig:
    """State persistence configuration."""
    auto_save: bool = True
    save_interval: int = 5
    state_file: str = "self_improvement_state.json"
    backup_count: int = 5


@dataclass
class GapDetectionConfig:
    """Gap detection configuration."""
    enabled: bool = True
    max_gaps_per_cycle: int = 10
    min_severity: int = 3
    auto_generate_goals: bool = True
    detect_types: list = field(default_factory=lambda: [
        'structural', 'semantic', 'coverage', 'confidence'
    ])


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""
    enabled: bool = True
    history_size: int = 100
    health_check_interval: int = 10
    alert_min_success_rate: float = 0.6
    alert_max_weak_pattern_ratio: float = 0.3
    alert_max_open_gaps: int = 50


@dataclass
class SafetyConfig:
    """Safety constraint configuration."""
    max_daily_mutations: int = 100
    validate_mutations: bool = True
    auto_rollback_threshold: int = 3
    preserve_older_than: int = 30
    protected_tags: list = field(default_factory=lambda: ['core', 'safety', 'system'])


class SIConfiguration:
    """
    Self-Improvement Configuration Manager.
    
    Loads configuration from YAML, provides access to typed config sections,
    and supports domain-specific overrides.
    
    Usage:
        config = SIConfiguration()
        config.load()
        
        # Access settings
        threshold = config.confidence.default_threshold
        rate = config.mutation.rate
        
        # Get domain-specific config
        python_config = config.get_domain_config('python')
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML config file (default: config/self_improvement.yaml)
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._raw_config: Dict[str, Any] = {}
        self._loaded = False
        
        # Typed config sections
        self.confidence = ConfidenceConfig()
        self.mutation = MutationConfig()
        self.reinforcement = ReinforcementConfig()
        self.retry = RetryConfigData()
        self.cycle = CycleConfig()
        self.persistence = PersistenceConfig()
        self.gap_detection = GapDetectionConfig()
        self.monitoring = MonitoringConfig()
        self.safety = SafetyConfig()
        
        # Domain overrides
        self._domain_overrides: Dict[str, Dict] = {}
    
    def load(self) -> bool:
        """
        Load configuration from YAML file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            logger.info("Using default configuration")
            self._loaded = True
            return True
        
        try:
            with open(self.config_path, 'r') as f:
                self._raw_config = yaml.safe_load(f) or {}
            
            self._parse_config()
            self._loaded = True
            logger.info(f"Loaded configuration from {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            self._loaded = True
            return False
    
    def _parse_config(self):
        """Parse raw YAML config into typed sections."""
        
        # Confidence
        if 'confidence' in self._raw_config:
            conf = self._raw_config['confidence']
            self.confidence = ConfidenceConfig(
                default_threshold=conf.get('default_threshold', 0.7),
                low_confidence_threshold=conf.get('low_confidence_threshold', 0.3),
                high_confidence_threshold=conf.get('high_confidence_threshold', 0.8),
                execution_threshold=conf.get('execution_threshold', 0.5),
                success_boost=conf.get('success_boost', 0.05),
                failure_penalty=conf.get('failure_penalty', 0.1)
            )
        
        # Mutation
        if 'mutation' in self._raw_config:
            mut = self._raw_config['mutation']
            self.mutation = MutationConfig(
                rate=mut.get('rate', 0.1),
                max_per_cycle=mut.get('max_per_cycle', 10),
                auto_enabled=mut.get('auto_enabled', True),
                min_failures_for_mutation=mut.get('min_failures_for_mutation', 2),
                strategy_weights=mut.get('strategy_weights', self.mutation.strategy_weights),
                history_retention_days=mut.get('history_retention_days', 30),
                max_versions=mut.get('max_versions', 10)
            )
        
        # Reinforcement
        if 'reinforcement' in self._raw_config:
            reinf = self._raw_config['reinforcement']
            self.reinforcement = ReinforcementConfig(
                decay_rate=reinf.get('decay_rate', 0.05),
                min_strength_threshold=reinf.get('min_strength_threshold', 0.2),
                strong_pattern_threshold=reinf.get('strong_pattern_threshold', 0.7),
                reinforce_amount=reinf.get('reinforce_amount', 0.1),
                max_strength=reinf.get('max_strength', 1.0),
                min_strength_floor=reinf.get('min_strength_floor', 0.1),
                stability_threshold=reinf.get('stability_threshold', 5)
            )
        
        # Retry
        if 'retry' in self._raw_config:
            ret = self._raw_config['retry']
            self.retry = RetryConfigData(
                max_attempts=ret.get('max_attempts', 3),
                backoff_multiplier=ret.get('backoff_multiplier', 1.5),
                initial_delay=ret.get('initial_delay', 1.0),
                max_delay=ret.get('max_delay', 30.0),
                mutate_on_retry=ret.get('mutate_on_retry', True)
            )
        
        # Cycle
        if 'cycle' in self._raw_config:
            cyc = self._raw_config['cycle']
            schedule = cyc.get('schedule', {})
            self.cycle = CycleConfig(
                patterns_per_cycle=cyc.get('patterns_per_cycle', 50),
                gap_closure_priority=cyc.get('gap_closure_priority', True),
                cycles_per_day=cyc.get('cycles_per_day', 3),
                schedule_morning=schedule.get('morning', 6),
                schedule_midday=schedule.get('midday', 12),
                schedule_evening=schedule.get('evening', 22),
                max_duration=cyc.get('max_duration', 300)
            )
        
        # Persistence
        if 'persistence' in self._raw_config:
            pers = self._raw_config['persistence']
            self.persistence = PersistenceConfig(
                auto_save=pers.get('auto_save', True),
                save_interval=pers.get('save_interval', 5),
                state_file=pers.get('state_file', 'self_improvement_state.json'),
                backup_count=pers.get('backup_count', 5)
            )
        
        # Gap Detection
        if 'gap_detection' in self._raw_config:
            gap = self._raw_config['gap_detection']
            self.gap_detection = GapDetectionConfig(
                enabled=gap.get('enabled', True),
                max_gaps_per_cycle=gap.get('max_gaps_per_cycle', 10),
                min_severity=gap.get('min_severity', 3),
                auto_generate_goals=gap.get('auto_generate_goals', True),
                detect_types=gap.get('detect_types', self.gap_detection.detect_types)
            )
        
        # Monitoring
        if 'monitoring' in self._raw_config:
            mon = self._raw_config['monitoring']
            alerts = mon.get('alerts', {})
            self.monitoring = MonitoringConfig(
                enabled=mon.get('enabled', True),
                history_size=mon.get('history_size', 100),
                health_check_interval=mon.get('health_check_interval', 10),
                alert_min_success_rate=alerts.get('min_success_rate', 0.6),
                alert_max_weak_pattern_ratio=alerts.get('max_weak_pattern_ratio', 0.3),
                alert_max_open_gaps=alerts.get('max_open_gaps', 50)
            )
        
        # Safety
        if 'safety' in self._raw_config:
            saf = self._raw_config['safety']
            self.safety = SafetyConfig(
                max_daily_mutations=saf.get('max_daily_mutations', 100),
                validate_mutations=saf.get('validate_mutations', True),
                auto_rollback_threshold=saf.get('auto_rollback_threshold', 3),
                preserve_older_than=saf.get('preserve_older_than', 30),
                protected_tags=saf.get('protected_tags', self.safety.protected_tags)
            )
        
        # Domain overrides
        if 'domains' in self._raw_config:
            self._domain_overrides = self._raw_config['domains']
    
    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """
        Get configuration with domain-specific overrides applied.
        
        Args:
            domain: Domain name (e.g., 'python', 'medicine', 'finance')
            
        Returns:
            Dict with merged configuration for the domain
        """
        base_config = self.to_dict()
        
        if domain in self._domain_overrides:
            overrides = self._domain_overrides[domain]
            return self._deep_merge(base_config, overrides)
        
        return base_config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'confidence': asdict(self.confidence),
            'mutation': asdict(self.mutation),
            'reinforcement': asdict(self.reinforcement),
            'retry': asdict(self.retry),
            'cycle': asdict(self.cycle),
            'persistence': asdict(self.persistence),
            'gap_detection': asdict(self.gap_detection),
            'monitoring': asdict(self.monitoring),
            'safety': asdict(self.safety)
        }
    
    def save(self, path: Optional[Path] = None) -> bool:
        """
        Save current configuration to YAML file.
        
        Args:
            path: Path to save to (default: self.config_path)
            
        Returns:
            True if saved successfully
        """
        save_path = path or self.config_path
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def update(self, section: str, key: str, value: Any) -> bool:
        """
        Update a specific configuration value.
        
        Args:
            section: Config section (e.g., 'confidence', 'mutation')
            key: Key within section
            value: New value
            
        Returns:
            True if updated successfully
        """
        section_obj = getattr(self, section, None)
        if section_obj is None:
            logger.warning(f"Unknown config section: {section}")
            return False
        
        if not hasattr(section_obj, key):
            logger.warning(f"Unknown config key: {section}.{key}")
            return False
        
        setattr(section_obj, key, value)
        logger.info(f"Updated {section}.{key} = {value}")
        return True
    
    @property
    def is_loaded(self) -> bool:
        """Check if configuration has been loaded."""
        return self._loaded
    
    def __repr__(self) -> str:
        return f"SIConfiguration(loaded={self._loaded}, path={self.config_path})"


# Singleton instance for convenience
_config_instance: Optional[SIConfiguration] = None


def get_si_config(config_path: Optional[Path] = None, reload: bool = False) -> SIConfiguration:
    """
    Get the global SI configuration instance.
    
    Args:
        config_path: Path to config file (only used on first call or reload)
        reload: Force reload from file
        
    Returns:
        SIConfiguration instance
    """
    global _config_instance
    
    if _config_instance is None or reload:
        _config_instance = SIConfiguration(config_path)
        _config_instance.load()
    
    return _config_instance


def create_self_improvement_config_from_yaml(
    config_path: Optional[Path] = None
) -> 'SelfImprovementConfig':
    """
    Create SelfImprovementConfig from YAML file.
    
    This bridges the YAML configuration with the dataclass used
    by SelfImprovementOrchestrator.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        SelfImprovementConfig populated from YAML
    """
    from rpa.training.self_improvement import SelfImprovementConfig
    
    # Create a fresh config instance (not using singleton) if path is specified
    if config_path is not None:
        si_config = SIConfiguration(config_path)
        si_config.load()
    else:
        # Use singleton for default path
        si_config = get_si_config()
    
    return SelfImprovementConfig(
        confidence_threshold=si_config.confidence.default_threshold,
        low_confidence_threshold=si_config.confidence.low_confidence_threshold,
        high_confidence_threshold=si_config.confidence.high_confidence_threshold,
        mutation_rate=si_config.mutation.rate,
        max_mutations_per_cycle=si_config.mutation.max_per_cycle,
        enable_auto_mutation=si_config.mutation.auto_enabled,
        reinforcement_decay=si_config.reinforcement.decay_rate,
        min_strength_threshold=si_config.reinforcement.min_strength_threshold,
        strong_pattern_threshold=si_config.reinforcement.strong_pattern_threshold,
        max_retry_attempts=si_config.retry.max_attempts,
        retry_backoff_factor=si_config.retry.backoff_multiplier,
        patterns_per_cycle=si_config.cycle.patterns_per_cycle,
        gap_closure_priority=si_config.cycle.gap_closure_priority,
        auto_save=si_config.persistence.auto_save,
        save_interval_cycles=si_config.persistence.save_interval
    )
