"""
Agent Interface - API for external agent integration.

Provides a unified interface for external agents to:
- Query patterns
- Teach new patterns
- Assess learning
- Answer inquiries
- Get system status
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging

from ..core.node import Node, NodeType
from ..core.edge import Edge, EdgeType
from ..memory.stm import ShortTermMemory
from ..memory.ltm import LongTermMemory
from ..memory.episodic import EpisodicMemory
from ..inquiry.question_generator import QuestionGenerator
from ..learning.answer_integrator import AnswerIntegrator
from ..learning.recursive_linker import RecursiveLinker
from ..validation.validator import Validator

logger = logging.getLogger(__name__)


@dataclass
class PatternQueryResult:
    """Result of a pattern query."""
    found: bool
    pattern: Optional[Dict[str, Any]] = None
    message: str = ""
    related_patterns: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "found": self.found,
            "pattern": self.pattern,
            "message": self.message,
            "related_patterns": self.related_patterns
        }


@dataclass
class TeachingResult:
    """Result of a teaching operation."""
    success: bool
    pattern_id: str = ""
    message: str = ""
    validation: Optional[Dict[str, Any]] = None
    consolidation_status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "pattern_id": self.pattern_id,
            "message": self.message,
            "validation": self.validation,
            "consolidation_status": self.consolidation_status
        }


@dataclass
class AssessmentResult:
    """Result of a pattern assessment."""
    pattern_id: str
    is_valid: bool
    pass_rate: float
    exercises: List[Dict[str, Any]] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "is_valid": self.is_valid,
            "pass_rate": self.pass_rate,
            "exercises": self.exercises,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations
        }


@dataclass
class MemoryStatus:
    """Status of the memory system."""
    stm_patterns: int
    ltm_patterns: int
    total_episodes: int
    domains: List[str]
    hierarchy_levels: Dict[int, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stm_patterns": self.stm_patterns,
            "ltm_patterns": self.ltm_patterns,
            "total_episodes": self.total_episodes,
            "domains": self.domains,
            "hierarchy_levels": self.hierarchy_levels
        }


class AgentInterface:
    """
    Unified interface for external agent integration.

    Provides methods for:
    - Pattern querying and teaching
    - Learning assessment
    - Inquiry handling
    - Status monitoring
    """

    def __init__(
        self,
        stm: Optional[ShortTermMemory] = None,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None
    ):
        """
        Initialize AgentInterface.

        Args:
            stm: Short-term memory instance
            ltm: Long-term memory instance
            episodic: Episodic memory instance
        """
        self.stm = stm or ShortTermMemory()
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()

        # Initialize helper components
        self.question_generator = QuestionGenerator()
        self.answer_integrator = AnswerIntegrator(self.episodic)
        self.recursive_linker = RecursiveLinker()
        self.validator = Validator()

        # Track inquiries
        self._pending_inquiries: Dict[str, Dict[str, Any]] = {}

    def query_pattern(
        self,
        label: str,
        domain: Optional[str] = None
    ) -> PatternQueryResult:
        """
        Query a pattern by label.

        Args:
            label: Pattern label to search for
            domain: Optional domain filter

        Returns:
            PatternQueryResult with pattern details
        """
        # Search in LTM
        for node_id, node in self.ltm._nodes.items():
            if node.label.lower() == label.lower():
                if domain and node.domain != domain:
                    continue

                # Get related patterns
                related = []
                edges = self.ltm.get_edges_from(node_id)
                for edge in edges:
                    related_node = self.ltm.get_node(edge.target_id)
                    if related_node:
                        related.append({
                            "id": related_node.node_id,
                            "label": related_node.label,
                            "relationship": edge.edge_type.value
                        })

                # Get composition from edges
                composition_edges = self.ltm.get_edges_from(node_id, EdgeType.COMPOSED_OF)
                composition = [e.target_id for e in composition_edges]
                
                return PatternQueryResult(
                    found=True,
                    pattern={
                        "id": node.node_id,
                        "label": node.label,
                        "type": node.node_type.value,
                        "domain": node.domain,
                        "hierarchy_level": node.hierarchy_level,
                        "composition": composition,
                        "is_uncertain": node.is_uncertain,
                        "confidence": node.confidence
                    },
                    message=f"Found pattern: {label}",
                    related_patterns=related
                )

        return PatternQueryResult(
            found=False,
            message=f"Pattern '{label}' not found"
        )

    def teach_pattern(
        self,
        content: str,
        domain: str,
        hierarchy_level: int = 1,
        composition: Optional[List[str]] = None
    ) -> TeachingResult:
        """
        Teach a new pattern to the system.

        Args:
            content: The pattern content/label
            domain: Domain (e.g., "english", "python")
            hierarchy_level: Hierarchy level (0=primitive, 1=pattern, 2+=higher)
            composition: List of component pattern IDs

        Returns:
            TeachingResult with status
        """
        # Create node ID
        node_type = "primitive" if hierarchy_level == 0 else "pattern"
        node_id = f"{node_type}:{content}"

        # Check if already exists
        if self.ltm.get_node(node_id):
            return TeachingResult(
                success=False,
                pattern_id=node_id,
                message=f"Pattern '{content}' already exists"
            )

        # Create the node
        node = Node(
            node_id=node_id,
            label=content,
            node_type=NodeType.PRIMITIVE if hierarchy_level == 0 else NodeType.PATTERN,
            content=content,
            domain=domain,
            hierarchy_level=hierarchy_level
        )

        # Validate before adding
        if composition:
            validation = self.validator.validate_pattern(node_id, self.ltm)
            if not validation.is_valid:
                return TeachingResult(
                    success=False,
                    pattern_id=node_id,
                    message="Validation failed",
                    validation={
                        "is_valid": validation.is_valid,
                        "issues": validation.issues
                    }
                )
        else:
            validation = None

        # Add to STM first, then consolidate to LTM
        self.stm.create_pattern(
            label=content,
            domain=domain,
            hierarchy_level=hierarchy_level,
            composition=composition or []
        )

        # Add directly to LTM for simplicity
        self.ltm.add_node(node)

        # Create composition edges
        if composition:
            for comp_id in composition:
                edge = Edge(
                    source_id=node_id,
                    target_id=comp_id,
                    edge_type=EdgeType.COMPOSITION
                )
                self.ltm.add_edge(edge)

        # Log to episodic memory
        self.episodic.log_event(
            event_type="pattern_taught",
            details={
                "pattern_id": node_id,
                "label": content,
                "domain": domain,
                "hierarchy_level": hierarchy_level
            }
        )

        return TeachingResult(
            success=True,
            pattern_id=node_id,
            message=f"Successfully taught pattern: {content}",
            validation={
                "is_valid": True,
                "issues": []
            } if validation is None else {
                "is_valid": validation.is_valid,
                "issues": validation.issues
            },
            consolidation_status="consolidated"
        )

    def assess_pattern(
        self,
        label: str,
        domain: Optional[str] = None
    ) -> AssessmentResult:
        """
        Assess a pattern's learning status.

        Args:
            label: Pattern label to assess
            domain: Optional domain filter

        Returns:
            AssessmentResult with details
        """
        # Find the pattern
        query_result = self.query_pattern(label, domain)
        if not query_result.found:
            return AssessmentResult(
                pattern_id="",
                is_valid=False,
                pass_rate=0.0,
                recommendations=[f"Pattern '{label}' not found"]
            )

        pattern = query_result.pattern
        node_id = pattern["id"]

        # Get integrity from recursive linker
        integrity = self.recursive_linker.verify_recursive_integrity(
            node_id, self.ltm
        )

        # Calculate pass rate based on integrity and validation
        if integrity.is_valid:
            pass_rate = 1.0
            strengths = ["All composition links valid"]
            weaknesses = []
        else:
            missing_count = len(integrity.missing_links)
            total_links = integrity.total_linked_nodes + missing_count
            pass_rate = integrity.total_linked_nodes / max(total_links, 1)

            strengths = []
            weaknesses = []

            if integrity.missing_links:
                weaknesses.append(f"Missing links: {integrity.missing_links[:3]}")

            if integrity.circular_references:
                weaknesses.append(f"Circular references detected")

            if integrity.total_linked_nodes > 0:
                strengths.append(f"{integrity.total_linked_nodes} valid links")

        # Generate recommendations
        recommendations = []
        if not integrity.is_valid:
            recommendations.append("Review missing composition elements")

            # Check for compounds
            compounds = self.recursive_linker.identify_compound_patterns(
                self.ltm, domain
            )
            if compounds:
                recommendations.append(
                    f"Consider creating {len(compounds)} compound patterns"
                )

        return AssessmentResult(
            pattern_id=node_id,
            is_valid=integrity.is_valid,
            pass_rate=pass_rate,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def get_inquiries(
        self,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending inquiries for learning.

        Args:
            domain: Optional domain filter

        Returns:
            List of inquiry dictionaries
        """
        # Generate inquiries based on gaps
        from ..inquiry.gap_detector import GapDetector

        gap_detector = GapDetector(self.ltm)
        gaps = gap_detector.detect_all_gaps()

        inquiries = []
        for gap in gaps[:10]:  # Limit to 10
            if domain and gap.domain != domain:
                continue

            inquiry = self.question_generator.generate_question(
                gap.node_id,
                gap.gap_type.value,
                {"missing_children": gap.metadata.get("missing_children", [])}
            )

            self._pending_inquiries[inquiry.inquiry_id] = {
                "inquiry": inquiry.to_dict(),
                "gap": gap.to_dict()
            }

            inquiries.append(inquiry.to_dict())

        return inquiries

    def answer_inquiry(
        self,
        inquiry_id: str,
        response: str
    ) -> Dict[str, Any]:
        """
        Answer a pending inquiry.

        Args:
            inquiry_id: ID of the inquiry
            response: Answer/response text

        Returns:
            Result of the answer integration
        """
        if inquiry_id not in self._pending_inquiries:
            return {
                "success": False,
                "message": f"Inquiry {inquiry_id} not found"
            }

        inquiry_data = self._pending_inquiries[inquiry_id]
        inquiry = inquiry_data["inquiry"]
        gap = inquiry_data["gap"]

        # Integrate the answer
        result = self.answer_integrator.integrate_answer(
            inquiry_id,
            response,
            gap["node_id"],
            gap["gap_type"]
        )

        # Remove from pending
        del self._pending_inquiries[inquiry_id]

        # Log to episodic memory
        self.episodic.log_event(
            event_type="inquiry_answered",
            details={
                "inquiry_id": inquiry_id,
                "response": response[:100],  # Truncate
                "result": result.to_dict() if hasattr(result, 'to_dict') else result
            }
        )

        return {
            "success": True,
            "message": "Answer integrated successfully",
            "result": result.to_dict() if hasattr(result, 'to_dict') else result
        }

    def get_curriculum_status(self) -> Dict[str, Any]:
        """
        Get status of curriculum learning.

        Returns:
            Curriculum status dictionary
        """
        stats = self.recursive_linker.get_hierarchy_stats(self.ltm)

        return {
            "total_patterns": stats["total_nodes"],
            "by_domain": stats["by_domain"],
            "by_level": stats["by_level"],
            "unlinked_patterns": stats["unlinked_nodes"],
            "pending_inquiries": len(self._pending_inquiries)
        }

    def get_memory_status(self) -> MemoryStatus:
        """
        Get memory system status.

        Returns:
            MemoryStatus object
        """
        # Count patterns
        stm_count = len(self.stm)  # STM uses __len__ via _graph
        ltm_count = len(self.ltm._nodes)

        # Get domains
        domains = set()
        hierarchy_levels: Dict[int, int] = {}

        for node in self.ltm._nodes.values():
            domains.add(node.domain)
            level = node.hierarchy_level
            hierarchy_levels[level] = hierarchy_levels.get(level, 0) + 1

        return MemoryStatus(
            stm_patterns=stm_count,
            ltm_patterns=ltm_count,
            total_episodes=len(self.episodic._events),
            domains=list(domains),
            hierarchy_levels=hierarchy_levels
        )

    def batch_teach(
        self,
        patterns: List[Dict[str, Any]]
    ) -> List[TeachingResult]:
        """
        Teach multiple patterns at once.

        Args:
            patterns: List of pattern dictionaries with:
                     - content: str
                     - domain: str
                     - hierarchy_level: int (optional)
                     - composition: List[str] (optional)

        Returns:
            List of TeachingResult objects
        """
        results = []

        for pattern in patterns:
            result = self.teach_pattern(
                content=pattern["content"],
                domain=pattern["domain"],
                hierarchy_level=pattern.get("hierarchy_level", 1),
                composition=pattern.get("composition")
            )
            results.append(result)

        return results

    def search_patterns(
        self,
        query: str,
        domain: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for patterns matching a query.

        Args:
            query: Search query
            domain: Optional domain filter
            limit: Maximum results to return

        Returns:
            List of matching patterns
        """
        matches = []
        query_lower = query.lower()

        for node_id, node in self.ltm._nodes.items():
            if domain and node.domain != domain:
                continue

            # Match on label
            if query_lower in node.label.lower():
                matches.append({
                    "id": node.node_id,
                    "label": node.label,
                    "domain": node.domain,
                    "hierarchy_level": node.hierarchy_level,
                    "match_type": "label"
                })

            # Match on composition
            elif any(query_lower in str(c).lower() for c in (node.composition or [])):
                matches.append({
                    "id": node.node_id,
                    "label": node.label,
                    "domain": node.domain,
                    "hierarchy_level": node.hierarchy_level,
                    "match_type": "composition"
                })

            if len(matches) >= limit:
                break

        return matches

    def export_knowledge(
        self,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export all knowledge as a dictionary.

        Args:
            domain: Optional domain filter

        Returns:
            Dictionary with all nodes and edges
        """
        nodes = []
        edges = []

        for node_id, node in self.ltm._nodes.items():
            if domain and node.domain != domain:
                continue
            
            # Get composition from edges
            comp_edges = self.ltm.get_edges_from(node_id, EdgeType.COMPOSED_OF)
            composition = [e.target_id for e in comp_edges]
            
            nodes.append({
                "id": node.node_id,
                "label": node.label,
                "type": node.node_type.value,
                "domain": node.domain,
                "hierarchy_level": node.hierarchy_level,
                "composition": composition,
                "confidence": node.confidence
            })

        for edge in self.ltm._edges:
            source = self.ltm.get_node(edge.source_id)
            if domain and source and source.domain != domain:
                continue

            edges.append({
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.edge_type.value,
                "weight": edge.weight
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }
