"""
LanguageAgent - Specialized agent for natural language understanding.

Extends BaseAgent with:
- Sentence parsing and generation
- Concept explanation
- Cross-domain concept translation
- Grammar and structure analysis
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid
import logging
import re

from rpa.agents.base_agent import BaseAgent, Inquiry
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.core.graph import Node, NodeType

logger = logging.getLogger(__name__)


@dataclass
class ParsedSentence:
    """Result of sentence parsing."""
    parse_id: str
    sentence: str
    words: List[str]
    structure: Dict[str, Any]
    pos_tags: List[Tuple[str, str]]  # (word, tag) pairs
    parsed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "parse_id": self.parse_id,
            "sentence": self.sentence,
            "words": self.words,
            "structure": self.structure,
            "pos_tags": self.pos_tags,
            "parsed_at": self.parsed_at.isoformat(),
        }


@dataclass
class Concept:
    """Represents a linguistic or semantic concept."""
    concept_id: str
    name: str
    category: str  # noun, verb, adjective, concept, etc.
    definition: str
    examples: List[str]
    related_concepts: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "category": self.category,
            "definition": self.definition,
            "examples": self.examples,
            "related_concepts": self.related_concepts,
            "metadata": self.metadata,
        }


class LanguageAgent(BaseAgent):
    """
    Specialized agent for natural language understanding.

    Extends BaseAgent with language-specific capabilities:
    - Sentence parsing and structure analysis
    - Sentence generation from components
    - Concept explanation and definition
    - Cross-domain concept translation
    """

    # Common English words by category
    COMMON_NOUNS = ["cat", "dog", "house", "car", "book", "tree", "water", "food"]
    COMMON_VERBS = ["run", "walk", "eat", "sleep", "read", "write", "speak", "think"]
    COMMON_ADJECTIVES = ["big", "small", "good", "bad", "fast", "slow", "happy", "sad"]
    ARTICLES = ["the", "a", "an"]
    PREPOSITIONS = ["in", "on", "at", "to", "from", "with", "by", "for"]

    # Simple POS tag patterns
    POS_PATTERNS = {
        "article": r"^(the|a|an)$",
        "preposition": r"^(in|on|at|to|from|with|by|for|of|about)$",
        "pronoun": r"^(I|you|he|she|it|we|they|me|him|her|us|them)$",
        "verb_ed": r"^.+ed$",  # past tense verbs
        "verb_ing": r"^.+ing$",  # present participle
        "plural_noun": r"^.+s$",  # simple plural detection
    }

    def __init__(
        self,
        language: str = "english",
        agent_id: Optional[str] = None,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """
        Initialize a LanguageAgent.

        Args:
            language: The language this agent handles
            agent_id: Optional agent ID
            ltm: Optional LongTermMemory instance
            episodic: Optional EpisodicMemory instance
        """
        super().__init__(
            domain=f"language_{language}",
            agent_id=agent_id,
            ltm=ltm,
            episodic=episodic,
        )
        self.language = language
        self._parsed_sentences: Dict[str, ParsedSentence] = {}
        self._concepts: Dict[str, Concept] = {}

        # Initialize common concepts
        self._initialize_concepts()

    def _initialize_concepts(self) -> None:
        """Initialize common linguistic concepts."""
        common_concepts = [
            ("sentence", "structure", "A grammatical unit consisting of words",
             ["The cat sat.", "I love coding.", "She reads books."]),
            ("noun", "part_of_speech", "A word representing a person, place, thing, or idea",
             ["cat", "house", "happiness", "computer"]),
            ("verb", "part_of_speech", "A word expressing an action or state",
             ["run", "is", "think", "become"]),
            ("adjective", "part_of_speech", "A word describing a noun",
             ["big", "beautiful", "quick", "happy"]),
            ("subject", "sentence_role", "The doer of the action in a sentence",
             ["The cat (in 'The cat sat')", "I (in 'I run')"]),
            ("predicate", "sentence_role", "The part of a sentence containing the verb",
             ["sat on the mat", "runs quickly"]),
        ]
        for name, category, definition, examples in common_concepts:
            cid = f"concept_{name}"
            self._concepts[cid] = Concept(
                concept_id=cid,
                name=name,
                category=category,
                definition=definition,
                examples=examples,
                related_concepts=[],
            )

    def parse_sentence(
        self,
        sentence: str,
    ) -> ParsedSentence:
        """
        Parse a sentence into components.

        Args:
            sentence: The sentence to parse

        Returns:
            ParsedSentence with analysis
        """
        self._update_activity()

        # Tokenize
        words = self._tokenize(sentence)

        # POS tagging (simple rule-based)
        pos_tags = self._simple_pos_tag(words)

        # Extract structure
        structure = self._extract_structure(words, pos_tags)

        parsed = ParsedSentence(
            parse_id=f"parse_{uuid.uuid4().hex[:8]}",
            sentence=sentence,
            words=words,
            structure=structure,
            pos_tags=pos_tags,
        )

        self._parsed_sentences[parsed.parse_id] = parsed

        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id=self.agent_id,
            data={
                "action": "parse_sentence",
                "sentence": sentence,
                "words_count": len(words),
            },
        )

        return parsed

    def generate_sentence(
        self,
        components: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a sentence from components.

        Args:
            components: Dictionary with optional keys:
                - subject: Subject noun phrase
                - verb: Verb
                - object: Object noun phrase
                - adjective: Adjective for subject or object
                - adverb: Adverb for verb

        Returns:
            Generated sentence and metadata
        """
        self._update_activity()

        # Get components with defaults
        subject = components.get("subject", "The cat")
        verb = components.get("verb", "sat")
        obj = components.get("object", "")
        adjective = components.get("adjective", "")
        adverb = components.get("adverb", "")

        # Build sentence
        if adjective:
            if subject.startswith("The "):
                subject = f"The {adjective} {subject[4:]}"
            else:
                subject = f"{adjective} {subject}"

        if adverb:
            verb = f"{adverb} {verb}"

        sentence = f"{subject} {verb}"
        if obj:
            sentence += f" {obj}"
        sentence += "."

        return {
            "success": True,
            "sentence": sentence,
            "components": components,
            "message": f"Generated sentence: {sentence}",
        }

    def explain_concept(
        self,
        concept_name: str,
        detail_level: str = "medium",
    ) -> Dict[str, Any]:
        """
        Explain a concept.

        Args:
            concept_name: Name of the concept to explain
            detail_level: Level of detail (brief, medium, detailed)

        Returns:
            Concept explanation
        """
        self._update_activity()

        # Check if concept exists in our knowledge
        concept = None
        for c in self._concepts.values():
            if c.name.lower() == concept_name.lower():
                concept = c
                break

        # Also check LTM
        if not concept:
            patterns = self.ltm.search(concept_name, limit=1)
            if patterns:
                pattern = patterns[0]
                concept = Concept(
                    concept_id=pattern.node_id,
                    name=pattern.label,
                    category="learned",
                    definition=pattern.content,
                    examples=[],
                    related_concepts=[],
                )

        if concept:
            explanation = {
                "success": True,
                "concept": concept.name,
                "category": concept.category,
                "definition": concept.definition,
                "examples": concept.examples[:3] if detail_level != "brief" else [],
                "related": concept.related_concepts if detail_level == "detailed" else [],
            }

            if detail_level == "detailed":
                explanation["additional_info"] = (
                    f"This concept belongs to the '{concept.category}' category. "
                    f"It has {len(concept.examples)} known examples."
                )

            return explanation

        return {
            "success": False,
            "concept": concept_name,
            "message": f"Concept '{concept_name}' not found in knowledge base",
            "suggestion": "Try teaching me about this concept first",
        }

    def translate_concept(
        self,
        concept: str,
        from_domain: str,
        to_domain: str,
    ) -> Dict[str, Any]:
        """
        Translate a concept between domains.

        Args:
            concept: The concept to translate
            from_domain: Source domain
            to_domain: Target domain

        Returns:
            Translation result
        """
        self._update_activity()

        # Cross-domain translations
        translations = {
            ("english", "python"): {
                "if": "if statement: if condition:",
                "then": "code block after condition",
                "else": "else clause: else:",
                "while": "while loop: while condition:",
                "for": "for loop: for item in iterable:",
                "function": "def function_name(params):",
                "return": "return value",
                "variable": "variable_name = value",
            },
            ("python", "english"): {
                "if": "conditional statement (if this, then that)",
                "for": "iteration over items",
                "while": "repeated action while condition is true",
                "def": "definition of a function",
                "return": "output value from a function",
                "class": "blueprint for creating objects",
            },
        }

        translation_key = (from_domain.lower(), to_domain.lower())
        domain_translations = translations.get(translation_key, {})

        # Look for exact match or partial match
        result = None
        concept_lower = concept.lower()

        if concept_lower in domain_translations:
            result = domain_translations[concept_lower]
        else:
            # Partial match
            for key, value in domain_translations.items():
                if key in concept_lower or concept_lower in key:
                    result = value
                    break

        if result:
            return {
                "success": True,
                "concept": concept,
                "from_domain": from_domain,
                "to_domain": to_domain,
                "translation": result,
                "message": f"Translated '{concept}' from {from_domain} to {to_domain}",
            }

        return {
            "success": False,
            "concept": concept,
            "from_domain": from_domain,
            "to_domain": to_domain,
            "message": f"No translation found for '{concept}' from {from_domain} to {to_domain}",
            "available_translations": list(domain_translations.keys()) if domain_translations else [],
        }

    def analyze_grammar(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Analyze grammar of the given text.

        Args:
            text: Text to analyze

        Returns:
            Grammar analysis
        """
        self._update_activity()

        sentences = text.split(".")
        sentences = [s.strip() for s in sentences if s.strip()]

        analysis = {
            "sentence_count": len(sentences),
            "word_count": len(text.split()),
            "sentences": [],
            "issues": [],
            "suggestions": [],
        }

        for sent in sentences:
            parsed = self.parse_sentence(sent + ".")  # Re-add period
            sentence_analysis = {
                "text": sent,
                "words": len(parsed.words),
                "structure": parsed.structure,
            }
            analysis["sentences"].append(sentence_analysis)

            # Check for common issues
            if len(parsed.words) < 3:
                analysis["issues"].append({
                    "sentence": sent,
                    "issue": "Sentence is too short",
                    "suggestion": "Consider adding more detail",
                })

            # Check for missing subject/verb (simple heuristic)
            has_verb = any(tag in ["verb", "verb_ed", "verb_ing"] for _, tag in parsed.pos_tags)
            if not has_verb:
                analysis["issues"].append({
                    "sentence": sent,
                    "issue": "No verb detected",
                    "suggestion": "Every sentence should have a verb",
                })

        return analysis

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        # Simple tokenization
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', '', text.lower())
        return text.split()

    def _simple_pos_tag(self, words: List[str]) -> List[Tuple[str, str]]:
        """Simple part-of-speech tagging."""
        tags = []

        for word in words:
            word_lower = word.lower()
            tag = "unknown"

            # Check patterns
            for pattern_name, pattern in self.POS_PATTERNS.items():
                if re.match(pattern, word_lower, re.IGNORECASE):
                    tag = pattern_name
                    break

            # Check word lists
            if tag == "unknown":
                if word_lower in self.ARTICLES:
                    tag = "article"
                elif word_lower in self.PREPOSITIONS:
                    tag = "preposition"
                elif word_lower in self.COMMON_NOUNS:
                    tag = "noun"
                elif word_lower in self.COMMON_VERBS:
                    tag = "verb"
                elif word_lower in self.COMMON_ADJECTIVES:
                    tag = "adjective"

            tags.append((word, tag))

        return tags

    def _extract_structure(
        self,
        words: List[str],
        pos_tags: List[Tuple[str, str]],
    ) -> Dict[str, Any]:
        """Extract sentence structure from POS tags."""
        structure = {
            "subject": None,
            "verb": None,
            "object": None,
            "modifiers": [],
        }

        # Simple heuristic: first noun phrase is subject, verb, rest is object
        found_verb = False
        subject_parts = []
        object_parts = []

        for word, tag in pos_tags:
            if tag == "verb" and not found_verb:
                structure["verb"] = word
                found_verb = True
            elif tag in ("article", "noun", "adjective"):
                if not found_verb:
                    subject_parts.append(word)
                else:
                    object_parts.append(word)
            elif tag in ("preposition", "adverb"):
                structure["modifiers"].append(word)

        if subject_parts:
            structure["subject"] = " ".join(subject_parts)
        if object_parts:
            structure["object"] = " ".join(object_parts)

        return structure

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            **super().get_capabilities(),
            "domain_specific": [
                "parse_sentence",
                "generate_sentence",
                "explain_concept",
                "translate_concept",
                "analyze_grammar",
            ],
            "language": self.language,
        }

    def get_parse(self, parse_id: str) -> Optional[ParsedSentence]:
        """Get a parsed sentence by ID."""
        return self._parsed_sentences.get(parse_id)

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept by ID."""
        return self._concepts.get(concept_id)

    def add_concept(
        self,
        name: str,
        category: str,
        definition: str,
        examples: Optional[List[str]] = None,
    ) -> Concept:
        """Add a new concept."""
        concept = Concept(
            concept_id=f"concept_{uuid.uuid4().hex[:8]}",
            name=name,
            category=category,
            definition=definition,
            examples=examples or [],
            related_concepts=[],
        )
        self._concepts[concept.concept_id] = concept
        return concept

    def __repr__(self) -> str:
        return f"LanguageAgent(id={self.agent_id}, language={self.language})"
