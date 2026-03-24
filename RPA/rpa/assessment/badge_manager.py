"""
Badge Manager - Award badges when AI passes curriculum level exams.

Badges are dev milestone markers and versioning points.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import uuid
import logging

from rpa.assessment.curriculum_registry import CurriculumRegistry
from rpa.memory.episodic import EpisodicMemory, EventType

logger = logging.getLogger(__name__)


@dataclass
class Badge:
    """
    Lightweight milestone marker awarded on exam pass.
    
    Doubles as a dev versioning/milestone point.
    """
    badge_id: str
    track_id: str
    level_id: str
    label: str              # e.g., "🎓 Kindergarten English"
    description: str = ""
    earned_at: datetime = field(default_factory=datetime.now)
    exam_score: float = 0.0
    exam_session_id: Optional[str] = None
    patterns_at_time: int = 0  # LTM pattern count when badge was earned
    version_tag: str = ""      # git-style tag: v0.3-english-kg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "badge_id": self.badge_id,
            "track_id": self.track_id,
            "level_id": self.level_id,
            "label": self.label,
            "description": self.description,
            "earned_at": self.earned_at.isoformat(),
            "exam_score": self.exam_score,
            "exam_session_id": self.exam_session_id,
            "patterns_at_time": self.patterns_at_time,
            "version_tag": self.version_tag,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Badge":
        """Create from dictionary."""
        return cls(
            badge_id=data["badge_id"],
            track_id=data["track_id"],
            level_id=data["level_id"],
            label=data["label"],
            description=data.get("description", ""),
            earned_at=datetime.fromisoformat(data["earned_at"]) if data.get("earned_at") else datetime.now(),
            exam_score=data.get("exam_score", 0.0),
            exam_session_id=data.get("exam_session_id"),
            patterns_at_time=data.get("patterns_at_time", 0),
            version_tag=data.get("version_tag", ""),
        )


class BadgeManager:
    """
    Manages badge creation, storage, and retrieval.
    
    Badges are awarded when the AI passes a curriculum level exam.
    They serve as:
    - Milestone markers for development
    - Versioning points for the AI's knowledge state
    - Display items in the UI
    """
    
    # Badge icons by track
    TRACK_ICONS = {
        "english": "📚",
        "python": "🐍",
        "finance": "💰",
        "physics": "🔬",
        "general": "🎓",
    }
    
    # Level abbreviations for version tags
    LEVEL_ABBREVS = {
        "english_kindergarten": "kg",
        "english_grade1": "g1",
        "english_grade2": "g2",
        "english_elementary": "elem",
        "python_junior": "jr",
        "python_mid": "mid",
        "python_senior": "sr",
    }
    
    def __init__(
        self,
        registry: Optional[CurriculumRegistry] = None,
        episodic: Optional[EpisodicMemory] = None,
        storage_path: Optional[str] = None,
        ltm_pattern_count: int = 0,
    ):
        """
        Initialize the BadgeManager.
        
        Args:
            registry: CurriculumRegistry for track/level info
            episodic: EpisodicMemory for event logging
            storage_path: Path to badges.json file
            ltm_pattern_count: Current LTM pattern count
        """
        self.registry = registry or CurriculumRegistry()
        self.episodic = episodic or EpisodicMemory()
        self.storage_path = Path(storage_path) if storage_path else None
        self.ltm_pattern_count = ltm_pattern_count
        
        # Badge storage
        self._badges: Dict[str, Badge] = {}
        self._by_track: Dict[str, List[str]] = {}  # track_id -> badge_ids
        
        # Load existing badges
        self._load_badges()
    
    def award_badge(
        self,
        track_id: str,
        level_id: str,
        exam_score: float,
        exam_session_id: Optional[str] = None,
    ) -> Optional[Badge]:
        """
        Award a badge for passing an exam.
        
        Args:
            track_id: Curriculum track ID
            level_id: Level ID passed
            exam_score: Score achieved
            exam_session_id: Related exam session
            
        Returns:
            Badge if awarded, None if already earned or invalid
        """
        # Check if already earned
        badge_key = f"{track_id}_{level_id}"
        if badge_key in self._badges:
            logger.info(f"Badge already earned: {badge_key}")
            return None
        
        # Get level info
        level = self.registry.get_level(track_id, level_id)
        if not level:
            logger.warning(f"Level not found: {track_id}/{level_id}")
            return None
        
        # Generate badge
        badge_id = f"badge_{uuid.uuid4().hex[:8]}"
        icon = self.TRACK_ICONS.get(track_id, "🎓")
        label = f"{icon} {level.label}"
        
        # Generate version tag
        version_tag = self._generate_version_tag(track_id, level_id)
        
        badge = Badge(
            badge_id=badge_id,
            track_id=track_id,
            level_id=level_id,
            label=label,
            description=f"Passed {level.label} exam with {exam_score:.0%} score",
            exam_score=exam_score,
            exam_session_id=exam_session_id,
            patterns_at_time=self.ltm_pattern_count,
            version_tag=version_tag,
        )
        
        # Store badge
        self._badges[badge_key] = badge
        
        # Update track index
        if track_id not in self._by_track:
            self._by_track[track_id] = []
        self._by_track[track_id].append(badge_id)
        
        # Log event
        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id=exam_session_id or "badge_award",
            data={
                "type": "badge_awarded",
                "badge_id": badge_id,
                "track_id": track_id,
                "level_id": level_id,
                "exam_score": exam_score,
                "version_tag": version_tag,
            },
        )
        
        # Save
        self._save_badges()
        
        logger.info(f"Awarded badge: {label} (version: {version_tag})")
        
        return badge
    
    def _generate_version_tag(self, track_id: str, level_id: str) -> str:
        """Generate a version tag for the badge."""
        # Count badges in this track
        track_count = len(self._by_track.get(track_id, []))
        
        # Get level abbreviation
        level_abbrev = self.LEVEL_ABBREVS.get(level_id, level_id.split("_")[-1][:3])
        
        # Major version from total badges
        major = len(self._badges) // 10 + 1
        minor = len(self._badges) % 10
        
        return f"v{major}.{minor}-{track_id}-{level_abbrev}"
    
    def get_badge(self, track_id: str, level_id: str) -> Optional[Badge]:
        """Get a specific badge."""
        badge_key = f"{track_id}_{level_id}"
        return self._badges.get(badge_key)
    
    def get_all_badges(self) -> List[Badge]:
        """Get all earned badges."""
        return list(self._badges.values())
    
    def get_badges_by_track(self, track_id: str) -> List[Badge]:
        """Get all badges for a track."""
        badge_ids = self._by_track.get(track_id, [])
        return [self._badges[bid] for bid in badge_ids if bid in self._badges]
    
    def get_latest_badge(self) -> Optional[Badge]:
        """Get the most recently earned badge."""
        if not self._badges:
            return None
        return max(self._badges.values(), key=lambda b: b.earned_at)
    
    def get_highest_badge(self, track_id: str) -> Optional[Badge]:
        """Get the highest level badge in a track."""
        badges = self.get_badges_by_track(track_id)
        if not badges:
            return None
        
        # Sort by level order
        levels = self.registry.list_levels(track_id)
        level_order = {l.level_id: l.order for l in levels}
        
        return max(badges, key=lambda b: level_order.get(b.level_id, 0))
    
    def _load_badges(self) -> None:
        """Load badges from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            
            for badge_data in data.get("badges", []):
                badge = Badge.from_dict(badge_data)
                badge_key = f"{badge.track_id}_{badge.level_id}"
                self._badges[badge_key] = badge
                
                if badge.track_id not in self._by_track:
                    self._by_track[badge.track_id] = []
                self._by_track[badge.track_id].append(badge.badge_id)
            
            logger.info(f"Loaded {len(self._badges)} badges from storage")
            
        except Exception as e:
            logger.warning(f"Failed to load badges: {e}")
    
    def _save_badges(self) -> None:
        """Save badges to storage."""
        if not self.storage_path:
            return
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "badges": [b.to_dict() for b in self._badges.values()],
            "total": len(self._badges),
            "last_updated": datetime.now().isoformat(),
        }
        
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get badge statistics."""
        return {
            "total_badges": len(self._badges),
            "by_track": {
                track: len(badges)
                for track, badges in self._by_track.items()
            },
            "latest_badge": self.get_latest_badge().to_dict() if self._badges else None,
        }
