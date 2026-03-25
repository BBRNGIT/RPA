"""
Autonomous Learning System Package

Provides continuous learning capabilities for the RPA AI:
- Skill-to-Curriculum conversion
- Per-minute learning engine
- Gap detection and prioritization
- External source curriculum generation
"""

from .skill_curriculum_converter import SkillCurriculumConverter, SkillCurriculum, CurriculumItem
from .learning_engine import AutonomousLearningEngine, LearningSession, LearningStats
from .gap_detector import GapDetector, KnowledgeGap, DomainBalance
from .source_manager import SourceManager, ExternalSource, CurriculumBatch

__all__ = [
    'SkillCurriculumConverter',
    'SkillCurriculum', 
    'CurriculumItem',
    'AutonomousLearningEngine',
    'LearningSession',
    'LearningStats',
    'GapDetector',
    'KnowledgeGap',
    'DomainBalance',
    'SourceManager',
    'ExternalSource',
    'CurriculumBatch'
]
