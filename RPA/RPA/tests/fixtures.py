"""
Test fixtures and sample data for RPA tests.
"""

import pytest
from typing import Dict, List

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType
from rpa.memory.stm import ShortTermMemory
from rpa.memory.ltm import LongTermMemory


# === Sample Primitives ===

PRIMITIVE_CHARS = "abcdefghijklmnopqrstuvwxyz"


def create_primitive_nodes(domain: str = "english") -> Dict[str, Node]:
    """Create sample primitive nodes for testing."""
    nodes = {}
    for char in PRIMITIVE_CHARS:
        node = Node.create_primitive(char, domain)
        nodes[node.node_id] = node
    return nodes


def create_sample_primitives() -> List[Node]:
    """Create a list of sample primitives."""
    return [Node.create_primitive(c) for c in "abcdef"]


# === Sample Words ===

SAMPLE_WORDS = [
    {"label": "cat", "content": "cat", "composition": ["c", "a", "t"]},
    {"label": "dog", "content": "dog", "composition": ["d", "o", "g"]},
    {"label": "apple", "content": "apple", "composition": ["a", "p", "p", "l", "e"]},
    {"label": "bat", "content": "bat", "composition": ["b", "a", "t"]},
    {"label": "cab", "content": "cab", "composition": ["c", "a", "b"]},
]


def create_word_nodes(domain: str = "english") -> Dict[str, Node]:
    """Create sample word nodes for testing."""
    nodes = {}
    for word_data in SAMPLE_WORDS:
        node = Node.create_pattern(
            label=word_data["label"],
            content=word_data["content"],
            hierarchy_level=1,
            domain=domain,
        )
        nodes[node.node_id] = node
    return nodes


# === Sample Sentences ===

SAMPLE_SENTENCES = [
    {
        "label": "the_cat_sat",
        "content": "The cat sat.",
        "composition": ["the", "cat", "sat"],
    },
    {
        "label": "the_dog_ran",
        "content": "The dog ran.",
        "composition": ["the", "dog", "ran"],
    },
]


def create_sentence_nodes(domain: str = "english") -> Dict[str, Node]:
    """Create sample sentence nodes for testing."""
    nodes = {}
    for sent_data in SAMPLE_SENTENCES:
        node = Node.create_sequence(
            label=sent_data["label"],
            content=sent_data["content"],
            hierarchy_level=2,
            domain=domain,
        )
        nodes[node.node_id] = node
    return nodes


# === Sample Code Patterns ===

SAMPLE_CODE_PATTERNS = [
    {
        "label": "assignment_x",
        "content": "x = 5",
        "composition": ["x", "=", "5"],
        "pattern_type": "assignment",
    },
    {
        "label": "for_loop",
        "content": "for i in range(5):",
        "composition": ["for", "i", "in", "range", "(", "5", ")", ":"],
        "pattern_type": "loop",
    },
]


def create_code_nodes(domain: str = "python") -> Dict[str, Node]:
    """Create sample code pattern nodes for testing."""
    nodes = {}
    for code_data in SAMPLE_CODE_PATTERNS:
        node = Node.create_pattern(
            label=code_data["label"],
            content=code_data["content"],
            hierarchy_level=1,
            domain=domain,
        )
        node.metadata["pattern_type"] = code_data.get("pattern_type", "")
        nodes[node.node_id] = node
    return nodes


# === Graph Fixtures ===

@pytest.fixture
def empty_graph() -> PatternGraph:
    """Create an empty pattern graph."""
    return PatternGraph()


@pytest.fixture
def primitive_graph() -> PatternGraph:
    """Create a graph with primitive nodes."""
    graph = PatternGraph()
    primitives = create_primitive_nodes()
    for node in primitives.values():
        graph.add_node(node)
    return graph


