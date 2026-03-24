"""
RPA Mutation Pipeline

Enhanced pattern mutation with multiple strategies and lineage tracking.
Extends PatternMutator with parameter tweaking, structure rearrangement,
and cross-pattern merging.

Ticket: SI-005
"""

import os
import json
import logging
import re
import ast
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import hashlib

from rpa.closed_loop.pattern_mutator import (
    PatternMutator, MutationType, MutationRecord, PatternVersion
)
from rpa.closed_loop.outcome_evaluator import Outcome, OutcomeType

logger = logging.getLogger(__name__)


class MutationStrategy(Enum):
    """Advanced mutation strategies for pattern improvement."""
    PARAMETER_TWEAK = "parameter_tweak"         # Adjust numeric/string parameters
    STRUCTURE_REARRANGE = "structure_rearrange" # Reorganize pattern structure
    CROSS_PATTERN_MERGE = "cross_pattern_merge" # Combine patterns
    CONTEXT_EXPANSION = "context_expansion"     # Add context to pattern
    SIMPLIFICATION = "simplification"           # Simplify complex patterns
    OPTIMIZATION = "optimization"               # Optimize for performance


@dataclass
class MutationLineage:
    """Track the full lineage of a pattern mutation."""
    lineage_id: str
    root_pattern_id: str
    current_pattern_id: str
    depth: int
    path: List[str]  # List of pattern IDs from root to current
    mutation_types: List[str]  # Types of mutations along the path
    success_rates: List[float]  # Success rate after each mutation
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'lineage_id': self.lineage_id,
            'root_pattern_id': self.root_pattern_id,
            'current_pattern_id': self.current_pattern_id,
            'depth': self.depth,
            'path': self.path,
            'mutation_types': self.mutation_types,
            'success_rates': self.success_rates,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class MutationResult:
    """Result of a mutation attempt."""
    success: bool
    strategy: MutationStrategy
    original_content: str
    mutated_content: str
    changes: Dict[str, Any]
    confidence: float
    message: str
    lineage_update: Optional[MutationLineage] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'strategy': self.strategy.value,
            'original_content': self.original_content,
            'mutated_content': self.mutated_content,
            'changes': self.changes,
            'confidence': self.confidence,
            'message': self.message,
            'lineage_update': self.lineage_update.to_dict() if self.lineage_update else None
        }


