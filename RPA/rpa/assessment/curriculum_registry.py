"""
Curriculum Registry - Domain-specific learning tracks with level ladders.

Maps curriculum levels to exam datasets, pass thresholds, and badges.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class TrackType(Enum):
    """Types of curriculum tracks."""
    ENGLISH = "english"
    PYTHON = "python"
    FINANCE = "finance"
    PHYSICS = "physics"
    GENERAL = "general"


@dataclass
class CurriculumLevel:
    """A single level within a curriculum track."""
    level_id: str              # e.g., "english_kindergarten"
    label: str                 # "Kindergarten", "Junior Coder"
    description: str
    exam_dataset: str          # HF dataset or "manual"
    exam_subset: Optional[str] = None  # HF subset filter
    pass_threshold: float = 0.8  # 80% correct to pass
    badge_id: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    order: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level_id": self.level_id,
            "label": self.label,
            "description": self.description,
            "exam_dataset": self.exam_dataset,
            "exam_subset": self.exam_subset,
            "pass_threshold": self.pass_threshold,
            "badge_id": self.badge_id,
            "prerequisites": self.prerequisites,
            "order": self.order,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurriculumLevel":
        """Create from dictionary."""
        return cls(
            level_id=data["level_id"],
            label=data["label"],
            description=data.get("description", ""),
            exam_dataset=data.get("exam_dataset", "manual"),
            exam_subset=data.get("exam_subset"),
            pass_threshold=data.get("pass_threshold", 0.8),
            badge_id=data.get("badge_id"),
            prerequisites=data.get("prerequisites", []),
            order=data.get("order", 0),
        )


@dataclass
class CurriculumTrack:
    """
    A domain-specific learning ladder with levels.
    
    Examples:
        - English: Kindergarten → Grade 1 → Grade 2 → ...
        - Python: Junior → Mid → Senior
    """
    track_id: str              # "english", "python"
    track_type: TrackType
    name: str                  # "English Language", "Python Programming"
    description: str
    levels: List[CurriculumLevel] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "track_id": self.track_id,
            "track_type": self.track_type.value,
            "name": self.name,
            "description": self.description,
            "levels": [l.to_dict() for l in self.levels],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurriculumTrack":
        """Create from dictionary."""
        return cls(
            track_id=data["track_id"],
            track_type=TrackType(data.get("track_type", "general")),
            name=data["name"],
            description=data.get("description", ""),
            levels=[CurriculumLevel.from_dict(l) for l in data.get("levels", [])],
        )
    
    def get_level(self, level_id: str) -> Optional[CurriculumLevel]:
        """Get a specific level by ID."""
        for level in self.levels:
            if level.level_id == level_id:
                return level
        return None
    
    def get_next_level(self, level_id: str) -> Optional[CurriculumLevel]:
        """Get the next level after a given level."""
        for i, level in enumerate(self.levels):
            if level.level_id == level_id and i + 1 < len(self.levels):
                return self.levels[i + 1]
        return None


class CurriculumRegistry:
    """
    Manages all curriculum tracks and levels.
    
    The registry:
    - Loads track definitions from JSON config files
    - Maps levels to exam datasets and pass thresholds
    - Integrates with ExamEngine and BadgeManager
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the CurriculumRegistry.
        
        Args:
            config_dir: Directory containing track JSON files
        """
        self._tracks: Dict[str, CurriculumTrack] = {}
        self._config_dir = Path(config_dir) if config_dir else None
        
        # Load default tracks
        self._load_default_tracks()
        
        # Load from config directory if provided
        if self._config_dir and self._config_dir.exists():
            self._load_from_config()
    
    def _load_default_tracks(self) -> None:
        """Load default curriculum tracks."""
        # English Track
        english_track = CurriculumTrack(
            track_id="english",
            track_type=TrackType.ENGLISH,
            name="English Language",
            description="English language proficiency curriculum",
            levels=[
                CurriculumLevel(
                    level_id="english_kindergarten",
                    label="Kindergarten",
                    description="Basic vocabulary and simple sentences",
                    exam_dataset="manual",
                    pass_threshold=0.7,
                    badge_id="badge_english_kg",
                    order=1,
                ),
                CurriculumLevel(
                    level_id="english_grade1",
                    label="Grade 1",
                    description="Simple reading comprehension",
                    exam_dataset="squad",
                    pass_threshold=0.75,
                    badge_id="badge_english_g1",
                    prerequisites=["english_kindergarten"],
                    order=2,
                ),
                CurriculumLevel(
                    level_id="english_grade2",
                    label="Grade 2",
                    description="Intermediate reading and grammar",
                    exam_dataset="squad",
                    pass_threshold=0.75,
                    badge_id="badge_english_g2",
                    prerequisites=["english_grade1"],
                    order=3,
                ),
                CurriculumLevel(
                    level_id="english_elementary",
                    label="Elementary",
                    description="Full elementary English proficiency",
                    exam_dataset="mmlu",
                    exam_subset="global_facts",
                    pass_threshold=0.8,
                    badge_id="badge_english_elem",
                    prerequisites=["english_grade2"],
                    order=4,
                ),
            ],
        )
        
        # Python Track
        python_track = CurriculumTrack(
            track_id="python",
            track_type=TrackType.PYTHON,
            name="Python Programming",
            description="Python coding proficiency curriculum",
            levels=[
                CurriculumLevel(
                    level_id="python_junior",
                    label="Junior Coder",
                    description="Basic Python syntax and simple functions",
                    exam_dataset="manual",
                    pass_threshold=0.7,
                    badge_id="badge_python_jr",
                    order=1,
                ),
                CurriculumLevel(
                    level_id="python_mid",
                    label="Mid Coder",
                    description="Object-oriented programming and algorithms",
                    exam_dataset="humaneval",
                    pass_threshold=0.6,
                    badge_id="badge_python_mid",
                    prerequisites=["python_junior"],
                    order=2,
                ),
                CurriculumLevel(
                    level_id="python_senior",
                    label="Senior Coder",
                    description="Advanced patterns and optimization",
                    exam_dataset="humaneval",
                    pass_threshold=0.75,
                    badge_id="badge_python_sr",
                    prerequisites=["python_mid"],
                    order=3,
                ),
            ],
        )
        
        # Register tracks
        self._tracks["english"] = english_track
        self._tracks["python"] = python_track
        
        logger.info(f"Loaded {len(self._tracks)} default curriculum tracks")
    
    def _load_from_config(self) -> None:
        """Load tracks from config directory."""
        tracks_dir = self._config_dir / "tracks"
        if not tracks_dir.exists():
            return
        
        for json_file in tracks_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                track = CurriculumTrack.from_dict(data)
                self._tracks[track.track_id] = track
                logger.info(f"Loaded curriculum track: {track.track_id}")
            except Exception as e:
                logger.warning(f"Failed to load track {json_file}: {e}")
    
    def register_track(self, track: CurriculumTrack) -> None:
        """Register a new curriculum track."""
        self._tracks[track.track_id] = track
        logger.info(f"Registered track: {track.track_id}")
    
    def get_track(self, track_id: str) -> Optional[CurriculumTrack]:
        """Get a curriculum track by ID."""
        return self._tracks.get(track_id)
    
    def get_level(self, track_id: str, level_id: str) -> Optional[CurriculumLevel]:
        """Get a specific level from a track."""
        track = self.get_track(track_id)
        if track:
            return track.get_level(level_id)
        return None
    
    def list_tracks(self) -> List[CurriculumTrack]:
        """List all registered tracks."""
        return list(self._tracks.values())
    
    def list_levels(self, track_id: str) -> List[CurriculumLevel]:
        """List all levels in a track."""
        track = self.get_track(track_id)
        if track:
            return sorted(track.levels, key=lambda l: l.order)
        return []
    
    def get_starting_level(self, track_id: str) -> Optional[CurriculumLevel]:
        """Get the first level in a track."""
        levels = self.list_levels(track_id)
        return levels[0] if levels else None
    
    def can_take_level(self, track_id: str, level_id: str, 
                       completed_levels: List[str]) -> bool:
        """Check if prerequisites are met for a level."""
        level = self.get_level(track_id, level_id)
        if not level:
            return False
        
        for prereq in level.prerequisites:
            if prereq not in completed_levels:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Export registry to dictionary."""
        return {
            track_id: track.to_dict()
            for track_id, track in self._tracks.items()
        }
    
    def save(self, path: str) -> None:
        """Save registry to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
