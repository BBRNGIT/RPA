"""
Tests for RPA Core module (Node, Edge, PatternGraph).
"""

import pytest
from datetime import datetime

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType
from tests.fixtures import (
    empty_graph, primitive_graph, word_graph, full_english_graph,
    create_test_node, create_test_graph_with_patterns
)


class TestNode:
    """Tests for the Node class."""
    
    def test_create_primitive(self):
        """Test creating a primitive node."""
        node = Node.create_primitive("a")
        
        assert node.node_id == "primitive:a"
        assert node.label == "a"
        assert node.content == "a"
        assert node.node_type == NodeType.PRIMITIVE
        assert node.hierarchy_level == 0
    
    def test_create_primitive_invalid(self):
        """Test that primitives must be single characters."""
        with pytest.raises(ValueError):
            Node.create_primitive("ab")
        with pytest.raises(ValueError):
            Node.create_primitive("")
    
    def test_create_pattern(self):
        """Test creating a pattern node."""
        node = Node.create_pattern(
            label="test",
            content="test content",
            hierarchy_level=1,
            domain="english",
        )
        
        assert node.node_id == "pattern:test"
        assert node.label == "test"
        assert node.content == "test content"
        assert node.node_type == NodeType.PATTERN
        assert node.hierarchy_level == 1
        assert node.domain == "english"
    
    def test_create_sequence(self):
        """Test creating a sequence node."""
        node = Node.create_sequence(
            label="test_sentence",
            content="This is a test.",
            hierarchy_level=2,
        )
        
        assert node.node_id == "sequence:test_sentence"
        assert node.node_type == NodeType.SEQUENCE
        assert node.hierarchy_level == 2
    
    def test_node_touch(self):
        """Test the touch method updates timestamps."""
        node = create_test_node()
        old_time = node.updated_at
        
        node.touch()
        
        assert node.updated_at >= old_time
        assert node.access_count == 1
    
    def test_node_mark_uncertain(self):
        """Test marking a node as uncertain."""
        node = create_test_node()
        
        node.mark_uncertain("test reason")
        
        assert node.is_uncertain is True
        assert node.metadata.get("uncertainty_reason") == "test reason"
    
    def test_node_serialization(self):
        """Test node to_dict and from_dict."""
        node = create_test_node()
        
        data = node.to_dict()
        restored = Node.from_dict(data)
        
        assert restored.node_id == node.node_id
        assert restored.label == node.label
        assert restored.content == node.content
        assert restored.node_type == node.node_type
    
    def test_node_confidence_validation(self):
        """Test that confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            Node(
                node_id="test:node",
                label="test",
                node_type=NodeType.PATTERN,
                content="test",
                confidence=1.5,
            )
        
        with pytest.raises(ValueError):
            Node(
                node_id="test:node",
                label="test",
                node_type=NodeType.PATTERN,
                content="test",
                confidence=-0.5,
            )


class TestEdge:
    """Tests for the Edge class."""
    
    def test_create_composition_edge(self):
        """Test creating a composition edge."""
        edge = Edge.create_composition(
            parent_id="pattern:cat",
            child_id="primitive:c",
            order=0,
        )
        
        assert edge.source_id == "pattern:cat"
        assert edge.target_id == "primitive:c"
        assert edge.edge_type == EdgeType.COMPOSED_OF
        assert edge.order == 0
    
    def test_create_sequence_edge(self):
        """Test creating a sequence edge."""
        edge = Edge.create_sequence(
            from_id="word:the",
            to_id="word:cat",
            order=0,
        )
        
        assert edge.source_id == "word:the"
        assert edge.target_id == "word:cat"
        assert edge.edge_type == EdgeType.PRECEDES
    
    def test_create_instance_edge(self):
        """Test creating an instance edge."""
        edge = Edge.create_instance(
            specific_id="pattern:cat",
            general_id="concept:animal",
        )
        
        assert edge.source_id == "pattern:cat"
        assert edge.target_id == "concept:animal"
        assert edge.edge_type == EdgeType.IS_INSTANCE_OF
    
    def test_create_correction_edge(self):
        """Test creating a correction edge."""
        edge = Edge.create_correction(
            wrong_id="pattern:ct",
            correct_id="pattern:cat",
        )
        
        assert edge.source_id == "pattern:cat"
        assert edge.target_id == "pattern:ct"
        assert edge.edge_type == EdgeType.CORRECTS
    
    def test_edge_serialization(self):
        """Test edge to_dict and from_dict."""
        edge = Edge.create_composition("parent", "child", 0)
        
        data = edge.to_dict()
        restored = Edge.from_dict(data)
        
        assert restored.edge_id == edge.edge_id
        assert restored.source_id == edge.source_id
        assert restored.target_id == edge.target_id
        assert restored.edge_type == edge.edge_type


class TestPatternGraph:
    """Tests for the PatternGraph class."""
    
    def test_empty_graph(self, empty_graph: PatternGraph):
        """Test empty graph initialization."""
        assert len(empty_graph) == 0
        assert empty_graph.get_node_count() == 0
        assert empty_graph.get_edge_count() == 0
    
    def test_add_node(self, empty_graph: PatternGraph):
        """Test adding nodes to the graph."""
        node = create_test_node("test1")
        
        result = empty_graph.add_node(node)
        
        assert result is True
        assert len(empty_graph) == 1
        assert empty_graph.has_node(node.node_id)
    
    def test_add_duplicate_node(self, primitive_graph: PatternGraph):
        """Test that duplicate nodes are rejected."""
        node = Node.create_primitive("a")
        
        result = primitive_graph.add_node(node)
        
        assert result is False
    
    def test_get_node(self, primitive_graph: PatternGraph):
        """Test retrieving nodes."""
        node = primitive_graph.get_node("primitive:a")
        
        assert node is not None
        assert node.content == "a"
    
    def test_get_nonexistent_node(self, empty_graph: PatternGraph):
        """Test retrieving a non-existent node."""
        node = empty_graph.get_node("nonexistent")
        
        assert node is None
    
    def test_delete_node(self, primitive_graph: PatternGraph):
        """Test deleting a node."""
        result = primitive_graph.delete_node("primitive:a")
        
        assert result is True
        assert not primitive_graph.has_node("primitive:a")
    
    def test_delete_nonexistent_node(self, empty_graph: PatternGraph):
        """Test deleting a non-existent node."""
        result = empty_graph.delete_node("nonexistent")
        
        assert result is False
    
    def test_add_edge(self, word_graph: PatternGraph):
        """Test adding an edge."""
        # word_graph already has edges from word composition
        edge_count = word_graph.get_edge_count()
        
        assert edge_count > 0
    
    def test_get_children(self, word_graph: PatternGraph):
        """Test getting children of a node."""
        children = word_graph.get_children("pattern:cat")
        
        assert len(children) == 3
        contents = [c.content for c in children]
        assert "c" in contents
        assert "a" in contents
        assert "t" in contents
    
    def test_get_parents(self, word_graph: PatternGraph):
        """Test getting parents of a node."""
        parents = word_graph.get_parents("primitive:a")
        
        # 'a' should be a child of multiple words
        assert len(parents) >= 1
    
    def test_detect_circular_dependencies(self, word_graph: PatternGraph):
        """Test circular dependency detection."""
        # word_graph shouldn't have cycles
        cycles = word_graph.detect_circular_dependencies("pattern:cat")
        
        assert len(cycles) == 0
    
    def test_detect_circular_dependencies_with_cycle(self):
        """Test detecting actual cycles."""
        graph = PatternGraph()
        
        # Create nodes
        a = Node.create_pattern("a", "a", 1)
        b = Node.create_pattern("b", "b", 1)
        c = Node.create_pattern("c", "c", 1)
        
        graph.add_node(a)
        graph.add_node(b)
        graph.add_node(c)
        
        # Create a cycle: a -> b -> c -> a
        graph.add_edge(Edge.create_composition("pattern:a", "pattern:b", 0))
        graph.add_edge(Edge.create_composition("pattern:b", "pattern:c", 0))
        graph.add_edge(Edge.create_composition("pattern:c", "pattern:a", 0))
        
        cycles = graph.detect_circular_dependencies("pattern:a")
        
        assert len(cycles) > 0
    
    def test_traverse_bfs(self, word_graph: PatternGraph):
        """Test breadth-first traversal."""
        nodes = word_graph.traverse_bfs("pattern:cat", max_depth=3)
        
        assert len(nodes) > 0
        # First node should be the start node
        assert nodes[0].node_id == "pattern:cat"
    
    def test_get_nodes_by_type(self, primitive_graph: PatternGraph):
        """Test getting nodes by type."""
        primitives = primitive_graph.get_all_nodes_by_type(NodeType.PRIMITIVE)
        
        assert len(primitives) == 26  # a-z
    
    def test_get_nodes_by_level(self, word_graph: PatternGraph):
        """Test getting nodes by hierarchy level."""
        level_0 = word_graph.get_nodes_by_level(0)
        level_1 = word_graph.get_nodes_by_level(1)
        
        assert len(level_0) == 26  # primitives
        assert len(level_1) == 5   # words
    
    def test_graph_serialization(self, word_graph: PatternGraph):
        """Test graph to_dict and from_dict."""
        data = word_graph.to_dict()
        restored = PatternGraph.from_dict(data)
        
        assert len(restored) == len(word_graph)
        assert restored.get_edge_count() == word_graph.get_edge_count()
    
    def test_find_unresolved_references(self, word_graph: PatternGraph):
        """Test finding unresolved references."""
        # word_graph should have no unresolved references
        unresolved = word_graph.find_unresolved_references()
        
        assert len(unresolved) == 0
        
        # Add an edge to a non-existent node
        fake_edge = Edge(
            edge_id="fake_edge",
            source_id="pattern:cat",
            target_id="primitive:xyz",
            edge_type=EdgeType.COMPOSED_OF,
        )
        # This should raise an error since target doesn't exist
        # But if we somehow added it, find_unresolved_references would catch it


class TestPatternGraphHierarchy:
    """Tests for hierarchy-related graph operations."""
    
    def test_hierarchy_level_calculation(self, full_english_graph: PatternGraph):
        """Test calculating hierarchy levels."""
        # Primitives should be level 0
        prim = full_english_graph.get_node("primitive:a")
        level = full_english_graph.calculate_hierarchy_level("primitive:a")
        assert level == 0
        
        # Words should be level 1
        word = full_english_graph.get_node("pattern:cat")
        level = full_english_graph.calculate_hierarchy_level("pattern:cat")
        assert level == 1
        
        # Sentences should be level 2
        sent = full_english_graph.get_node("sequence:the_cat_sat")
        level = full_english_graph.calculate_hierarchy_level("sequence:the_cat_sat")
        assert level == 2
