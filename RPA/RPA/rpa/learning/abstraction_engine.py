"""
AbstractionEngine - Concept formation and pattern abstraction for RPA.

Provides intelligent abstraction capabilities:
- Pattern generalization
- Concept formation from examples
- Hierarchical abstraction
- Cross-domain concept mapping
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class AbstractConcept:
    """Represents an abstract concept formed from patterns."""
    concept_id: str
    name: str
    description: str
    abstraction_level: int  # 1=surface, 2=structural, 3=semantic
    source_patterns: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    counter_examples: List[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "description": self.description,
            "abstraction_level": self.abstraction_level,
            "source_patterns": self.source_patterns,
            "attributes": self.attributes,
            "constraints": self.constraints,
            "examples": self.examples,
            "counter_examples": self.counter_examples,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class AbstractionRule:
    """Rule for forming abstractions."""
    rule_id: str
    rule_type: str  # generalize, specialize, combine, transform
    condition: str  # When to apply this rule
    transformation: str  # How to transform
    confidence: float = 0.5
    success_count: int = 0
    failure_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "condition": self.condition,
            "transformation": self.transformation,
            "confidence": self.confidence,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count),
        }


class AbstractionEngine:
    """
    Intelligent abstraction and concept formation system.

    Forms higher-level concepts from patterns and enables
    cross-domain knowledge transfer.
    """

    # Abstraction levels
    LEVEL_SURFACE = 1     # Direct pattern features
    LEVEL_STRUCTURAL = 2  # Structural relationships
    LEVEL_SEMANTIC = 3    # Meaning and purpose

    def __init__(self):
        """Initialize the AbstractionEngine."""
        self._concepts: Dict[str, AbstractConcept] = {}
        self._rules: Dict[str, AbstractionRule] = {}
        self._pattern_index: Dict[str, Set[str]] = {}  # pattern -> concept IDs
        self._abstraction_history: List[Dict[str, Any]] = []
        self._max_history = 200

        # Initialize default rules
        self._initialize_rules()

    def _initialize_rules(self) -> None:
        """Initialize default abstraction rules."""
        default_rules = [
            {
                "rule_id": "common_suffix",
                "rule_type": "generalize",
                "condition": "Multiple patterns share common suffix",
                "transformation": "Extract suffix as abstract concept",
            },
            {
                "rule_id": "common_structure",
                "rule_type": "generalize",
                "condition": "Multiple patterns share structural pattern",
                "transformation": "Create structural abstraction",
            },
            {
                "rule_id": "frequency_based",
                "rule_type": "generalize",
                "condition": "Pattern occurs frequently across contexts",
                "transformation": "Promote to abstract concept",
            },
            {
                "rule_id": "hierarchy_based",
                "rule_type": "combine",
                "condition": "Patterns at same hierarchy level share attributes",
                "transformation": "Create parent concept",
            },
            {
                "rule_id": "cross_domain",
                "rule_type": "transform",
                "condition": "Similar patterns exist in different domains",
                "transformation": "Create cross-domain abstraction",
            },
        ]

        for rule_data in default_rules:
            rule = AbstractionRule(**rule_data)
            self._rules[rule.rule_id] = rule

    def form_concept(
        self,
        patterns: List[Dict[str, Any]],
        name: Optional[str] = None,
        description: Optional[str] = None,
        abstraction_level: int = LEVEL_STRUCTURAL,
    ) -> AbstractConcept:
        """
        Form an abstract concept from patterns.

        Args:
            patterns: List of pattern dictionaries
            name: Optional name for the concept
            description: Optional description
            abstraction_level: Level of abstraction (1-3)

        Returns:
            The formed AbstractConcept
        """
        import uuid
        concept_id = f"concept_{uuid.uuid4().hex[:8]}"

        # Extract common features
        common_features = self._extract_common_features(patterns)
        
        # Generate name if not provided
        if not name:
            name = self._generate_concept_name(common_features, patterns)

        # Generate description if not provided
        if not description:
            description = self._generate_description(common_features, patterns)

        # Extract constraints
        constraints = self._extract_constraints(patterns, common_features)

        # Extract examples
        examples = [p.get("content", str(p)) for p in patterns[:5]]

        # Calculate confidence
        confidence = self._calculate_confidence(patterns, common_features)

        # Create concept
        concept = AbstractConcept(
            concept_id=concept_id,
            name=name,
            description=description,
            abstraction_level=abstraction_level,
            source_patterns=[p.get("id", str(i)) for i, p in enumerate(patterns)],
            attributes=common_features,
            constraints=constraints,
            examples=examples,
            confidence=confidence,
        )

        # Store concept
        self._concepts[concept_id] = concept

        # Update pattern index
        for pattern_id in concept.source_patterns:
            if pattern_id not in self._pattern_index:
                self._pattern_index[pattern_id] = set()
            self._pattern_index[pattern_id].add(concept_id)

        # Record in history
        self._record_abstraction("form_concept", concept_id, len(patterns))

        return concept

    def _extract_common_features(
        self,
        patterns: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract common features from patterns."""
        if not patterns:
            return {}

        common = {}

        # Check for common attributes
        all_keys = set()
        for p in patterns:
            all_keys.update(p.keys())

        for key in all_keys:
            values = [p.get(key) for p in patterns if key in p]
            if len(values) == len(patterns):
                # All patterns have this key
                unique_values = set(str(v) for v in values)
                if len(unique_values) == 1:
                    # All have same value
                    common[key] = values[0]
                elif len(unique_values) <= len(patterns) * 0.3:
                    # Most values are similar
                    counter = Counter(str(v) for v in values)
                    most_common = counter.most_common(1)[0]
                    if most_common[1] >= len(patterns) * 0.5:
                        common[f"{key}_dominant"] = most_common[0]

        # Check for structural patterns
        compositions = [p.get("composition", []) for p in patterns]
        if all(compositions):
            common["has_composition"] = True
            # Find common elements
            if compositions:
                common_elements = set(compositions[0])
                for comp in compositions[1:]:
                    common_elements &= set(comp)
                if common_elements:
                    common["shared_elements"] = list(common_elements)

        # Check for hierarchy patterns
        hierarchy_levels = [p.get("hierarchy_level") for p in patterns]
        if all(h is not None for h in hierarchy_levels):
            common["hierarchy_range"] = (min(hierarchy_levels), max(hierarchy_levels))

        return common

    def _generate_concept_name(
        self,
        features: Dict[str, Any],
        patterns: List[Dict[str, Any]],
    ) -> str:
        """Generate a name for the concept."""
        # Try to use domain
        domains = [p.get("domain") for p in patterns if p.get("domain")]
        if domains:
            domain = Counter(domains).most_common(1)[0][0]
            return f"{domain.title()}Concept_{len(self._concepts) + 1}"

        # Use hierarchy level
        levels = [p.get("hierarchy_level") for p in patterns if p.get("hierarchy_level") is not None]
        if levels:
            avg_level = sum(levels) / len(levels)
            return f"Level{int(avg_level)}Concept_{len(self._concepts) + 1}"

        return f"AbstractConcept_{len(self._concepts) + 1}"

    def _generate_description(
        self,
        features: Dict[str, Any],
        patterns: List[Dict[str, Any]],
    ) -> str:
        """Generate a description for the concept."""
        parts = []

        if "shared_elements" in features:
            parts.append(f"Contains shared elements: {features['shared_elements']}")

        if "hierarchy_range" in features:
            lo, hi = features["hierarchy_range"]
            parts.append(f"Hierarchy level range: {lo}-{hi}")

        if "has_composition" in features:
            parts.append("Has compositional structure")

        if parts:
            return " | ".join(parts)
        else:
            return f"Abstract concept formed from {len(patterns)} patterns"

    def _extract_constraints(
        self,
        patterns: List[Dict[str, Any]],
        common_features: Dict[str, Any],
    ) -> List[str]:
        """Extract constraints for the concept."""
        constraints = []

        # Size constraints
        sizes = [len(p.get("composition", [])) for p in patterns if p.get("composition")]
        if sizes:
            constraints.append(f"composition_length >= {min(sizes)}")
            constraints.append(f"composition_length <= {max(sizes)}")

        # Type constraints
        types = set(p.get("type") for p in patterns if p.get("type"))
        if len(types) == 1:
            constraints.append(f"type == '{list(types)[0]}'")

        # Domain constraints
        domains = set(p.get("domain") for p in patterns if p.get("domain"))
        if len(domains) == 1:
            constraints.append(f"domain == '{list(domains)[0]}'")

        return constraints

    def _calculate_confidence(
        self,
        patterns: List[Dict[str, Any]],
        common_features: Dict[str, Any],
    ) -> float:
        """Calculate confidence score for the abstraction."""
        if not patterns or not common_features:
            return 0.0

        # Base confidence from pattern count
        count_score = min(1.0, len(patterns) / 5)

        # Feature score
        feature_score = min(1.0, len(common_features) / 5)

        # Variance score (lower variance = higher confidence)
        if "hierarchy_range" in common_features:
            lo, hi = common_features["hierarchy_range"]
            variance_score = 1.0 - (hi - lo) * 0.2
        else:
            variance_score = 0.5

        return (count_score * 0.4 + feature_score * 0.4 + variance_score * 0.2)

    def generalize_pattern(
        self,
        pattern: Dict[str, Any],
        similar_patterns: List[Dict[str, Any]],
    ) -> AbstractConcept:
        """
        Generalize from a pattern and similar patterns.

        Args:
            pattern: The base pattern
            similar_patterns: Similar patterns found

        Returns:
            Abstract concept representing the generalization
        """
        all_patterns = [pattern] + similar_patterns
        return self.form_concept(
            all_patterns,
            name=f"Generalized_{pattern.get('label', 'Pattern')}",
            abstraction_level=self.LEVEL_STRUCTURAL,
        )

    def find_abstractions(
        self,
        patterns: List[Dict[str, Any]],
        min_similarity: float = 0.5,
    ) -> List[AbstractConcept]:
        """
        Find potential abstractions in patterns.

        Args:
            patterns: List of patterns to analyze
            min_similarity: Minimum similarity to form abstraction

        Returns:
            List of abstract concepts
        """
        if len(patterns) < 2:
            return []

        abstractions = []

        # Group by domain
        by_domain: Dict[str, List[Dict]] = {}
        for p in patterns:
            domain = p.get("domain", "unknown")
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(p)

        # Form concepts for each domain group
        for domain, domain_patterns in by_domain.items():
            if len(domain_patterns) >= 2:
                # Check similarity
                similarity = self._calculate_group_similarity(domain_patterns)
                if similarity >= min_similarity:
                    concept = self.form_concept(
                        domain_patterns,
                        name=f"{domain.title()}Abstraction",
                    )
                    abstractions.append(concept)

        # Find cross-domain abstractions
        if len(by_domain) >= 2:
            cross_domain = self._find_cross_domain_abstractions(by_domain)
            abstractions.extend(cross_domain)

        return abstractions

    def _calculate_group_similarity(
        self,
        patterns: List[Dict[str, Any]],
    ) -> float:
        """Calculate average similarity within a group of patterns."""
        if len(patterns) < 2:
            return 0.0

        total_sim = 0.0
        count = 0

        for i, p1 in enumerate(patterns):
            for p2 in patterns[i + 1:]:
                sim = self._pattern_similarity(p1, p2)
                total_sim += sim
                count += 1

        return total_sim / count if count > 0 else 0.0

    def _pattern_similarity(
        self,
        p1: Dict[str, Any],
        p2: Dict[str, Any],
    ) -> float:
        """Calculate similarity between two patterns."""
        scores = []

        # Type match
        if p1.get("type") == p2.get("type"):
            scores.append(1.0)
        else:
            scores.append(0.0)

        # Hierarchy level
        h1, h2 = p1.get("hierarchy_level"), p2.get("hierarchy_level")
        if h1 is not None and h2 is not None:
            scores.append(1.0 - abs(h1 - h2) * 0.25)

        # Composition overlap
        comp1 = set(p1.get("composition", []))
        comp2 = set(p2.get("composition", []))
        if comp1 and comp2:
            overlap = len(comp1 & comp2)
            union = len(comp1 | comp2)
            scores.append(overlap / union if union > 0 else 0)

        return sum(scores) / len(scores) if scores else 0.0

    def _find_cross_domain_abstractions(
        self,
        by_domain: Dict[str, List[Dict]],
    ) -> List[AbstractConcept]:
        """Find abstractions that span domains."""
        abstractions = []
        domains = list(by_domain.keys())

        for i, d1 in enumerate(domains):
            for d2 in domains[i + 1:]:
                # Find similar patterns across domains
                cross_patterns = []
                for p1 in by_domain[d1]:
                    for p2 in by_domain[d2]:
                        if self._pattern_similarity(p1, p2) >= 0.6:
                            cross_patterns.extend([p1, p2])

                if len(cross_patterns) >= 2:
                    concept = self.form_concept(
                        cross_patterns,
                        name=f"CrossDomain_{d1}_{d2}",
                        description=f"Cross-domain abstraction between {d1} and {d2}",
                        abstraction_level=self.LEVEL_SEMANTIC,
                    )
                    abstractions.append(concept)

        return abstractions

    def refine_concept(
        self,
        concept_id: str,
        new_patterns: List[Dict[str, Any]],
        is_counter_example: bool = False,
    ) -> Optional[AbstractConcept]:
        """
        Refine an existing concept with new patterns.

        Args:
            concept_id: ID of concept to refine
            new_patterns: New patterns to incorporate
            is_counter_example: Whether these are counter-examples

        Returns:
            Updated concept or None
        """
        concept = self._concepts.get(concept_id)
        if not concept:
            return None

        if is_counter_example:
            # Add counter-examples
            for p in new_patterns:
                example = p.get("content", str(p))
                if example not in concept.counter_examples:
                    concept.counter_examples.append(example)
            
            # Reduce confidence
            concept.confidence *= 0.9
        else:
            # Add supporting patterns
            for p in new_patterns:
                pattern_id = p.get("id", str(len(concept.source_patterns)))
                if pattern_id not in concept.source_patterns:
                    concept.source_patterns.append(pattern_id)
                example = p.get("content", str(p))
                if example not in concept.examples:
                    concept.examples.append(example)

            # Recalculate confidence
            old_patterns = [{"id": pid} for pid in concept.source_patterns]
            all_patterns = old_patterns + new_patterns
            concept.attributes = self._extract_common_features(all_patterns)
            concept.confidence = self._calculate_confidence(all_patterns, concept.attributes)

        self._record_abstraction("refine_concept", concept_id, len(new_patterns))
        return concept

    def get_concept(self, concept_id: str) -> Optional[AbstractConcept]:
        """Get a concept by ID."""
        return self._concepts.get(concept_id)

    def get_concepts_by_pattern(self, pattern_id: str) -> List[AbstractConcept]:
        """Get all concepts that include a pattern."""
        concept_ids = self._pattern_index.get(pattern_id, set())
        return [self._concepts[cid] for cid in concept_ids if cid in self._concepts]

    def get_all_concepts(self) -> List[Dict[str, Any]]:
        """Get all concepts."""
        return [c.to_dict() for c in self._concepts.values()]

    def get_concepts_by_level(self, level: int) -> List[AbstractConcept]:
        """Get concepts at a specific abstraction level."""
        return [c for c in self._concepts.values() if c.abstraction_level == level]

    def _record_abstraction(
        self,
        action: str,
        concept_id: str,
        pattern_count: int,
    ) -> None:
        """Record abstraction action in history."""
        self._abstraction_history.append({
            "action": action,
            "concept_id": concept_id,
            "pattern_count": pattern_count,
            "timestamp": datetime.now().isoformat(),
        })

        if len(self._abstraction_history) > self._max_history:
            self._abstraction_history.pop(0)

    def get_abstraction_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get abstraction history."""
        return self._abstraction_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        levels = Counter(c.abstraction_level for c in self._concepts.values())
        avg_confidence = (
            sum(c.confidence for c in self._concepts.values()) / len(self._concepts)
            if self._concepts else 0
        )

        return {
            "total_concepts": len(self._concepts),
            "by_level": dict(levels),
            "average_confidence": avg_confidence,
            "total_patterns_indexed": len(self._pattern_index),
            "rules_count": len(self._rules),
        }

    def clear(self) -> None:
        """Clear all concepts and history."""
        self._concepts.clear()
        self._pattern_index.clear()
        self._abstraction_history.clear()


class ConceptHierarchy:
    """
    Manages hierarchical relationships between concepts.
    """

    def __init__(self):
        """Initialize the ConceptHierarchy."""
        self._parent_map: Dict[str, str] = {}  # child -> parent
        self._children_map: Dict[str, Set[str]] = {}  # parent -> children

    def add_relationship(
        self,
        parent_id: str,
        child_id: str,
    ) -> None:
        """
        Add a parent-child relationship.

        Args:
            parent_id: Parent concept ID
            child_id: Child concept ID
        """
        self._parent_map[child_id] = parent_id
        if parent_id not in self._children_map:
            self._children_map[parent_id] = set()
        self._children_map[parent_id].add(child_id)

    def get_parent(self, concept_id: str) -> Optional[str]:
        """Get parent of a concept."""
        return self._parent_map.get(concept_id)

    def get_children(self, concept_id: str) -> Set[str]:
        """Get children of a concept."""
        return self._children_map.get(concept_id, set())

    def get_ancestors(self, concept_id: str) -> List[str]:
        """Get all ancestors of a concept."""
        ancestors = []
        current = concept_id
        while current in self._parent_map:
            parent = self._parent_map[current]
            ancestors.append(parent)
            current = parent
        return ancestors

    def get_descendants(self, concept_id: str) -> List[str]:
        """Get all descendants of a concept."""
        descendants = []
        to_visit = list(self._children_map.get(concept_id, set()))
        while to_visit:
            child = to_visit.pop()
            descendants.append(child)
            to_visit.extend(self._children_map.get(child, set()))
        return descendants

    def get_siblings(self, concept_id: str) -> Set[str]:
        """Get siblings of a concept."""
        parent = self._parent_map.get(concept_id)
        if parent:
            siblings = self._children_map.get(parent, set()).copy()
            siblings.discard(concept_id)
            return siblings
        return set()

    def get_depth(self, concept_id: str) -> int:
        """Get depth of a concept in the hierarchy."""
        return len(self.get_ancestors(concept_id))

    def find_common_ancestor(
        self,
        concept_id1: str,
        concept_id2: str,
    ) -> Optional[str]:
        """Find common ancestor of two concepts."""
        ancestors1 = set(self.get_ancestors(concept_id1))
        ancestors2 = set(self.get_ancestors(concept_id2))
        common = ancestors1 & ancestors2
        if common:
            # Return the closest (first) common ancestor
            for ancestor in self.get_ancestors(concept_id1):
                if ancestor in common:
                    return ancestor
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert hierarchy to dictionary."""
        return {
            "parent_map": self._parent_map,
            "children_map": {k: list(v) for k, v in self._children_map.items()},
        }
