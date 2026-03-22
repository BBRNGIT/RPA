"""
Curriculum Ingestion Gate - Validate curriculum before ingestion.

This module ensures that curriculum data is properly structured, validated,
and safe for ingestion into the RPA learning system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
import re


@dataclass
class CurriculumBatch:
    """Represents a curriculum batch for validation."""
    batch_id: str
    domain: str
    hierarchy_level: int
    items: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "batch_id": self.batch_id,
            "domain": self.domain,
            "hierarchy_level": self.hierarchy_level,
            "items": self.items,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurriculumBatch":
        """Create from dictionary representation."""
        return cls(
            batch_id=data.get("batch_id", ""),
            domain=data.get("domain", ""),
            hierarchy_level=data.get("hierarchy_level", 0),
            items=data.get("items", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )

    def compute_hash(self) -> str:
        """Compute a hash of the batch for integrity checking."""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class IngestionResult:
    """Result of curriculum ingestion validation."""
    batch_id: str
    is_valid: bool
    items_accepted: int
    items_rejected: int
    rejection_reasons: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_time_ms: float = 0.0
    batch_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "batch_id": self.batch_id,
            "is_valid": self.is_valid,
            "items_accepted": self.items_accepted,
            "items_rejected": self.items_rejected,
            "rejection_reasons": self.rejection_reasons,
            "warnings": self.warnings,
            "validation_time_ms": self.validation_time_ms,
            "batch_hash": self.batch_hash,
        }


class CurriculumIngestionGate:
    """
    Gate for validating curriculum before ingestion into the RPA system.

    This class ensures that:
    - Curriculum structure is correct
    - Content is properly formatted
    - No malicious or malformed data enters the system
    - Hierarchy levels are appropriate
    - Composition references are valid
    """

    # Supported domains
    SUPPORTED_DOMAINS = {"english", "python", "javascript", "general"}

    # Required fields for curriculum items
    REQUIRED_ITEM_FIELDS = ["content"]

    # Optional fields with validation rules
    OPTIONAL_ITEM_FIELDS = {
        "label": str,
        "hierarchy_level": int,
        "composition": list,
        "related_patterns": list,
        "difficulty": int,
        "frequency": str,
        "metadata": dict,
    }

    # Maximum sizes
    MAX_BATCH_SIZE = 10000
    MAX_ITEM_CONTENT_LENGTH = 10000
    MAX_COMPOSITION_LENGTH = 100

    # Forbidden patterns (security)
    FORBIDDEN_PATTERNS = [
        r"<script.*?>",  # Script injection
        r"javascript:",  # JavaScript URLs
        r"data:",  # Data URLs
        r"eval\s*\(",  # Eval calls in content
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize the curriculum ingestion gate.

        Args:
            strict_mode: If True, reject batches with any validation errors.
                        If False, accept items that pass validation individually.
        """
        self.strict_mode = strict_mode
        self._ingested_hashes: Dict[str, datetime] = {}
        self._validation_stats: Dict[str, int] = {
            "batches_processed": 0,
            "items_accepted": 0,
            "items_rejected": 0,
        }

    def validate_batch(self, batch: CurriculumBatch) -> IngestionResult:
        """
        Validate a curriculum batch for ingestion.

        Args:
            batch: The curriculum batch to validate.

        Returns:
            IngestionResult with validation details.
        """
        start_time = datetime.now()
        rejection_reasons = []
        warnings = []

        # Validate batch structure
        if not batch.batch_id:
            rejection_reasons.append({
                "item_index": -1,
                "reason": "Missing batch_id",
                "severity": "critical",
            })

        if not batch.domain:
            rejection_reasons.append({
                "item_index": -1,
                "reason": "Missing domain",
                "severity": "critical",
            })
        elif batch.domain not in self.SUPPORTED_DOMAINS:
            rejection_reasons.append({
                "item_index": -1,
                "reason": f"Unsupported domain: {batch.domain}",
                "severity": "critical",
            })

        # Check batch size
        if len(batch.items) > self.MAX_BATCH_SIZE:
            rejection_reasons.append({
                "item_index": -1,
                "reason": f"Batch size {len(batch.items)} exceeds maximum {self.MAX_BATCH_SIZE}",
                "severity": "critical",
            })

        # Check for duplicate batches
        batch_hash = batch.compute_hash()
        if batch_hash in self._ingested_hashes:
            warnings.append(f"Batch with hash {batch_hash[:16]}... was previously ingested")

        # Validate hierarchy level
        if batch.hierarchy_level < 0:
            rejection_reasons.append({
                "item_index": -1,
                "reason": f"Invalid hierarchy level: {batch.hierarchy_level}",
                "severity": "critical",
            })

        # Validate individual items
        items_accepted = 0
        items_rejected = 0

        for idx, item in enumerate(batch.items):
            item_validation = self._validate_item(item, idx, batch.domain)
            if item_validation["is_valid"]:
                items_accepted += 1
            else:
                items_rejected += 1
                rejection_reasons.extend(item_validation["issues"])
            warnings.extend(item_validation.get("warnings", []))

        # Compute validation time
        validation_time = (datetime.now() - start_time).total_seconds() * 1000

        # Determine overall validity
        is_valid = len([r for r in rejection_reasons if r.get("severity") == "critical"]) == 0
        if self.strict_mode:
            is_valid = len(rejection_reasons) == 0

        # Update stats
        self._validation_stats["batches_processed"] += 1
        self._validation_stats["items_accepted"] += items_accepted
        self._validation_stats["items_rejected"] += items_rejected

        return IngestionResult(
            batch_id=batch.batch_id,
            is_valid=is_valid,
            items_accepted=items_accepted,
            items_rejected=items_rejected,
            rejection_reasons=rejection_reasons,
            warnings=warnings,
            validation_time_ms=validation_time,
            batch_hash=batch_hash,
        )

    def _validate_item(self, item: Dict[str, Any], index: int, domain: str) -> Dict[str, Any]:
        """
        Validate a single curriculum item.

        Args:
            item: The item to validate.
            index: The item index in the batch.
            domain: The domain of the batch.

        Returns:
            Dict with is_valid, issues, and warnings.
        """
        issues = []
        warnings = []

        # Check required fields
        for field in self.REQUIRED_ITEM_FIELDS:
            if field not in item:
                issues.append({
                    "item_index": index,
                    "reason": f"Missing required field: {field}",
                    "severity": "critical",
                })

        # Check content
        content = item.get("content", "")
        if not content:
            issues.append({
                "item_index": index,
                "reason": "Empty content",
                "severity": "critical",
            })
        elif len(content) > self.MAX_ITEM_CONTENT_LENGTH:
            issues.append({
                "item_index": index,
                "reason": f"Content length {len(content)} exceeds maximum {self.MAX_ITEM_CONTENT_LENGTH}",
                "severity": "critical",
            })

        # Check for forbidden patterns (security)
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append({
                    "item_index": index,
                    "reason": f"Forbidden pattern detected in content",
                    "severity": "critical",
                })

        # Validate optional fields
        for field, expected_type in self.OPTIONAL_ITEM_FIELDS.items():
            if field in item and not isinstance(item[field], expected_type):
                issues.append({
                    "item_index": index,
                    "reason": f"Invalid type for {field}: expected {expected_type.__name__}",
                    "severity": "warning",
                })

        # Validate composition
        composition = item.get("composition", [])
        if composition:
            if len(composition) > self.MAX_COMPOSITION_LENGTH:
                issues.append({
                    "item_index": index,
                    "reason": f"Composition length {len(composition)} exceeds maximum",
                    "severity": "warning",
                })

            # Check for empty composition elements
            if any(not c for c in composition):
                warnings.append(f"Item {index}: Empty element in composition")

        # Validate hierarchy level
        item_hl = item.get("hierarchy_level")
        if item_hl is not None and item_hl < 0:
            issues.append({
                "item_index": index,
                "reason": f"Invalid hierarchy level: {item_hl}",
                "severity": "warning",
            })

        # Validate difficulty
        difficulty = item.get("difficulty")
        if difficulty is not None and (difficulty < 1 or difficulty > 10):
            warnings.append(f"Item {index}: Difficulty {difficulty} outside typical range 1-10")

        # Domain-specific validation
        domain_issues = self._validate_domain_specific(item, index, domain)
        issues.extend(domain_issues)

        return {
            "is_valid": len([i for i in issues if i.get("severity") == "critical"]) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    def _validate_domain_specific(self, item: Dict[str, Any], index: int, domain: str) -> List[Dict[str, Any]]:
        """
        Apply domain-specific validation rules.

        Args:
            item: The item to validate.
            index: The item index.
            domain: The domain.

        Returns:
            List of validation issues.
        """
        issues = []
        content = item.get("content", "")

        if domain == "python":
            # Python-specific validation
            # Check for obvious syntax errors in code
            if "def " in content and ":" not in content:
                issues.append({
                    "item_index": index,
                    "reason": "Python function definition missing colon",
                    "severity": "warning",
                })

            # Check for unbalanced brackets
            if content.count("(") != content.count(")"):
                issues.append({
                    "item_index": index,
                    "reason": "Unbalanced parentheses in Python code",
                    "severity": "warning",
                })

        elif domain == "english":
            # English-specific validation
            # Check for very short content
            if len(content.split()) < 1:
                issues.append({
                    "item_index": index,
                    "reason": "English content appears too short",
                    "severity": "warning",
                })

        return issues

    def validate_json_file(self, file_path: str) -> IngestionResult:
        """
        Validate a curriculum JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            IngestionResult with validation details.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return IngestionResult(
                batch_id="",
                is_valid=False,
                items_accepted=0,
                items_rejected=0,
                rejection_reasons=[{
                    "item_index": -1,
                    "reason": f"Invalid JSON: {str(e)}",
                    "severity": "critical",
                }],
            )
        except Exception as e:
            return IngestionResult(
                batch_id="",
                is_valid=False,
                items_accepted=0,
                items_rejected=0,
                rejection_reasons=[{
                    "item_index": -1,
                    "reason": f"File error: {str(e)}",
                    "severity": "critical",
                }],
            )

        # Extract batch data
        batch = CurriculumBatch(
            batch_id=data.get("batch_id", data.get("lesson_id", "")),
            domain=data.get("domain", "general"),
            hierarchy_level=data.get("hierarchy_level", 0),
            items=data.get("items", [data] if "content" in data else []),
            metadata=data.get("metadata", {}),
        )

        return self.validate_batch(batch)

    def mark_ingested(self, batch_hash: str) -> None:
        """Mark a batch as successfully ingested."""
        self._ingested_hashes[batch_hash] = datetime.now()

    def is_duplicate(self, batch_hash: str) -> bool:
        """Check if a batch has been previously ingested."""
        return batch_hash in self._ingested_hashes

    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            **self._validation_stats,
            "unique_batches_seen": len(self._ingested_hashes),
        }

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self._validation_stats = {
            "batches_processed": 0,
            "items_accepted": 0,
            "items_rejected": 0,
        }
        self._ingested_hashes.clear()