class MutationPipeline:
    """
    Enhanced mutation pipeline with multiple strategies.
    
    Provides sophisticated mutation capabilities:
    - Parameter tweaking for fine adjustments
    - Structure rearrangement for reorganization
    - Cross-pattern merging for combining patterns
    - Lineage tracking for mutation history
    
    Usage:
        pipeline = MutationPipeline(mutator, ltm)
        
        # Apply specific strategy
        result = pipeline.apply_strategy(pattern_id, MutationStrategy.PARAMETER_TWEAK)
        
        # Auto-select best strategy
        result = pipeline.mutate_with_best_strategy(pattern_id, outcome)
        
        # Get lineage
        lineage = pipeline.get_lineage(pattern_id)
    """
    
    def __init__(
        self,
        mutator: PatternMutator,
        ltm: Any,
        storage_path: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize mutation pipeline.
        
        Args:
            mutator: PatternMutator instance
            ltm: Long-term memory instance
            storage_path: Path for lineage persistence
            config: Configuration options
        """
        self.mutator = mutator
        self.ltm = ltm
        self.storage_path = storage_path or Path.home() / ".rpa" / "mutations"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.config = config or {
            'max_lineage_depth': 10,
            'min_confidence_for_auto_apply': 0.7,
            'enable_cross_pattern_merge': True,
            'parameter_tweak_range': 0.2,  # +/- 20%
            'max_merge_candidates': 5
        }
        
        # Lineage tracking
        self._lineages: Dict[str, MutationLineage] = {}
        self._pattern_to_lineage: Dict[str, str] = {}  # pattern_id -> lineage_id
        
        # Strategy executors
        self._strategies: Dict[MutationStrategy, Callable] = {
            MutationStrategy.PARAMETER_TWEAK: self._execute_parameter_tweak,
            MutationStrategy.STRUCTURE_REARRANGE: self._execute_structure_rearrange,
            MutationStrategy.CROSS_PATTERN_MERGE: self._execute_cross_pattern_merge,
            MutationStrategy.CONTEXT_EXPANSION: self._execute_context_expansion,
            MutationStrategy.SIMPLIFICATION: self._execute_simplification,
            MutationStrategy.OPTIMIZATION: self._execute_optimization,
        }
        
        # Statistics
        self._stats = {
            'total_mutations': 0,
            'successful_mutations': 0,
            'by_strategy': {s.value: {'attempts': 0, 'success': 0} for s in MutationStrategy},
            'avg_confidence': 0.0,
            'lineage_depths': []
        }
        
        # Load state
        self._load_state()
    
    def apply_strategy(
        self,
        pattern_id: str,
        strategy: MutationStrategy,
        context: Optional[Dict[str, Any]] = None
    ) -> MutationResult:
        """
        Apply a specific mutation strategy to a pattern.
        
        Args:
            pattern_id: ID of pattern to mutate
            strategy: Mutation strategy to apply
            context: Additional context for mutation
            
        Returns:
            MutationResult with outcome details
        """
        # Get pattern content
        pattern = self._get_pattern(pattern_id)
        if pattern is None:
            return MutationResult(
                success=False,
                strategy=strategy,
                original_content="",
                mutated_content="",
                changes={},
                confidence=0.0,
                message=f"Pattern {pattern_id} not found"
            )
        
        content = pattern.content if hasattr(pattern, 'content') else str(pattern)
        
        # Execute strategy
        executor = self._strategies.get(strategy)
        if executor is None:
            return MutationResult(
                success=False,
                strategy=strategy,
                original_content=content,
                mutated_content=content,
                changes={},
                confidence=0.0,
                message=f"Unknown strategy: {strategy}"
            )
        
        result = executor(pattern_id, content, context or {})
        
        # Update statistics
        self._stats['total_mutations'] += 1
        self._stats['by_strategy'][strategy.value]['attempts'] += 1
        
        if result.success:
            self._stats['successful_mutations'] += 1
            self._stats['by_strategy'][strategy.value]['success'] += 1
            
            # Update lineage
            lineage = self._update_lineage(pattern_id, strategy, result.confidence)
            result.lineage_update = lineage
            
            # Create new version if content changed
            if result.mutated_content != content:
                self._create_mutated_version(pattern_id, result, strategy)
        
        # Update average confidence
        total = self._stats['total_mutations']
        current_avg = self._stats['avg_confidence']
        self._stats['avg_confidence'] = (current_avg * (total - 1) + result.confidence) / total
        
        # Save state
        self._save_state()
        
        return result
    
    def mutate_with_best_strategy(
        self,
        pattern_id: str,
        outcome: Optional[Outcome] = None
    ) -> MutationResult:
        """
        Automatically select and apply the best mutation strategy.
        
        Args:
            pattern_id: ID of pattern to mutate
            outcome: Optional outcome that triggered mutation
            
        Returns:
            MutationResult from the best strategy
        """
        # Score each strategy
        scores = self._score_strategies(pattern_id, outcome)
        
        # Sort by score
        sorted_strategies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Try strategies in order until one succeeds
        for strategy, score in sorted_strategies:
            if score < self.config['min_confidence_for_auto_apply']:
                continue
            
            result = self.apply_strategy(pattern_id, strategy, {'outcome': outcome})
            
            if result.success and result.confidence >= self.config['min_confidence_for_auto_apply']:
                return result
        
        # No strategy succeeded
        return MutationResult(
            success=False,
            strategy=sorted_strategies[0][0] if sorted_strategies else MutationStrategy.PARAMETER_TWEAK,
            original_content="",
            mutated_content="",
            changes={},
            confidence=0.0,
            message="No mutation strategy succeeded"
        )
    
    def _score_strategies(
        self,
        pattern_id: str,
        outcome: Optional[Outcome]
    ) -> Dict[MutationStrategy, float]:
        """Score each strategy for the given pattern."""
        scores = {}
        
        pattern = self._get_pattern(pattern_id)
        content = pattern.content if pattern and hasattr(pattern, 'content') else ""
        
        # Parameter tweak: good for patterns with numbers/parameters
        param_count = len(re.findall(r'\b\d+\.?\d*\b', content))
        scores[MutationStrategy.PARAMETER_TWEAK] = min(1.0, param_count * 0.2)
        
        # Structure rearrange: good for complex patterns
        complexity = self._calculate_complexity(content)
        scores[MutationStrategy.STRUCTURE_REARRANGE] = min(1.0, complexity * 0.1)
        
        # Cross pattern merge: good if similar patterns exist
        similar_count = len(self._find_similar_patterns(pattern_id, content))
        scores[MutationStrategy.CROSS_PATTERN_MERGE] = min(1.0, similar_count * 0.15)
        
        # Context expansion: good for short patterns
        if len(content) < 100:
            scores[MutationStrategy.CONTEXT_EXPANSION] = 0.8
        else:
            scores[MutationStrategy.CONTEXT_EXPANSION] = 0.3
        
        # Simplification: good for very complex patterns
        if complexity > 10:
            scores[MutationStrategy.SIMPLIFICATION] = 0.9
        else:
            scores[MutationStrategy.SIMPLIFICATION] = 0.2
        
        # Optimization: good based on failure type
        if outcome and outcome.outcome_type == OutcomeType.ERROR:
            scores[MutationStrategy.OPTIMIZATION] = 0.7
        else:
            scores[MutationStrategy.OPTIMIZATION] = 0.4
        
        return scores
    
    def _execute_parameter_tweak(
        self,
        pattern_id: str,
        content: str,
        context: Dict[str, Any]
    ) -> MutationResult:
        """
        Tweak numeric or string parameters in the pattern.
        
        Strategy: Identify parameters and adjust them within a range.
        """
        original = content
        changes = {}
        tweak_count = 0
        
        # Find numeric parameters
        def tweak_number(match):
            nonlocal tweak_count
            try:
                value = float(match.group())
                tweak_range = self.config['parameter_tweak_range']
                
                # Apply small random tweak (deterministic based on hash)
                hash_val = int(hashlib.md5(f"{pattern_id}{match.start()}".encode()).hexdigest()[:8], 16)
                factor = 1.0 + ((hash_val % 100) / 250.0 - 0.2) * tweak_range
                
                new_value = value * factor
                tweak_count += 1
                
                # Preserve integer format
                if '.' not in match.group():
                    return str(int(round(new_value)))
                return f"{new_value:.4f}".rstrip('0').rstrip('.')
            except:
                return match.group()
        
        # Tweak numbers
        mutated = re.sub(r'\b\d+\.?\d*\b', tweak_number, content)
        
        # Also try tweaking string parameters
        string_params = re.findall(r'["\']([^"\']+)["\']', content)
        if string_params:
            # For now, just note potential string params
            changes['string_params_found'] = string_params[:5]
        
        success = mutated != original and tweak_count > 0
        confidence = min(1.0, tweak_count * 0.3) if success else 0.0
        
        changes['parameters_tweaked'] = tweak_count
        
        return MutationResult(
            success=success,
            strategy=MutationStrategy.PARAMETER_TWEAK,
            original_content=original,
            mutated_content=mutated,
            changes=changes,
            confidence=confidence,
            message=f"Tweaked {tweak_count} parameters"
        )
    
    def _execute_structure_rearrange(
        self,
        pattern_id: str,
        content: str,
        context: Dict[str, Any]
    ) -> MutationResult:
        """
        Rearrange the structure of a pattern.
        
        Strategy: Reorder components, extract common parts, or reorganize.
        """
        original = content
        changes = {}
        
        # Try different rearrangements based on content type
        lines = content.split('\n')
        
        if len(lines) > 2:
            # Multi-line: try reordering non-dependent lines
            # Simple heuristic: move comment lines to top
            comments = [l for l in lines if l.strip().startswith('#')]
            code = [l for l in lines if not l.strip().startswith('#')]
            
            if comments and code:
                mutated = '\n'.join(comments + [''] + code)
                changes['rearrangement'] = 'comments_to_top'
            else:
                # Try reversing order (for certain patterns)
                mutated = '\n'.join(reversed(lines))
                changes['rearrangement'] = 'reversed'
        else:
            # Single line or short: try swapping parts
            parts = re.split(r'([;,\|])', content)
            if len(parts) > 3:
                # Swap sections
                mid = len(parts) // 2
                mutated = ''.join(parts[mid:] + parts[:mid])
                changes['rearrangement'] = 'swapped_halves'
            else:
                mutated = content
        
        success = mutated != original
        confidence = 0.6 if success else 0.0
        
        return MutationResult(
            success=success,
            strategy=MutationStrategy.STRUCTURE_REARRANGE,
            original_content=original,
            mutated_content=mutated,
            changes=changes,
            confidence=confidence,
            message=f"Rearranged structure: {changes.get('rearrangement', 'none')}"
        )
    
    def _execute_cross_pattern_merge(
        self,
        pattern_id: str,
        content: str,
        context: Dict[str, Any]
    ) -> MutationResult:
        """
        Merge with a similar pattern from the knowledge base.
        
        Strategy: Find similar patterns and combine their strengths.
        """
        if not self.config['enable_cross_pattern_merge']:
            return MutationResult(
                success=False,
                strategy=MutationStrategy.CROSS_PATTERN_MERGE,
                original_content=content,
                mutated_content=content,
                changes={},
                confidence=0.0,
                message="Cross-pattern merge disabled"
            )
        
        original = content
        changes = {}
        
        # Find similar patterns
        similar = self._find_similar_patterns(pattern_id, content)
        
        if not similar:
            return MutationResult(
                success=False,
                strategy=MutationStrategy.CROSS_PATTERN_MERGE,
                original_content=original,
                mutated_content=original,
                changes={'similar_found': 0},
                confidence=0.0,
                message="No similar patterns found for merging"
            )
        
        # Get the best candidate
        best_candidate = similar[0]
        candidate_content = best_candidate.get('content', '')
        
        # Merge strategy: combine unique parts
        original_parts = set(content.split())
        candidate_parts = set(candidate_content.split())
        
        # Add parts from candidate that aren't in original
        new_parts = candidate_parts - original_parts
        
        if new_parts:
            # Add new parts as alternatives
            mutated = content + " # Merged: " + ' '.join(list(new_parts)[:5])
            changes['merged_from'] = best_candidate.get('pattern_id')
            changes['new_parts_added'] = list(new_parts)[:5]
        else:
            mutated = content
        
        success = mutated != original
        confidence = best_candidate.get('similarity', 0.5) if success else 0.0
        
        return MutationResult(
            success=success,
            strategy=MutationStrategy.CROSS_PATTERN_MERGE,
            original_content=original,
            mutated_content=mutated,
            changes=changes,
            confidence=confidence,
            message=f"Merged with pattern {best_candidate.get('pattern_id', 'unknown')}"
        )
    
    def _execute_context_expansion(
        self,
        pattern_id: str,
        content: str,
        context: Dict[str, Any]
    ) -> MutationResult:
        """
        Expand pattern with additional context.
        
        Strategy: Add wrapping context or additional conditions.
        """
        original = content
        changes = {}
        
        # Determine what context to add
        expanded = content
        
        # Add try-except wrapper for code patterns
        if 'def ' in content or 'class ' in content or '=' in content:
            if 'try:' not in content and 'except' not in content:
                expanded = f"try:\n    {content.replace(chr(10), chr(10) + '    ')}\nexcept Exception as e:\n    pass  # Safe fallback"
                changes['expansion'] = 'try_except_wrapper'
        
        # Add condition check for variable patterns
        elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', content.strip()):
            expanded = f"if {content} is not None:\n    {content}"
            changes['expansion'] = 'none_check'
        
        # Add validation for expression patterns
        elif any(op in content for op in ['+', '-', '*', '/']):
            # Wrap in validation
            expanded = f"# Validated expression\n{content}"
            changes['expansion'] = 'validation_comment'
        
        success = expanded != original
        confidence = 0.7 if success else 0.0
        
        return MutationResult(
            success=success,
            strategy=MutationStrategy.CONTEXT_EXPANSION,
            original_content=original,
            mutated_content=expanded,
            changes=changes,
            confidence=confidence,
            message=f"Added context: {changes.get('expansion', 'none')}"
        )
    
    def _execute_simplification(
        self,
        pattern_id: str,
        content: str,
        context: Dict[str, Any]
    ) -> MutationResult:
        """
        Simplify a complex pattern.
        
        Strategy: Remove redundancy, shorten expressions.
        """
        original = content
        changes = {}
        
        simplified = content
        
        # Remove duplicate spaces
        simplified = re.sub(r' +', ' ', simplified)
        
        # Remove duplicate newlines
        simplified = re.sub(r'\n{3,}', '\n\n', simplified)
        
        # Simplify boolean expressions
        simplified = re.sub(r'== True', '', simplified)
        simplified = re.sub(r'== False', 'not ', simplified)
        
        # Remove redundant parentheses
        simplified = re.sub(r'\(\(([^()]+)\)\)', r'(\1)', simplified)
        
        # Remove comments (optional, based on context)
        if context.get('remove_comments', False):
            simplified = re.sub(r'#.*$', '', simplified, flags=re.MULTILINE)
            changes['comments_removed'] = True
        
        changes['original_length'] = len(original)
        changes['simplified_length'] = len(simplified)
        
        success = simplified != original
        reduction = len(original) - len(simplified)
        confidence = min(1.0, reduction / max(1, len(original)) * 2) if success else 0.0
        
        return MutationResult(
            success=success,
            strategy=MutationStrategy.SIMPLIFICATION,
            original_content=original,
            mutated_content=simplified,
            changes=changes,
            confidence=confidence,
            message=f"Simplified: {reduction} characters reduced"
        )
    
    def _execute_optimization(
        self,
        pattern_id: str,
        content: str,
        context: Dict[str, Any]
    ) -> MutationResult:
        """
        Optimize pattern for performance.
        
        Strategy: Apply common optimization patterns.
        """
        original = content
        changes = {}
        
        optimized = content
        
        # List comprehension optimization
        if 'for ' in content and 'append' in content:
            # Try to convert to list comprehension (heuristic)
            changes['optimization_attempt'] = 'list_comprehension'
        
        # Cache/memoization hint
        if 'def ' in content and '(' in content:
            optimized = f"@lru_cache(maxsize=None)\n{content}"
            changes['optimization'] = 'memoization'
        
        # Use local variables
        if '.' in content and '=' in content:
            # Suggest using local variable for repeated attribute access
            attrs = re.findall(r'(\w+\.\w+)', content)
            if attrs:
                changes['suggested_locals'] = list(set(attrs))[:3]
        
        success = optimized != original
        confidence = 0.6 if success else 0.0
        
        return MutationResult(
            success=success,
            strategy=MutationStrategy.OPTIMIZATION,
            original_content=original,
            mutated_content=optimized,
            changes=changes,
            confidence=confidence,
            message=f"Applied optimization: {changes.get('optimization', 'analysis_only')}"
        )
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate complexity score for content."""
        score = 0
        
        # Count nesting levels
        score += content.count('(') + content.count('[') + content.count('{')
        
        # Count control structures
        score += len(re.findall(r'\b(if|for|while|try|with|def|class)\b', content))
        
        # Count operators
        score += len(re.findall(r'[+\-*/<>=!&|]', content))
        
        # Length factor
        score += len(content) // 100
        
        return score
    
    def _find_similar_patterns(
        self,
        pattern_id: str,
        content: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar patterns in LTM."""
        similar = []
        
        if self.ltm is None:
            return similar
        
        try:
            # Get all patterns
            all_patterns = list(self.ltm._graph.nodes.values())
            
            # Calculate similarity scores
            content_words = set(content.lower().split())
            
            for node in all_patterns:
                if node.node_id == pattern_id:
                    continue
                
                node_content = node.content if hasattr(node, 'content') else str(node)
                node_words = set(node_content.lower().split())
                
                # Jaccard similarity
                if content_words and node_words:
                    intersection = len(content_words & node_words)
                    union = len(content_words | node_words)
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > 0.3:  # Threshold
                        similar.append({
                            'pattern_id': node.node_id,
                            'content': node_content,
                            'similarity': similarity
                        })
            
            # Sort by similarity
            similar.sort(key=lambda x: x['similarity'], reverse=True)
            
        except Exception as e:
            logger.warning(f"Error finding similar patterns: {e}")
        
        return similar[:limit]
    
    def _get_pattern(self, pattern_id: str) -> Any:
        """Get pattern from LTM."""
        if self.ltm is None:
            return None
        
        try:
            return self.ltm.get_pattern(pattern_id)
        except:
            return None
    
    def _update_lineage(
        self,
        pattern_id: str,
        strategy: MutationStrategy,
        confidence: float
    ) -> MutationLineage:
        """Update or create lineage for a pattern."""
        # Check if pattern already has lineage
        lineage_id = self._pattern_to_lineage.get(pattern_id)
        
        if lineage_id and lineage_id in self._lineages:
            # Update existing lineage
            lineage = self._lineages[lineage_id]
            lineage.depth += 1
            lineage.path.append(pattern_id)
            lineage.mutation_types.append(strategy.value)
            lineage.success_rates.append(confidence)
            lineage.current_pattern_id = pattern_id
        else:
            # Create new lineage
            lineage_id = f"lineage_{uuid.uuid4().hex[:8]}"
            lineage = MutationLineage(
                lineage_id=lineage_id,
                root_pattern_id=pattern_id,
                current_pattern_id=pattern_id,
                depth=1,
                path=[pattern_id],
                mutation_types=[strategy.value],
                success_rates=[confidence]
            )
            self._lineages[lineage_id] = lineage
        
        self._pattern_to_lineage[pattern_id] = lineage_id
        self._stats['lineage_depths'].append(lineage.depth)
        
        return lineage
    
    def _create_mutated_version(
        self,
        pattern_id: str,
        result: MutationResult,
        strategy: MutationStrategy
    ) -> Optional[PatternVersion]:
        """Create a new version with mutated content."""
        try:
            # Create through mutator
            active = self.mutator.get_active_version(pattern_id)
            
            if active:
                new_version = self.mutator._create_version(
                    pattern_id=pattern_id,
                    content=result.mutated_content,
                    label=active.label,
                    mutation_type=MutationType.REFINE,  # Map to standard type
                    mutation_reason=f"Pipeline strategy: {strategy.value}",
                    parent_version_id=active.version_id
                )
                return new_version
        except Exception as e:
            logger.warning(f"Could not create mutated version: {e}")
        
        return None
    
    def get_lineage(self, pattern_id: str) -> Optional[MutationLineage]:
        """Get the lineage for a pattern."""
        lineage_id = self._pattern_to_lineage.get(pattern_id)
        if lineage_id:
            return self._lineages.get(lineage_id)
        return None
    
    def get_lineage_tree(self, pattern_id: str) -> Dict[str, Any]:
        """Get the full lineage tree for visualization."""
        lineage = self.get_lineage(pattern_id)
        
        if lineage is None:
            return {'error': 'No lineage found'}
        
        tree = {
            'root': lineage.root_pattern_id,
            'current': lineage.current_pattern_id,
            'depth': lineage.depth,
            'path': [],
            'mutations': []
        }
        
        for i, pid in enumerate(lineage.path):
            node = {
                'pattern_id': pid,
                'mutation_type': lineage.mutation_types[i] if i < len(lineage.mutation_types) else None,
                'success_rate': lineage.success_rates[i] if i < len(lineage.success_rates) else None
            }
            tree['path'].append(node)
        
        tree['mutations'] = lineage.mutation_types
        
        return tree
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            **self._stats,
            'total_lineages': len(self._lineages),
            'patterns_tracked': len(self._pattern_to_lineage),
            'avg_lineage_depth': sum(self._stats['lineage_depths']) / max(1, len(self._stats['lineage_depths']))
        }
    
    def _load_state(self):
        """Load persisted state."""
        state_file = self.storage_path / "mutation_pipeline_state.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Load lineages
                for lid, ldata in state.get('lineages', {}).items():
                    lineage = MutationLineage(
                        lineage_id=ldata['lineage_id'],
                        root_pattern_id=ldata['root_pattern_id'],
                        current_pattern_id=ldata['current_pattern_id'],
                        depth=ldata['depth'],
                        path=ldata['path'],
                        mutation_types=ldata['mutation_types'],
                        success_rates=ldata['success_rates']
                    )
                    self._lineages[lid] = lineage
                
                self._pattern_to_lineage = state.get('pattern_to_lineage', {})
                self._stats = state.get('stats', self._stats)
                
                logger.info(f"Loaded mutation pipeline state: {len(self._lineages)} lineages")
                
            except Exception as e:
                logger.warning(f"Could not load pipeline state: {e}")
    
    def _save_state(self):
        """Save current state."""
        state_file = self.storage_path / "mutation_pipeline_state.json"
        
        try:
            state = {
                'lineages': {lid: lin.to_dict() for lid, lin in self._lineages.items()},
                'pattern_to_lineage': self._pattern_to_lineage,
                'stats': self._stats,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not save pipeline state: {e}")
    
    def __repr__(self) -> str:
        return f"MutationPipeline(mutations={self._stats['total_mutations']}, lineages={len(self._lineages)})"
