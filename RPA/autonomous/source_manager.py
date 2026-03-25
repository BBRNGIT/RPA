"""
Source Manager for Curriculum Generation

Manages verified external sources for curriculum generation:
- HuggingFace datasets
- Wikipedia articles
- Other educational resources

Generates curriculum from these sources when internal curriculum is exhausted.
"""

import json
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error


@dataclass
class ExternalSource:
    """A verified external source for curriculum."""
    source_id: str
    name: str
    source_type: str  # huggingface, wikipedia, custom
    url: str
    domain: str
    description: str
    last_fetched: Optional[str] = None
    items_fetched: int = 0
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "source_type": self.source_type,
            "url": self.url,
            "domain": self.domain,
            "description": self.description,
            "last_fetched": self.last_fetched,
            "items_fetched": self.items_fetched,
            "is_active": self.is_active
        }


@dataclass
class CurriculumBatch:
    """A batch of curriculum generated from external sources."""
    batch_id: str
    source: str
    domain: str
    items: List[Dict[str, Any]]
    generated_at: str
    item_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source": self.source,
            "domain": self.domain,
            "items": self.items,
            "generated_at": self.generated_at,
            "item_count": self.item_count
        }


class SourceManager:
    """
    Manages external sources for curriculum generation.
    
    Provides:
    - Registry of verified sources
    - Curriculum generation from sources
    - Caching and rate limiting
    - Quality filtering
    """
    
    OUTPUT_PATH = Path("/home/z/my-project/RPA/RPA/curriculum/generated")
    
    # Verified sources registry
    VERIFIED_SOURCES = {
        # English language sources
        "english_words": ExternalSource(
            source_id="english_words",
            name="Common English Words",
            source_type="builtin",
            url="internal://vocabulary",
            domain="english",
            description="Common English vocabulary with definitions"
        ),
        "english_idioms": ExternalSource(
            source_id="english_idioms",
            name="English Idioms",
            source_type="builtin",
            url="internal://idioms",
            domain="english",
            description="Common English idioms and expressions"
        ),
        
        # Python sources
        "python_patterns": ExternalSource(
            source_id="python_patterns",
            name="Python Design Patterns",
            source_type="builtin",
            url="internal://patterns",
            domain="python",
            description="Common Python design patterns and best practices"
        ),
        "python_snippets": ExternalSource(
            source_id="python_snippets",
            name="Python Code Snippets",
            source_type="builtin",
            url="internal://snippets",
            domain="python",
            description="Useful Python code snippets"
        ),
        
        # Reasoning sources
        "reasoning_patterns": ExternalSource(
            source_id="reasoning_patterns",
            name="Reasoning Patterns",
            source_type="builtin",
            url="internal://reasoning",
            domain="reasoning",
            description="Cognitive reasoning patterns and heuristics"
        ),
        
        # Finance sources
        "finance_concepts": ExternalSource(
            source_id="finance_concepts",
            name="Financial Concepts",
            source_type="builtin",
            url="internal://finance",
            domain="finance",
            description="Core financial concepts and formulas"
        ),
        
        # Medicine sources
        "medicine_basics": ExternalSource(
            source_id="medicine_basics",
            name="Medical Fundamentals",
            source_type="builtin",
            url="internal://medicine",
            domain="medicine",
            description="Basic medical knowledge and terminology"
        ),
        
        # Health sources
        "health_wellness": ExternalSource(
            source_id="health_wellness",
            name="Health and Wellness",
            source_type="builtin",
            url="internal://health",
            domain="health",
            description="Health and wellness guidelines"
        ),
        
        # Skills sources
        "skills_registry": ExternalSource(
            source_id="skills_registry",
            name="Skills Registry",
            source_type="builtin",
            url="internal://skills",
            domain="skills",
            description="Available skills and their applications"
        )
    }
    
    # Built-in knowledge bases
    KNOWLEDGE_BASES = {
        "english": {
            "words": [
                {"word": "accomplish", "definition": "to achieve or complete successfully", "type": "verb", "examples": ["She accomplished her goals."]},
                {"word": "acquire", "definition": "to gain possession of something", "type": "verb", "examples": ["He acquired new skills."]},
                {"word": "adequate", "definition": "satisfactory or acceptable in quality", "type": "adjective", "examples": ["The solution was adequate."]},
                {"word": "analyze", "definition": "to examine methodically and in detail", "type": "verb", "examples": ["Let's analyze the data."]},
                {"word": "approach", "definition": "a way of dealing with a situation", "type": "noun", "examples": ["A new approach was needed."]},
                {"word": "assess", "definition": "to evaluate or estimate the nature of", "type": "verb", "examples": ["We need to assess the risks."]},
                {"word": "assume", "definition": "to suppose to be the case without proof", "type": "verb", "examples": ["I assume you're ready."]},
                {"word": "available", "definition": "able to be used or obtained", "type": "adjective", "examples": ["The resources are available."]},
                {"word": "benefit", "definition": "an advantage or profit", "type": "noun", "examples": ["There are many benefits."]},
                {"word": "concept", "definition": "an abstract idea or general notion", "type": "noun", "examples": ["The concept is simple."]},
            ],
            "idioms": [
                {"idiom": "break the ice", "meaning": "to initiate conversation in a social setting", "usage": "Used when starting a conversation with strangers"},
                {"idiom": "hit the nail on the head", "meaning": "to describe exactly what is causing a situation", "usage": "Used when someone is exactly right"},
                {"idiom": "piece of cake", "meaning": "something very easy to do", "usage": "Used to describe an easy task"},
                {"idiom": "under the weather", "meaning": "feeling slightly ill", "usage": "Used when not feeling well"},
                {"idiom": "once in a blue moon", "meaning": "very rarely", "usage": "Used to describe rare events"},
            ],
            "grammar_rules": [
                {"rule": "subject_verb_agreement", "description": "Subjects and verbs must agree in number", "examples": ["She runs. They run."]},
                {"rule": "tense_consistency", "description": "Maintain consistent tense within sentences", "examples": ["She walked to the store and bought milk."]},
                {"rule": "pronoun_antecedent", "description": "Pronouns must agree with their antecedents", "examples": ["Each student has their own book."]},
            ]
        },
        "python": {
            "patterns": [
                {"name": "singleton", "description": "Ensure a class has only one instance", "code": "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance"},
                {"name": "factory", "description": "Create objects without specifying exact class", "code": "def factory(type):\n    if type == 'A': return ClassA()\n    elif type == 'B': return ClassB()"},
                {"name": "observer", "description": "Define a subscription mechanism", "code": "class Observable:\n    def __init__(self):\n        self._observers = []\n    def notify(self, event):\n        for obs in self._observers:\n            obs.update(event)"},
            ],
            "best_practices": [
                {"practice": "use_context_managers", "description": "Use 'with' statement for resource management", "example": "with open('file.txt') as f:\n    content = f.read()"},
                {"practice": "prefer_comprehensions", "description": "Use list/dict comprehensions for clarity", "example": "[x*2 for x in range(10)]"},
                {"practice": "use_type_hints", "description": "Add type hints for better code clarity", "example": "def greet(name: str) -> str:\n    return f'Hello, {name}'"},
            ]
        },
        "reasoning": {
            "patterns": [
                {"name": "deductive", "description": "Apply general rules to specific cases", "example": "All men are mortal. Socrates is a man. Therefore, Socrates is mortal."},
                {"name": "inductive", "description": "Derive general rules from specific cases", "example": "The sun has risen every morning. Therefore, the sun will rise tomorrow."},
                {"name": "abductive", "description": "Find the best explanation", "example": "The grass is wet. It probably rained."},
            ],
            "heuristics": [
                {"name": "occams_razor", "description": "The simplest explanation is usually correct"},
                {"name": "representativeness", "description": "Judge probability by similarity to prototype"},
                {"name": "availability", "description": "Judge probability by ease of recall"},
            ]
        },
        "finance": {
            "concepts": [
                {"name": "compound_interest", "formula": "A = P(1 + r/n)^(nt)", "description": "Interest calculated on initial principal and accumulated interest"},
                {"name": "present_value", "formula": "PV = FV / (1 + r)^n", "description": "Current value of a future sum of money"},
                {"name": "net_present_value", "formula": "NPV = sum(CF_t / (1+r)^t)", "description": "Sum of discounted cash flows"},
            ],
            "ratios": [
                {"name": "debt_to_equity", "formula": "Total Debt / Shareholders' Equity", "description": "Measure of financial leverage"},
                {"name": "current_ratio", "formula": "Current Assets / Current Liabilities", "description": "Measure of short-term liquidity"},
                {"name": "return_on_equity", "formula": "Net Income / Shareholders' Equity", "description": "Measure of profitability"},
            ]
        },
        "medicine": {
            "terminology": [
                {"term": "etiology", "definition": "The cause or origin of a disease"},
                {"term": "prognosis", "definition": "The likely course of a disease"},
                {"term": "symptom", "definition": "A physical or mental feature indicating a condition"},
                {"term": "diagnosis", "definition": "The identification of a disease by examination"},
                {"term": "treatment", "definition": "Medical care given to a patient"},
            ],
            "systems": [
                {"system": "cardiovascular", "organs": ["heart", "blood vessels"], "function": "Circulates blood throughout the body"},
                {"system": "respiratory", "organs": ["lungs", "trachea"], "function": "Facilitates gas exchange"},
                {"system": "nervous", "organs": ["brain", "spinal cord", "nerves"], "function": "Controls body functions"},
            ]
        },
        "health": {
            "guidelines": [
                {"topic": "sleep", "recommendation": "7-9 hours for adults", "importance": "Critical for recovery and cognitive function"},
                {"topic": "exercise", "recommendation": "150 minutes moderate or 75 minutes vigorous per week", "importance": "Essential for cardiovascular health"},
                {"topic": "hydration", "recommendation": "8 glasses of water daily", "importance": "Necessary for all bodily functions"},
            ],
            "nutrition": [
                {"nutrient": "protein", "recommendation": "0.8g per kg body weight", "function": "Building blocks for tissues"},
                {"nutrient": "carbohydrates", "recommendation": "45-65% of calories", "function": "Primary energy source"},
                {"nutrient": "fats", "recommendation": "20-35% of calories", "function": "Energy storage and cell function"},
            ]
        },
        "skills": {
            "applications": [
                {"skill": "fullstack-dev", "when_to_use": "Building web applications, APIs, databases", "keywords": ["website", "web app", "database", "API"]},
                {"skill": "docx", "when_to_use": "Creating Word documents", "keywords": ["document", "word", "report", "letter"]},
                {"skill": "pdf", "when_to_use": "Working with PDF files", "keywords": ["PDF", "form", "extract"]},
                {"skill": "pptx", "when_to_use": "Creating presentations", "keywords": ["presentation", "slides", "powerpoint"]},
                {"skill": "image-generation", "when_to_use": "Creating images from descriptions", "keywords": ["image", "picture", "generate", "create visual"]},
            ]
        }
    }
    
    def __init__(self):
        self.sources = self.VERIFIED_SOURCES.copy()
        self.fetch_history: List[Dict[str, Any]] = []
    
    def get_source(self, source_id: str) -> Optional[ExternalSource]:
        """Get a source by ID."""
        return self.sources.get(source_id)
    
    def list_sources(self, domain: Optional[str] = None) -> List[ExternalSource]:
        """List all available sources, optionally filtered by domain."""
        sources = list(self.sources.values())
        if domain:
            sources = [s for s in sources if s.domain == domain]
        return sources
    
    def generate_curriculum(
        self,
        source_id: str,
        count: int = 10,
        difficulty: str = "beginner"
    ) -> CurriculumBatch:
        """Generate curriculum items from a source."""
        source = self.get_source(source_id)
        if not source:
            raise ValueError(f"Source not found: {source_id}")
        
        # Get knowledge base
        domain = source.domain
        knowledge = self.KNOWLEDGE_BASES.get(domain, {})
        
        items = []
        
        if domain == "english":
            items = self._generate_english_items(knowledge, count, difficulty)
        elif domain == "python":
            items = self._generate_python_items(knowledge, count, difficulty)
        elif domain == "reasoning":
            items = self._generate_reasoning_items(knowledge, count, difficulty)
        elif domain == "finance":
            items = self._generate_finance_items(knowledge, count, difficulty)
        elif domain == "medicine":
            items = self._generate_medicine_items(knowledge, count, difficulty)
        elif domain == "health":
            items = self._generate_health_items(knowledge, count, difficulty)
        elif domain == "skills":
            items = self._generate_skills_items(knowledge, count, difficulty)
        
        # Update source stats
        source.last_fetched = datetime.now().isoformat()
        source.items_fetched += len(items)
        
        # Record fetch
        self.fetch_history.append({
            "source_id": source_id,
            "timestamp": datetime.now().isoformat(),
            "items_generated": len(items)
        })
        
        return CurriculumBatch(
            batch_id=f"batch_{source_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            source=source_id,
            domain=domain,
            items=items,
            generated_at=datetime.now().isoformat(),
            item_count=len(items)
        )
    
    def _generate_english_items(self, knowledge: Dict, count: int, difficulty: str) -> List[Dict]:
        """Generate English curriculum items."""
        items = []
        words = knowledge.get("words", [])
        idioms = knowledge.get("idioms", [])
        grammar = knowledge.get("grammar_rules", [])
        
        for i in range(count):
            item_type = random.choice(["vocabulary", "idiom", "grammar"])
            
            if item_type == "vocabulary" and words:
                word_data = random.choice(words)
                items.append({
                    "domain": "english",
                    "category": "vocabulary",
                    "concept": word_data["word"],
                    "definition": word_data["definition"],
                    "word_type": word_data["type"],
                    "examples": word_data.get("examples", []),
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Use '{word_data['word']}' in a sentence",
                        f"Find synonyms for '{word_data['word']}'",
                        f"Explain the meaning of '{word_data['word']}'"
                    ]
                })
            elif item_type == "idiom" and idioms:
                idiom_data = random.choice(idioms)
                items.append({
                    "domain": "english",
                    "category": "idiom",
                    "concept": idiom_data["idiom"],
                    "meaning": idiom_data["meaning"],
                    "usage": idiom_data["usage"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Use '{idiom_data['idiom']}' in context",
                        f"Explain when to use '{idiom_data['idiom']}'"
                    ]
                })
            elif grammar:
                rule_data = random.choice(grammar)
                items.append({
                    "domain": "english",
                    "category": "grammar",
                    "concept": rule_data["rule"],
                    "description": rule_data["description"],
                    "examples": rule_data.get("examples", []),
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Apply the '{rule_data['rule']}' rule in writing"
                    ]
                })
        
        return items
    
    def _generate_python_items(self, knowledge: Dict, count: int, difficulty: str) -> List[Dict]:
        """Generate Python curriculum items."""
        items = []
        patterns = knowledge.get("patterns", [])
        practices = knowledge.get("best_practices", [])
        
        for i in range(count):
            if i % 2 == 0 and patterns:
                pattern = random.choice(patterns)
                items.append({
                    "domain": "python",
                    "category": "design_pattern",
                    "concept": pattern["name"],
                    "description": pattern["description"],
                    "code": pattern["code"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Implement the {pattern['name']} pattern",
                        f"Identify when to use {pattern['name']}"
                    ]
                })
            elif practices:
                practice = random.choice(practices)
                items.append({
                    "domain": "python",
                    "category": "best_practice",
                    "concept": practice["practice"],
                    "description": practice["description"],
                    "example": practice["example"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Apply '{practice['practice']}' in code"
                    ]
                })
        
        return items
    
    def _generate_reasoning_items(self, knowledge: Dict, count: int, difficulty: str) -> List[Dict]:
        """Generate reasoning curriculum items."""
        items = []
        patterns = knowledge.get("patterns", [])
        heuristics = knowledge.get("heuristics", [])
        
        for i in range(count):
            if i % 2 == 0 and patterns:
                pattern = random.choice(patterns)
                items.append({
                    "domain": "reasoning",
                    "category": "reasoning_pattern",
                    "concept": pattern["name"],
                    "description": pattern["description"],
                    "example": pattern["example"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Apply {pattern['name']} reasoning to a problem"
                    ]
                })
            elif heuristics:
                heuristic = random.choice(heuristics)
                items.append({
                    "domain": "reasoning",
                    "category": "heuristic",
                    "concept": heuristic["name"],
                    "description": heuristic["description"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Use {heuristic['name']} in decision-making"
                    ]
                })
        
        return items
    
    def _generate_finance_items(self, knowledge: Dict, count: int, difficulty: str) -> List[Dict]:
        """Generate finance curriculum items."""
        items = []
        concepts = knowledge.get("concepts", [])
        ratios = knowledge.get("ratios", [])
        
        for i in range(count):
            if i % 2 == 0 and concepts:
                concept = random.choice(concepts)
                items.append({
                    "domain": "finance",
                    "category": "financial_concept",
                    "concept": concept["name"],
                    "formula": concept["formula"],
                    "description": concept["description"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Calculate {concept['name']} for a given scenario"
                    ]
                })
            elif ratios:
                ratio = random.choice(ratios)
                items.append({
                    "domain": "finance",
                    "category": "financial_ratio",
                    "concept": ratio["name"],
                    "formula": ratio["formula"],
                    "description": ratio["description"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Calculate {ratio['name']} from financial statements"
                    ]
                })
        
        return items
    
    def _generate_medicine_items(self, knowledge: Dict, count: int, difficulty: str) -> List[Dict]:
        """Generate medicine curriculum items."""
        items = []
        terminology = knowledge.get("terminology", [])
        systems = knowledge.get("systems", [])
        
        for i in range(count):
            if i % 2 == 0 and terminology:
                term = random.choice(terminology)
                items.append({
                    "domain": "medicine",
                    "category": "terminology",
                    "concept": term["term"],
                    "definition": term["definition"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Use '{term['term']}' correctly in context"
                    ]
                })
            elif systems:
                system = random.choice(systems)
                items.append({
                    "domain": "medicine",
                    "category": "body_system",
                    "concept": system["system"],
                    "organs": system["organs"],
                    "function": system["function"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Explain the {system['system']} system"
                    ]
                })
        
        return items
    
    def _generate_health_items(self, knowledge: Dict, count: int, difficulty: str) -> List[Dict]:
        """Generate health curriculum items."""
        items = []
        guidelines = knowledge.get("guidelines", [])
        nutrition = knowledge.get("nutrition", [])
        
        for i in range(count):
            if i % 2 == 0 and guidelines:
                guideline = random.choice(guidelines)
                items.append({
                    "domain": "health",
                    "category": "health_guideline",
                    "concept": guideline["topic"],
                    "recommendation": guideline["recommendation"],
                    "importance": guideline["importance"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Apply {guideline['topic']} recommendations"
                    ]
                })
            elif nutrition:
                nutrient = random.choice(nutrition)
                items.append({
                    "domain": "health",
                    "category": "nutrition",
                    "concept": nutrient["nutrient"],
                    "recommendation": nutrient["recommendation"],
                    "function": nutrient["function"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Identify foods rich in {nutrient['nutrient']}"
                    ]
                })
        
        return items
    
    def _generate_skills_items(self, knowledge: Dict, count: int, difficulty: str) -> List[Dict]:
        """Generate skills curriculum items."""
        items = []
        applications = knowledge.get("applications", [])
        
        for i in range(count):
            if applications:
                skill = random.choice(applications)
                items.append({
                    "domain": "skills",
                    "category": "skill_application",
                    "concept": skill["skill"],
                    "when_to_use": skill["when_to_use"],
                    "keywords": skill["keywords"],
                    "difficulty": difficulty,
                    "practice_tasks": [
                        f"Identify scenarios requiring {skill['skill']}",
                        f"Explain when to use {skill['skill']}"
                    ]
                })
        
        return items
    
    def save_curriculum_batch(self, batch: CurriculumBatch) -> str:
        """Save a curriculum batch to file."""
        self.OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
        
        filename = f"{batch.batch_id}.json"
        filepath = self.OUTPUT_PATH / filename
        
        with open(filepath, 'w') as f:
            json.dump(batch.to_dict(), f, indent=2)
        
        return str(filepath)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get source manager statistics."""
        return {
            "total_sources": len(self.sources),
            "sources_by_domain": {
                domain: len([s for s in self.sources.values() if s.domain == domain])
                for domain in set(s.domain for s in self.sources.values())
            },
            "total_fetches": len(self.fetch_history),
            "total_items_generated": sum(f["items_generated"] for f in self.fetch_history)
        }


def main():
    """Test the source manager."""
    print("="*60)
    print("SOURCE MANAGER TEST")
    print("="*60)
    
    manager = SourceManager()
    
    # List sources
    print("\nAvailable Sources:")
    for source in manager.list_sources():
        print(f"  - {source.source_id}: {source.name} ({source.domain})")
    
    # Generate curriculum from each source
    print("\n" + "="*60)
    print("GENERATING CURRICULUM")
    print("="*60)
    
    for source_id in ["english_words", "python_patterns", "reasoning_patterns"]:
        print(f"\n{source_id}:")
        batch = manager.generate_curriculum(source_id, count=3)
        print(f"  Generated {batch.item_count} items")
        for item in batch.items[:2]:
            print(f"    - {item['concept']}: {item.get('definition', item.get('description', 'N/A'))[:50]}...")
    
    # Stats
    stats = manager.get_stats()
    print(f"\nStats: {stats}")


if __name__ == "__main__":
    main()