@pytest.fixture
def word_graph() -> PatternGraph:
    """Create a graph with primitives and word patterns."""
    graph = PatternGraph()
    
    # Add primitives
    primitives = create_primitive_nodes()
    for node in primitives.values():
        graph.add_node(node)
    
    # Add word patterns
    for word_data in SAMPLE_WORDS:
        word_node = Node.create_pattern(
            label=word_data["label"],
            content=word_data["content"],
            hierarchy_level=1,
        )
        graph.add_node(word_node)
        
        # Add composition edges
        for i, char in enumerate(word_data["composition"]):
            child_id = f"primitive:{char}"
            if graph.has_node(child_id):
                edge = Edge.create_composition(
                    parent_id=word_node.node_id,
                    child_id=child_id,
                    order=i,
                )
                graph.add_edge(edge)
    
    return graph


@pytest.fixture
def full_english_graph() -> PatternGraph:
    """Create a complete graph with primitives, words, and sentences."""
    graph = PatternGraph()
    
    # Add primitives
    primitives = create_primitive_nodes()
    for node in primitives.values():
        graph.add_node(node)
    
    # Add word patterns
    word_nodes = {}
    for word_data in SAMPLE_WORDS:
        word_node = Node.create_pattern(
            label=word_data["label"],
            content=word_data["content"],
            hierarchy_level=1,
        )
        graph.add_node(word_node)
        word_nodes[word_data["label"]] = word_node
        
        # Add composition edges
        for i, char in enumerate(word_data["composition"]):
            child_id = f"primitive:{char}"
            if graph.has_node(child_id):
                edge = Edge.create_composition(
                    parent_id=word_node.node_id,
                    child_id=child_id,
                    order=i,
                )
                graph.add_edge(edge)
    
    # Add sentences
    for sent_data in SAMPLE_SENTENCES:
        sent_node = Node.create_sequence(
            label=sent_data["label"],
            content=sent_data["content"],
            hierarchy_level=2,
        )
        graph.add_node(sent_node)
        
        # Add composition edges (to word patterns)
        for i, word in enumerate(sent_data["composition"]):
            if word in word_nodes:
                edge = Edge.create_composition(
                    parent_id=sent_node.node_id,
                    child_id=word_nodes[word].node_id,
                    order=i,
                )
                graph.add_edge(edge)
    
    return graph


# === Memory Fixtures ===

@pytest.fixture
def empty_stm() -> ShortTermMemory:
    """Create an empty STM."""
    return ShortTermMemory()


@pytest.fixture
def stm_with_session(empty_stm: ShortTermMemory) -> ShortTermMemory:
    """Create an STM with an active session."""
    empty_stm.create_session("test_session")
    return empty_stm


@pytest.fixture
def stm_with_patterns(stm_with_session: ShortTermMemory) -> ShortTermMemory:
    """Create an STM with some patterns."""
    primitives = create_sample_primitives()
    for prim in primitives:
        stm_with_session.add_pattern(prim, "test_session")
    return stm_with_session


@pytest.fixture
def empty_ltm() -> LongTermMemory:
    """Create an empty LTM."""
    return LongTermMemory()


# === Helper Functions ===

def create_test_node(
    label: str = "test",
    content: str = "test",
    node_type: NodeType = NodeType.PATTERN,
    hierarchy_level: int = 1,
    domain: str = "english",
) -> Node:
    """Create a test node with default values."""
    return Node(
        node_id=f"{node_type.value}:{label}",
        label=label,
        node_type=node_type,
        content=content,
        hierarchy_level=hierarchy_level,
        domain=domain,
    )


def create_test_graph_with_patterns(num_patterns: int = 5) -> PatternGraph:
    """Create a test graph with a specified number of patterns."""
    graph = PatternGraph()
    
    # Add primitives
    for c in "abcdefg":
        graph.add_node(Node.create_primitive(c))
    
    # Add patterns
    for i in range(num_patterns):
        node = Node.create_pattern(
            label=f"pattern_{i}",
            content=f"pattern_{i}",
            hierarchy_level=1,
        )
        graph.add_node(node)
        
        # Add composition edges
        for j, c in enumerate(f"pattern_{i}"):
            if graph.has_node(f"primitive:{c}"):
                edge = Edge.create_composition(
                    parent_id=node.node_id,
                    child_id=f"primitive:{c}",
                    order=j,
                )
                graph.add_edge(edge)
    
    return graph
