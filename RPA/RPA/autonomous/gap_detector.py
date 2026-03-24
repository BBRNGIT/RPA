"""
Gap Detector and Self-Improvement Module

Identifies knowledge gaps and prioritizes learning to achieve
balanced, comprehensive knowledge across all domains.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class KnowledgeGap:
    """A detected knowledge gap."""
    gap_id: str
    domain: str
    category: str
    description: str
    severity: str  # critical, high, medium, low
    priority: int  # 1-10, higher is more urgent
    suggested_curriculum: str
    detected_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "domain": self.domain,
            "category": self.category,
            "description": self.description,
            "severity": self.severity,
            "priority": self.priority,
            "suggested_curriculum": self.suggested_curriculum,
            "detected_at": self.detected_at
        }


@dataclass
class DomainBalance:
    """Balance metrics for a domain."""
    domain: str
    pattern_count: int
    target_ratio: float
    actual_ratio: float
    gap: float  # target - actual (positive means under-represented)
    priority: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "pattern_count": self.pattern_count,
            "target_ratio": self.target_ratio,
            "actual_ratio": self.actual_ratio,
            "gap": self.gap,
            "priority": self.priority
        }


class GapDetector:
    """
    Detects knowledge gaps and prioritizes learning.
    
    Analyzes:
    - Domain balance (is the AI learning all domains equally?)
    - Concept coverage (are all key concepts covered?)
    - Skill gaps (which skills are missing or weak?)
    - Confidence gaps (which areas have low test scores?)
    """
    
    # Target domain ratios (percentage of total knowledge)
    TARGET_DOMAIN_RATIOS = {
        "english": 0.25,      # 25% - language is foundational
        "python": 0.20,       # 20% - coding is important
        "reasoning": 0.15,    # 15% - cognitive skills
        "skills": 0.15,       # 15% - practical skills
        "finance": 0.10,      # 10% - domain knowledge
        "medicine": 0.10,     # 10% - domain knowledge
        "health": 0.05,       # 5% - wellness
    }
    
    # Core concepts that must be covered in each domain
    CORE_CONCEPTS = {
        "english": [
            "vocabulary", "grammar", "syntax", "semantics", "pragmatics",
            "parts_of_speech", "sentence_structure", "punctuation", "spelling"
        ],
        "python": [
            "variables", "functions", "classes", "loops", "conditionals",
            "data_structures", "error_handling", "modules", "testing", "decorators"
        ],
        "reasoning": [
            "intent_recognition", "context_awareness", "logical_inference",
            "analogical_reasoning", "causal_reasoning", "critical_thinking",
            "problem_decomposition", "pattern_recognition"
        ],
        "skills": [
            "fullstack_dev", "document_creation", "image_generation",
            "web_search", "content_writing", "data_analysis", "ui_design"
        ],
        "finance": [
            "roi", "npv", "irr", "financial_statements", "budgeting",
            "investing", "risk_management", "market_analysis"
        ],
        "medicine": [
            "anatomy", "physiology", "pathology", "pharmacology",
            "diagnosis", "treatment", "prevention"
        ],
        "health": [
            "nutrition", "exercise", "sleep", "mental_health",
            "prevention", "wellness", "lifestyle"
        ]
    }
    
    def __init__(self):
        self.gaps: List[KnowledgeGap] = []
        self.balance_metrics: List[DomainBalance] = []
        self.last_analysis: Optional[str] = None
    
    def analyze_domain_balance(self, domain_counts: Dict[str, int]) -> List[DomainBalance]:
        """Analyze the balance of knowledge across domains."""
        total = sum(domain_counts.values())
        if total == 0:
            total = 1  # Avoid division by zero
        
        metrics = []
        
        for domain, target_ratio in self.TARGET_DOMAIN_RATIOS.items():
            actual_count = domain_counts.get(domain, 0)
            actual_ratio = actual_count / total
            
            gap = target_ratio - actual_ratio
            
            # Calculate priority (larger gap = higher priority)
            priority = min(10, max(1, int(gap * 50) + 5))
            
            metrics.append(DomainBalance(
                domain=domain,
                pattern_count=actual_count,
                target_ratio=target_ratio,
                actual_ratio=actual_ratio,
                gap=gap,
                priority=priority if gap > 0 else 1  # Under-represented domains get higher priority
            ))
        
        self.balance_metrics = sorted(metrics, key=lambda x: x.gap, reverse=True)
        return self.balance_metrics
    
    def detect_concept_gaps(self, domain: str, known_concepts: List[str]) -> List[KnowledgeGap]:
        """Detect gaps in concept coverage for a domain."""
        gaps = []
        core_concepts = self.CORE_CONCEPTS.get(domain, [])
        
        for concept in core_concepts:
            if concept not in known_concepts and concept not in [c.lower() for c in known_concepts]:
                gap = KnowledgeGap(
                    gap_id=f"concept_{domain}_{concept}",
                    domain=domain,
                    category="concept_coverage",
                    description=f"Missing core concept: {concept} in domain {domain}",
                    severity="high",
                    priority=8,
                    suggested_curriculum=f"curriculum/{domain}/{concept}_basics.json",
                    detected_at=datetime.now().isoformat()
                )
                gaps.append(gap)
        
        return gaps
    
    def detect_confidence_gaps(self, test_scores: Dict[str, float]) -> List[KnowledgeGap]:
        """Detect gaps based on low test scores."""
        gaps = []
        
        for domain, score in test_scores.items():
            if score < 0.7:  # Less than 70% correct
                severity = "critical" if score < 0.5 else "high"
                priority = 10 if score < 0.5 else 8
                
                gap = KnowledgeGap(
                    gap_id=f"confidence_{domain}",
                    domain=domain,
                    category="confidence_gap",
                    description=f"Low test score ({score*100:.1f}%) in {domain}",
                    severity=severity,
                    priority=priority,
                    suggested_curriculum=f"curriculum/{domain}/remedial.json",
                    detected_at=datetime.now().isoformat()
                )
                gaps.append(gap)
        
        return gaps
    
    def detect_skill_gaps(self, available_skills: List[str], learned_skills: List[str]) -> List[KnowledgeGap]:
        """Detect gaps in skill coverage."""
        gaps = []
        
        for skill in available_skills:
            if skill not in learned_skills:
                gap = KnowledgeGap(
                    gap_id=f"skill_{skill}",
                    domain="skills",
                    category="skill_gap",
                    description=f"Skill not yet learned: {skill}",
                    severity="medium",
                    priority=6,
                    suggested_curriculum=f"curriculum/skills/{skill}_curriculum.json",
                    detected_at=datetime.now().isoformat()
                )
                gaps.append(gap)
        
        return gaps
    
    def analyze_all(
        self,
        domain_counts: Dict[str, int],
        known_concepts: Dict[str, List[str]],
        test_scores: Dict[str, float],
        available_skills: List[str],
        learned_skills: List[str]
    ) -> List[KnowledgeGap]:
        """Run all gap detection analyses."""
        all_gaps = []
        
        # Domain balance gaps
        balance = self.analyze_domain_balance(domain_counts)
        for metric in balance:
            if metric.gap > 0.02:  # More than 2% under-represented
                gap = KnowledgeGap(
                    gap_id=f"balance_{metric.domain}",
                    domain=metric.domain,
                    category="domain_balance",
                    description=f"Domain under-represented by {metric.gap*100:.1f}%",
                    severity="medium" if metric.gap < 0.1 else "high",
                    priority=metric.priority,
                    suggested_curriculum=f"curriculum/{metric.domain}/additional.json",
                    detected_at=datetime.now().isoformat()
                )
                all_gaps.append(gap)
        
        # Concept gaps
        for domain, concepts in known_concepts.items():
            concept_gaps = self.detect_concept_gaps(domain, concepts)
            all_gaps.extend(concept_gaps)
        
        # Confidence gaps
        confidence_gaps = self.detect_confidence_gaps(test_scores)
        all_gaps.extend(confidence_gaps)
        
        # Skill gaps
        skill_gaps = self.detect_skill_gaps(available_skills, learned_skills)
        all_gaps.extend(skill_gaps)
        
        # Sort by priority
        self.gaps = sorted(all_gaps, key=lambda x: x.priority, reverse=True)
        self.last_analysis = datetime.now().isoformat()
        
        return self.gaps
    
    def get_learning_priorities(self) -> List[Dict[str, Any]]:
        """Get prioritized learning recommendations."""
        return [
            {
                "priority": gap.priority,
                "domain": gap.domain,
                "action": f"Learn {gap.category}: {gap.description}",
                "curriculum": gap.suggested_curriculum
            }
            for gap in self.gaps[:10]  # Top 10 priorities
        ]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive gap analysis report."""
        return {
            "analysis_time": self.last_analysis,
            "total_gaps": len(self.gaps),
            "gaps_by_severity": {
                "critical": len([g for g in self.gaps if g.severity == "critical"]),
                "high": len([g for g in self.gaps if g.severity == "high"]),
                "medium": len([g for g in self.gaps if g.severity == "medium"]),
                "low": len([g for g in self.gaps if g.severity == "low"])
            },
            "gaps_by_domain": {
                domain: len([g for g in self.gaps if g.domain == domain])
                for domain in self.TARGET_DOMAIN_RATIOS.keys()
            },
            "domain_balance": [m.to_dict() for m in self.balance_metrics],
            "top_priorities": self.get_learning_priorities(),
            "all_gaps": [g.to_dict() for g in self.gaps]
        }


