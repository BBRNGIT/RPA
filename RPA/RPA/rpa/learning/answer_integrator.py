"""
Answer Integration for RPA system.

Processes inquiry responses and integrates them into the knowledge graph.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import re

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType
from rpa.memory.stm import ShortTermMemory
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.inquiry.question_generator import Inquiry, QuestionType
from rpa.inquiry.gap_detector import GapType


@dataclass
class IntegrationResult:
    """Result of integrating an answer."""
    inquiry_id: str
    success: bool = False
    new_nodes: List[str] = field(default_factory=list)
    new_edges: List[str] = field(default_factory=list)
    updated_nodes: List[str] = field(default_factory=list)
    message: str = ""
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "inquiry_id": self.inquiry_id,
            "success": self.success,
            "new_nodes": self.new_nodes,
            "new_edges": self.new_edges,
            "updated_nodes": self.updated_nodes,
            "message": self.message,
            "issues": self.issues,
        }


class AnswerIntegrator:
    """
    Processes inquiry responses and integrates them into memory.
    
    The AnswerIntegrator takes user/agent responses to inquiries and
    updates the knowledge graph accordingly, creating new nodes,
    edges, or updating existing patterns.
    """
    
    def __init__(
        self,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """
        Initialize the AnswerIntegrator.
        
        Args:
            episodic: Optional episodic memory for logging
        """
        self.episodic = episodic or EpisodicMemory()
        self._integration_history: Dict[str, IntegrationResult] = {}
    
    def integrate_answer(
        self,
        inquiry: Inquiry,
        response: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> IntegrationResult:
        """
        Integrate an answer to an inquiry.
        
        Args:
            inquiry: The inquiry being answered
            response: The answer/response provided
            stm: Short-Term Memory
            ltm: Long-Term Memory
            
        Returns:
            IntegrationResult with details of changes made
        """
        # Route to appropriate handler based on question type
        handlers = {
            QuestionType.COMPOSITION: self.integrate_composition_answer,
            QuestionType.USAGE: self.integrate_usage_answer,
            QuestionType.HIERARCHY: self.integrate_hierarchy_answer,
            QuestionType.CROSS_DOMAIN: self.integrate_cross_domain_answer,
            QuestionType.VALIDATION: self.integrate_validation_answer,
            QuestionType.CLARIFICATION: self.integrate_clarification_answer,
        }
        
        handler = handlers.get(inquiry.question_type)
        if handler:
            result = handler(inquiry, response, stm, ltm)
        else:
            result = IntegrationResult(
                inquiry_id=inquiry.inquiry_id,
                success=False,
                message=f"No handler for question type: {inquiry.question_type.value}",
            )
        
        # Log to episodic memory
        self.episodic.log_event(
            event_type=EventType.INQUIRY_ANSWERED,
            pattern_id=inquiry.affected_nodes[0] if inquiry.affected_nodes else None,
            data={
                "inquiry_id": inquiry.inquiry_id,
                "response": response,
                "success": result.success,
            },
        )
        
        # Store result
        self._integration_history[inquiry.inquiry_id] = result
        
        return result
    
    def integrate_composition_answer(
        self,
        inquiry: Inquiry,
        response: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> IntegrationResult:
        """
        Integrate a response about pattern composition.
        
        Handles responses about missing components or how a pattern is composed.
        """
        result = IntegrationResult(inquiry_id=inquiry.inquiry_id)
        
        node_id = inquiry.affected_nodes[0] if inquiry.affected_nodes else None
        if not node_id:
            result.issues.append("No affected node specified")
            return result
        
        # Check which memory contains the node
        graph = ltm if ltm.has_pattern(node_id) else stm._graph
        node = graph.get_node(node_id)
        
        if not node:
            result.issues.append(f"Node {node_id} not found")
            return result
        
        # Extract potential component names from response
        components = self._extract_components(response, inquiry.metadata.get("missing_children", []))
        
        # Create missing primitives/patterns
        for comp in components:
            comp_id = f"primitive:{comp}" if len(comp) == 1 else f"pattern:{comp}"
            
            if not graph.has_node(comp_id):
                # Create the missing node
                if len(comp) == 1:
                    new_node = Node.create_primitive(comp, node.domain)
                else:
                    new_node = Node.create_pattern(comp, comp, domain=node.domain)
                
                # Add to appropriate memory
                if graph == ltm:
                    ltm.consolidate(new_node)
                else:
                    stm.add_pattern(new_node)
                
                result.new_nodes.append(comp_id)
        
        # Add edges for new components
        existing_children = graph.get_children(node_id)
        existing_ids = {c.node_id for c in existing_children}
        order_offset = len(existing_children)
        
        for i, comp in enumerate(components):
            comp_id = f"primitive:{comp}" if len(comp) == 1 else f"pattern:{comp}"
            
            if comp_id not in existing_ids:
                edge = Edge.create_composition(
                    parent_id=node_id,
                    child_id=comp_id,
                    order=order_offset + i,
                )
                graph.add_edge(edge)
                result.new_edges.append(edge.edge_id)
        
        result.success = True
        result.message = f"Added {len(result.new_nodes)} nodes and {len(result.new_edges)} edges"
        
        return result
    
    def integrate_usage_answer(
        self,
        inquiry: Inquiry,
        response: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> IntegrationResult:
        """
        Integrate a response about pattern usage.
        
        Handles responses about how a pattern is used in higher-level contexts.
        """
        result = IntegrationResult(inquiry_id=inquiry.inquiry_id)
        
        node_id = inquiry.affected_nodes[0] if inquiry.affected_nodes else None
        if not node_id:
            result.issues.append("No affected node specified")
            return result
        
        # Get the node to determine hierarchy level
        node = None
        if ltm.has_pattern(node_id):
            node = ltm.get_pattern(node_id)
        elif stm.has_pattern(node_id):
            node = stm.get_pattern(node_id)
        
        hierarchy_level = node.hierarchy_level + 1 if node else 2
        
        # Extract example usages from response
        examples = self._extract_examples(response)
        
        for example in examples:
            # Create a higher-level pattern containing this node
            example_id = f"sequence:{example[:20].replace(' ', '_')}"  # Truncate for ID
            
            if not ltm.has_pattern(example_id) and not stm.has_pattern(example_id):
                new_node = Node.create_sequence(
                    label=example[:50],  # Truncate label
                    content=example,
                    hierarchy_level=hierarchy_level,
                    domain=inquiry.metadata.get("domain", "english"),
                )
                
                # Add to STM first
                stm.add_pattern(new_node)
                result.new_nodes.append(new_node.node_id)
                
                # Create edge from example to this pattern
                edge = Edge.create_composition(
                    parent_id=new_node.node_id,
                    child_id=node_id,
                    order=0,
                )
                stm.add_edge(edge)
                result.new_edges.append(edge.edge_id)
        
        result.success = len(result.new_nodes) > 0
        result.message = f"Created {len(result.new_nodes)} usage examples"
        
        return result
    
    def integrate_hierarchy_answer(
        self,
        inquiry: Inquiry,
        response: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> IntegrationResult:
        """
        Integrate a response about hierarchy gaps.
        
        Handles responses about intermediate patterns to fill hierarchy gaps.
        """
        result = IntegrationResult(inquiry_id=inquiry.inquiry_id)
        
        domain = inquiry.metadata.get("domain", "english")
        missing_levels = inquiry.metadata.get("missing_levels", [])
        
        if not missing_levels:
            result.issues.append("No missing levels specified")
            return result
        
        # Extract patterns from response
        patterns = self._extract_patterns(response)
        
        # Determine target hierarchy level
        target_level = min(missing_levels) if missing_levels else 1
        
        for pattern in patterns:
            pattern_id = f"pattern:{pattern}"
            
            if not ltm.has_pattern(pattern_id):
                new_node = Node.create_pattern(
                    label=pattern,
                    content=pattern,
                    hierarchy_level=target_level,
                    domain=domain,
                )
                stm.add_pattern(new_node)
                result.new_nodes.append(new_node.node_id)
        
        result.success = True
        result.message = f"Created {len(result.new_nodes)} intermediate patterns"
        
        return result
    
    def integrate_cross_domain_answer(
        self,
        inquiry: Inquiry,
        response: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> IntegrationResult:
        """
        Integrate a response about cross-domain relationships.
        
        Creates links between related patterns in different domains.
        """
        result = IntegrationResult(inquiry_id=inquiry.inquiry_id)
        
        affected = inquiry.affected_nodes
        if len(affected) < 2:
            result.issues.append("Need at least 2 nodes for cross-domain link")
            return result
        
        # Get the two nodes from different domains
        node1_id, node2_id = affected[0], affected[1]
        
        # Determine relationship type from response
        relationship = self._extract_relationship(response)
        
        # Create edge between domains
        edge_type = EdgeType.CLARIFIES if "clarif" in response.lower() else EdgeType.RELATES_TO
        
        # Add edge in both directions
        edge = Edge(
            edge_id=f"edge:{node1_id}:relates:{node2_id}",
            source_id=node1_id,
            target_id=node2_id,
            edge_type=edge_type,
            metadata={"relationship": relationship, "cross_domain": True},
        )
        
        # Determine which graph to update
        if ltm.has_pattern(node1_id):
            ltm.add_edge(edge)
        else:
            stm.add_edge(edge)
        
        result.new_edges.append(edge.edge_id)
        result.success = True
        result.message = f"Created cross-domain link: {relationship}"
        
        return result
    
    def integrate_validation_answer(
        self,
        inquiry: Inquiry,
        response: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> IntegrationResult:
        """
        Integrate a validation response.
        
        Handles confirmations or corrections about pattern validity.
        """
        result = IntegrationResult(inquiry_id=inquiry.inquiry_id)
        
        node_id = inquiry.affected_nodes[0] if inquiry.affected_nodes else None
        if not node_id:
            result.issues.append("No affected node specified")
            return result
        
        # Check if response is affirmative
        is_valid = self._is_affirmative(response)
        
        # Update node in appropriate memory
        if ltm.has_pattern(node_id):
            node = ltm.get_pattern(node_id)
            if node:
                node.is_uncertain = False
                node.is_valid = is_valid
                node.metadata["validation_response"] = response
                ltm.update_pattern(node)
                result.updated_nodes.append(node_id)
        elif stm.has_pattern(node_id):
            node = stm.get_pattern(node_id)
            if node:
                node.is_uncertain = False
                node.is_valid = is_valid
                node.metadata["validation_response"] = response
                result.updated_nodes.append(node_id)
        
        result.success = True
        result.message = f"Pattern marked as {'valid' if is_valid else 'invalid'}"
        
        return result
    
    def integrate_clarification_answer(
        self,
        inquiry: Inquiry,
        response: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
    ) -> IntegrationResult:
        """
        Integrate a clarification response.
        
        Stores the clarification as metadata on the affected pattern.
        """
        result = IntegrationResult(inquiry_id=inquiry.inquiry_id)
        
        node_id = inquiry.affected_nodes[0] if inquiry.affected_nodes else None
        if not node_id:
            result.issues.append("No affected node specified")
            return result
        
        # Add clarification to node metadata
        if ltm.has_pattern(node_id):
            node = ltm.get_pattern(node_id)
            if node:
                node.metadata["clarifications"] = node.metadata.get("clarifications", [])
                node.metadata["clarifications"].append({
                    "inquiry_id": inquiry.inquiry_id,
                    "clarification": response,
                    "timestamp": datetime.now().isoformat(),
                })
                ltm.update_pattern(node)
                result.updated_nodes.append(node_id)
        elif stm.has_pattern(node_id):
            node = stm.get_pattern(node_id)
            if node:
                node.metadata["clarifications"] = node.metadata.get("clarifications", [])
                node.metadata["clarifications"].append({
                    "inquiry_id": inquiry.inquiry_id,
                    "clarification": response,
                    "timestamp": datetime.now().isoformat(),
                })
        
        result.success = True
        result.message = "Clarification stored"
        
        return result
    
    def validate_integrated_pattern(
        self,
        node_id: str,
        graph: PatternGraph,
    ) -> Dict[str, Any]:
        """
        Validate a pattern after integration.
        
        Args:
            node_id: ID of the pattern to validate
            graph: The pattern graph
            
        Returns:
            Validation result dictionary
        """
        from rpa.validation.validator import Validator
        
        validator = Validator()
        node = graph.get_node(node_id)
        
        if not node:
            return {"is_valid": False, "error": "Node not found"}
        
        result = validator.validate_pattern_structure(node, graph)
        return result.to_dict()
    
    def _extract_components(
        self,
        response: str,
        expected: List[str],
    ) -> List[str]:
        """Extract component names from a response."""
        components = []
        
        # Check for expected components first
        for comp in expected:
            if comp in response:
                components.append(comp)
        
        # Try to extract quoted or bracketed items
        quoted = re.findall(r'["\']([^"\']+)["\']', response)
        bracketed = re.findall(r'\[([^\]]+)\]', response)
        
        for item in quoted + bracketed:
            item = item.strip()
            if item and item not in components:
                components.append(item)
        
        # If still empty, try single characters
        if not components:
            chars = re.findall(r'\b([a-zA-Z])\b', response)
            components.extend(chars[:5])  # Limit to 5
        
        return components
    
    def _extract_examples(self, response: str) -> List[str]:
        """Extract example sentences/usage from response."""
        examples = []
        
        # Look for sentences (ending with period)
        sentences = re.split(r'[.!?]', response)
        
        for sent in sentences:
            sent = sent.strip()
            # Filter out very short or very long sentences
            if 10 < len(sent) < 200:
                examples.append(sent)
        
        return examples[:5]  # Limit to 5 examples
    
    def _extract_patterns(self, response: str) -> List[str]:
        """Extract pattern names from response."""
        patterns = []
        
        # Look for quoted items
        quoted = re.findall(r'["\']([^"\']+)["\']', response)
        patterns.extend(quoted)
        
        # Look for words after "pattern", "word", "learn"
        keywords = re.findall(r'(?:pattern|word|learn)[:\s]+(\w+)', response, re.IGNORECASE)
        patterns.extend(keywords)
        
        return list(set(patterns))[:10]  # Unique, limited to 10
    
    def _extract_relationship(self, response: str) -> str:
        """Extract relationship description from response."""
        # Look for relationship indicators
        patterns = [
            r'(?:relates? to|means?|is like|similar to)[:\s]+([^.]+)',
            r'(?:because|since)[:\s]+([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return response[:100]  # Default to first 100 chars
    
    def _is_affirmative(self, response: str) -> bool:
        """Check if response is affirmative."""
        response_lower = response.lower().strip()
        
        # Negative indicators that override affirmative words
        negative = ["not sure", "don't think", "no", "incorrect", "wrong", "false", "invalid"]
        
        # Check for negative phrases first
        for neg in negative:
            if neg in response_lower:
                return False
        
        affirmative = [
            "yes", "correct", "right", "true", "valid", "ok", "okay",
            "affirmative", "confirm", "sure", "indeed", "exactly",
        ]
        
        # Check for affirmative words at start (first 3 words)
        first_words = response_lower.split()[:3]
        # Also check the first word without punctuation
        first_word = response_lower.split()[0].rstrip('!.?') if response_lower.split() else ''
        
        return any(word in affirmative for word in first_words) or first_word in affirmative
    
    def get_integration_result(self, inquiry_id: str) -> Optional[IntegrationResult]:
        """Get a previous integration result."""
        return self._integration_history.get(inquiry_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        total = len(self._integration_history)
        successful = sum(1 for r in self._integration_history.values() if r.success)
        
        return {
            "total_integrations": total,
            "successful": successful,
            "failed": total - successful,
            "nodes_created": sum(len(r.new_nodes) for r in self._integration_history.values()),
            "edges_created": sum(len(r.new_edges) for r in self._integration_history.values()),
        }
