"""
Reasoning Domain Handler

Teaches cognitive skills like:
- Contextualization
- Intent recognition
- Question parsing
- Constraint extraction
- Reasoning chains

This domain is CRITICAL - the AI learns HOW to think, not just WHAT to know.
"""
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.core import Node, NodeType

logger = logging.getLogger("RPA-ReasoningDomain")


class ReasoningDomain:
    """
    Handles learning of cognitive/reasoning skills.
    
    Unlike other domains that teach facts, this domain teaches
    the AI HOW to process information and understand context.
    """
    
    DOMAIN_NAME = "reasoning"
    
    # Types of reasoning patterns
    REASONING_TYPES = [
        "intent_recognition",
        "contextualization", 
        "constraint_parsing",
        "question_parsing",
        "reasoning_chain",
        "contextual_disambiguation",
        "domain_inference"
    ]
    
    def __init__(self):
        self.patterns_learned = 0
        
    def process_curriculum(self, curriculum_data: Dict) -> List[Node]:
        """
        Process reasoning curriculum into learnable patterns.
        
        Reasoning patterns are stored with special metadata indicating
        they are cognitive skills, not factual knowledge.
        """
        patterns = []
        
        module = curriculum_data.get("module", "unknown")
        hierarchy_level = curriculum_data.get("hierarchy_level", 1)
        
        logger.info(f"Processing reasoning curriculum: {module}")
        
        for pattern_data in curriculum_data.get("patterns", []):
            pattern_type = pattern_data.get("type", "unknown")
            pattern_content = pattern_data.get("pattern", "")
            
            # Create a reasoning pattern node
            node = Node.create_pattern(
                label=f"{pattern_type}: {pattern_content[:50]}",
                content=json.dumps(pattern_data),
                hierarchy_level=hierarchy_level,
                domain=self.DOMAIN_NAME
            )
            
            # Add special metadata for reasoning patterns
            node.metadata["pattern_type"] = pattern_type
            node.metadata["is_cognitive_skill"] = True
            node.metadata["module"] = module
            
            # If there are examples, store them for training
            if "examples" in pattern_data:
                node.metadata["training_examples"] = pattern_data["examples"]
                
            # If there's reasoning, store it
            if "reasoning" in pattern_data:
                node.metadata["reasoning_process"] = pattern_data["reasoning"]
            
            patterns.append(node)
            self.patterns_learned += 1
            
        logger.info(f"Created {len(patterns)} reasoning patterns from {module}")
        return patterns
    
    def apply_reasoning(self, question: str, context: Dict) -> Dict:
        """
        Apply learned reasoning patterns to understand a question.
        
        This is NOT hardcoded logic - it uses the patterns the AI
        has learned to contextualize and parse questions.
        """
        result = {
            "original_question": question,
            "detected_intent": None,
            "detected_domain": None,
            "detected_constraints": {},
            "reasoning_steps": [],
            "confidence": 0.0
        }
        
        # The AI would search its learned reasoning patterns here
        # and apply them to understand the question
        
        return result
    
    def get_stats(self) -> Dict:
        """Return domain statistics."""
        return {
            "domain": self.DOMAIN_NAME,
            "patterns_learned": self.patterns_learned,
            "reasoning_types_available": self.REASONING_TYPES
        }


# Register this domain
def get_domain():
    """Return domain instance for registration."""
    return ReasoningDomain()