def main():
    """Test the gap detector."""
    print("="*60)
    print("GAP DETECTOR TEST")
    print("="*60)
    
    detector = GapDetector()
    
    # Sample data
    domain_counts = {
        "english": 5272,
        "python": 530,
        "finance": 200,
        "medicine": 200,
        "health": 200,
        "reasoning": 10,
        "skills": 0
    }
    
    known_concepts = {
        "english": ["vocabulary", "grammar"],
        "python": ["variables", "functions", "loops"],
        "reasoning": ["intent_recognition"]
    }
    
    test_scores = {
        "english": 0.87,
        "python": 0.82,
        "finance": 0.78,
        "medicine": 0.75,
        "health": 0.85,
        "reasoning": 0.65
    }
    
    available_skills = ["fullstack-dev", "docx", "pdf", "pptx", "image-generation"]
    learned_skills = []
    
    gaps = detector.analyze_all(
        domain_counts,
        known_concepts,
        test_scores,
        available_skills,
        learned_skills
    )
    
    print(f"\nDetected {len(gaps)} gaps")
    
    report = detector.generate_report()
    
    print("\nDomain Balance:")
    for metric in report["domain_balance"]:
        status = "UNDER" if metric["gap"] > 0 else "OVER"
        print(f"  {metric['domain']:12} {metric['pattern_count']:5} patterns | "
              f"{metric['actual_ratio']*100:5.1f}% actual vs {metric['target_ratio']*100:5.1f}% target | "
              f"{status}")
    
    print("\nTop 5 Learning Priorities:")
    for i, priority in enumerate(report["top_priorities"][:5], 1):
        print(f"  {i}. [{priority['priority']}] {priority['domain']}: {priority['action']}")
    
    print("\nGaps by Severity:")
    for severity, count in report["gaps_by_severity"].items():
        print(f"  {severity}: {count}")


if __name__ == "__main__":
    main()
