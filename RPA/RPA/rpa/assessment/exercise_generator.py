"""
Exercise generation for RPA assessment.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import random
import uuid

from rpa.core.graph import Node, PatternGraph, NodeType


class ExerciseType(Enum):
    """Types of assessment exercises."""
    RECONSTRUCT = "reconstruct"           # Generate output from pattern
    RECOGNIZE = "recognize"               # Identify pattern from output
    COMPOSE = "compose"                   # Compose pattern from components
    DECOMPOSE = "decompose"               # Decompose pattern into components
    RECURSIVE_RECALL = "recursive_recall" # Traverse and verify children
    CONTEXTUAL_USAGE = "contextual_usage" # Use pattern in context
    ERROR_DETECTION = "error_detection"   # Identify errors in pattern
    ANALOGY = "analogy"                   # Find similar patterns
    TRANSFORMATION = "transformation"     # Transform pattern


@dataclass
class Exercise:
    """Represents an assessment exercise."""
    exercise_id: str
    exercise_type: ExerciseType
    pattern_id: str
    prompt: str
    expected_answer: str
    options: List[str] = field(default_factory=list)  # For multiple choice
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "exercise_id": self.exercise_id,
            "exercise_type": self.exercise_type.value,
            "pattern_id": self.pattern_id,
            "prompt": self.prompt,
            "expected_answer": self.expected_answer,
            "options": self.options,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Exercise":
        """Create from dictionary."""
        return cls(
            exercise_id=data["exercise_id"],
            exercise_type=ExerciseType(data["exercise_type"]),
            pattern_id=data["pattern_id"],
            prompt=data["prompt"],
            expected_answer=data["expected_answer"],
            options=data.get("options", []),
            metadata=data.get("metadata", {}),
        )


class ExerciseGenerator:
    """
    Generates assessment exercises for patterns.
    
    The ExerciseGenerator creates various types of exercises to test
    pattern understanding, composition, and application.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the ExerciseGenerator.
        
        Args:
            seed: Optional random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def generate_exercises(
        self,
        node: Node,
        graph: PatternGraph,
        exercise_types: Optional[List[ExerciseType]] = None,
        count: int = 5,
    ) -> List[Exercise]:
        """
        Generate exercises for a pattern.
        
        Args:
            node: The pattern node to assess
            graph: The pattern graph
            exercise_types: Specific exercise types to generate
            count: Number of exercises to generate
            
        Returns:
            List of generated exercises
        """
        if exercise_types is None:
            # Default exercise types based on node type
            if node.node_type == NodeType.PRIMITIVE:
                exercise_types = [ExerciseType.RECOGNIZE, ExerciseType.RECONSTRUCT]
            else:
                exercise_types = [
                    ExerciseType.RECONSTRUCT,
                    ExerciseType.RECOGNIZE,
                    ExerciseType.COMPOSE,
                    ExerciseType.DECOMPOSE,
                    ExerciseType.RECURSIVE_RECALL,
                ]
        
        exercises = []
        
        # Generate exercises for each type
        for exercise_type in exercise_types:
            exercise = self._generate_exercise(node, graph, exercise_type)
            if exercise:
                exercises.append(exercise)
        
        # Ensure we have at least count exercises
        while len(exercises) < count:
            # Pick a random type and generate
            exercise_type = random.choice(exercise_types)
            exercise = self._generate_exercise(node, graph, exercise_type)
            if exercise:
                exercises.append(exercise)
        
        return exercises[:count]
    
    def _generate_exercise(
        self,
        node: Node,
        graph: PatternGraph,
        exercise_type: ExerciseType,
    ) -> Optional[Exercise]:
        """Generate a single exercise of the specified type."""
        
        generators = {
            ExerciseType.RECONSTRUCT: self._generate_reconstruct,
            ExerciseType.RECOGNIZE: self._generate_recognize,
            ExerciseType.COMPOSE: self._generate_compose,
            ExerciseType.DECOMPOSE: self._generate_decompose,
            ExerciseType.RECURSIVE_RECALL: self._generate_recursive_recall,
            ExerciseType.CONTEXTUAL_USAGE: self._generate_contextual_usage,
            ExerciseType.ERROR_DETECTION: self._generate_error_detection,
            ExerciseType.ANALOGY: self._generate_analogy,
            ExerciseType.TRANSFORMATION: self._generate_transformation,
        }
        
        generator = generators.get(exercise_type)
        if generator:
            return generator(node, graph)
        return None
    
    def _generate_reconstruct(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Exercise:
        """Generate a reconstruction exercise."""
        children = graph.get_children(node.node_id)
        
        if children:
            # Show components, ask for the whole
            component_str = ", ".join(c.content for c in children)
            prompt = f"Construct the pattern from these components: [{component_str}]"
            expected = node.content
        else:
            # For primitives, just show the label
            prompt = f"Output the character for: '{node.label}'"
            expected = node.content
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.RECONSTRUCT,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=expected,
            metadata={"hierarchy_level": node.hierarchy_level},
        )
    
    def _generate_recognize(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Exercise:
        """Generate a recognition exercise."""
        # Show content, ask for pattern identification
        prompt = f"Identify the pattern: '{node.content}'"
        
        # Create options (correct answer + distractors)
        options = [node.label]
        
        # Get similar patterns as distractors
        similar = self._find_similar_patterns(node, graph)
        for similar_node in similar[:3]:
            options.append(similar_node.label)
        
        # Add random distractors if needed
        while len(options) < 4:
            options.append(f"option_{len(options)}")
        
        random.shuffle(options)
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.RECOGNIZE,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=node.label,
            options=options[:4],
            metadata={"type": "multiple_choice"},
        )
    
    def _generate_compose(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Optional[Exercise]:
        """Generate a composition exercise."""
        children = graph.get_children(node.node_id)
        
        if not children or len(children) < 2:
            return None
        
        # Show components, ask for composition
        component_str = ", ".join(c.label for c in children)
        prompt = f"What pattern can be formed by composing: {component_str}?"
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.COMPOSE,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=node.label,
            metadata={"components": [c.node_id for c in children]},
        )
    
    def _generate_decompose(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Optional[Exercise]:
        """Generate a decomposition exercise."""
        children = graph.get_children(node.node_id)
        
        if not children:
            return None
        
        # Show pattern, ask for components
        prompt = f"Decompose the pattern '{node.label}' into its components."
        expected = ", ".join(c.label for c in children)
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.DECOMPOSE,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=expected,
            metadata={"component_count": len(children)},
        )
    
    def _generate_recursive_recall(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Exercise:
        """Generate a recursive recall exercise."""
        children = graph.get_children(node.node_id)
        all_descendants = self._get_all_descendants(node.node_id, graph)
        
        if children:
            prompt = (
                f"List all descendant patterns of '{node.label}' "
                f"(patterns it is composed of, recursively)."
            )
            expected = ", ".join(n.label for n in all_descendants)
        else:
            prompt = f"'{node.label}' is a primitive. What is its hierarchy level?"
            expected = "0"
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.RECURSIVE_RECALL,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=expected,
            metadata={
                "descendant_count": len(all_descendants),
                "hierarchy_level": node.hierarchy_level,
            },
        )
    
    def _generate_contextual_usage(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Optional[Exercise]:
        """Generate a contextual usage exercise."""
        # This would ideally use a language model
        # For now, create a simple template
        
        if node.node_type == NodeType.PRIMITIVE:
            return None
        
        if node.domain == "english":
            prompt = f"Use '{node.content}' in a sentence."
            expected = f"A sentence containing '{node.content}'"
        elif node.domain in ["python", "javascript", "code"]:
            prompt = f"Write a code snippet using: {node.content}"
            expected = f"Code containing {node.content}"
        else:
            prompt = f"Provide an example usage of: {node.content}"
            expected = f"An example using {node.content}"
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.CONTEXTUAL_USAGE,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=expected,
            metadata={"domain": node.domain, "open_ended": True},
        )
    
    def _generate_error_detection(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Optional[Exercise]:
        """Generate an error detection exercise."""
        children = graph.get_children(node.node_id)
        
        if not children:
            return None
        
        # Create a version with an error
        if len(children) >= 2:
            # Swap two children
            error_children = children.copy()
            random.shuffle(error_children)
            error_content = "".join(c.content for c in error_children)
            
            prompt = (
                f"Identify the error in this pattern: '{error_content}' "
                f"(correct: '{node.content}')"
            )
            expected = f"Order is incorrect. Correct order: {node.content}"
        else:
            # Remove a child
            error_content = ""
            prompt = (
                f"What is missing from this pattern: '{error_content or '(empty)'}' "
                f"(should be '{node.content}')"
            )
            expected = f"Missing: {children[0].content}"
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.ERROR_DETECTION,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=expected,
            metadata={"error_type": "composition_error"},
        )
    
    def _generate_analogy(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Optional[Exercise]:
        """Generate an analogy exercise."""
        similar = self._find_similar_patterns(node, graph)
        
        if not similar:
            return None
        
        # Find patterns with similar structure
        prompt = f"'{node.label}' is to '{node.content}' as '{similar[0].label}' is to ___?"
        expected = similar[0].content
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.ANALOGY,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=expected,
            metadata={"analogous_pattern": similar[0].node_id},
        )
    
    def _generate_transformation(
        self,
        node: Node,
        graph: PatternGraph,
    ) -> Optional[Exercise]:
        """Generate a transformation exercise."""
        if node.node_type == NodeType.PRIMITIVE:
            return None
        
        # Different transformations based on domain
        if node.domain == "english":
            if node.content.islower():
                prompt = f"Convert '{node.content}' to uppercase."
                expected = node.content.upper()
            elif node.content.isupper():
                prompt = f"Convert '{node.content}' to lowercase."
                expected = node.content.lower()
            else:
                prompt = f"Capitalize the first letter of '{node.content}'."
                expected = node.content.capitalize()
        else:
            # For code, ask for a simple transformation
            prompt = f"Reverse the pattern: '{node.content}'"
            expected = node.content[::-1]
        
        return Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            exercise_type=ExerciseType.TRANSFORMATION,
            pattern_id=node.node_id,
            prompt=prompt,
            expected_answer=expected,
            metadata={"transformation_type": "case" if node.domain == "english" else "reverse"},
        )
    
    def _find_similar_patterns(
        self,
        node: Node,
        graph: PatternGraph,
        limit: int = 5,
    ) -> List[Node]:
        """Find patterns similar to the given node."""
        similar = []
        
        # Find patterns with same hierarchy level and domain
        for other in graph.nodes.values():
            if other.node_id == node.node_id:
                continue
            if other.hierarchy_level == node.hierarchy_level:
                if other.domain == node.domain:
                    similar.append(other)
        
        # Sort by content similarity (simple length comparison for now)
        similar.sort(key=lambda n: abs(len(n.content) - len(node.content)))
        
        return similar[:limit]
    
    def _get_all_descendants(
        self,
        node_id: str,
        graph: PatternGraph,
        visited: Optional[set] = None,
    ) -> List[Node]:
        """Get all descendants of a node recursively."""
        if visited is None:
            visited = set()
        
        if node_id in visited:
            return []
        
        visited.add(node_id)
        descendants = []
        
        children = graph.get_children(node_id)
        for child in children:
            descendants.append(child)
            descendants.extend(self._get_all_descendants(child.node_id, graph, visited))
        
        return descendants
