"""
Skill-to-Curriculum Converter

Converts skills from the skills folder into learnable curriculum format
for the RPA AI to learn through the curriculum-based training system.

This enables the AI to acquire skills through LEARNING, not hardcoding.
"""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib


@dataclass
class CurriculumItem:
    """A single learnable curriculum item."""
    item_id: str
    skill_name: str
    category: str
    concept: str
    instruction: str
    examples: List[str]
    practice_tasks: List[str]
    difficulty: str  # novice, beginner, intermediate, advanced, expert
    prerequisites: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "skill_name": self.skill_name,
            "category": self.category,
            "concept": self.concept,
            "instruction": self.instruction,
            "examples": self.examples,
            "practice_tasks": self.practice_tasks,
            "difficulty": self.difficulty,
            "prerequisites": self.prerequisites,
            "metadata": self.metadata
        }


@dataclass
class SkillCurriculum:
    """Complete curriculum generated from a skill."""
    skill_name: str
    skill_description: str
    items: List[CurriculumItem]
    total_items: int
    generated_at: str
    source_path: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "skill_description": self.skill_description,
            "items": [item.to_dict() for item in self.items],
            "total_items": self.total_items,
            "generated_at": self.generated_at,
            "source_path": self.source_path
        }


class SkillCurriculumConverter:
    """
    Converts skills from SKILL.md files into learnable curriculum format.
    
    The converter:
    1. Reads all SKILL.md files from the skills folder
    2. Parses skill structure, concepts, and instructions
    3. Generates curriculum items with concepts, examples, and practice tasks
    4. Creates project-based assessments for each skill
    """
    
    SKILLS_PATH = "/home/z/my-project/RPA_GITHUB/skills"
    OUTPUT_PATH = "/home/z/my-project/RPA/RPA/curriculum/skills"
    
    # Difficulty mapping based on skill complexity
    DIFFICULTY_KEYWORDS = {
        "novice": ["basic", "beginner", "intro", "getting started", "simple"],
        "beginner": ["fundamental", "foundation", "learn", "quick"],
        "intermediate": ["intermediate", "standard", "common", "typical"],
        "advanced": ["advanced", "complex", "expert", "sophisticated", "optimize"],
        "expert": ["expert", "master", "architect", "enterprise", "production"]
    }
    
    def __init__(self):
        self.skills: List[Dict[str, Any]] = []
        self.curricula: List[SkillCurriculum] = []
        self.stats = {
            "skills_processed": 0,
            "curriculum_items_generated": 0,
            "errors": []
        }
    
    def discover_skills(self) -> List[Dict[str, Any]]:
        """Discover all skills in the skills folder."""
        skills = []
        skills_path = Path(self.SKILLS_PATH)
        
        if not skills_path.exists():
            print(f"Skills path not found: {skills_path}")
            return skills
        
        for skill_dir in skills_path.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            
            try:
                skill_data = self._parse_skill_file(skill_md, skill_dir)
                skills.append(skill_data)
            except Exception as e:
                self.stats["errors"].append(f"Error parsing {skill_dir.name}: {str(e)}")
        
        self.skills = skills
        return skills
    
    def _parse_skill_file(self, skill_path: Path, skill_dir: Path) -> Dict[str, Any]:
        """Parse a SKILL.md file and extract skill information."""
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse frontmatter (YAML between ---)
        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                fm_text = parts[1].strip()
                for line in fm_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip().strip('"\'')
        
        # Extract sections
        sections = self._extract_sections(content)
        
        # Find all code examples
        code_examples = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)
        
        # Find all bullet points (instructions)
        instructions = re.findall(r'^\s*[-*]\s+(.+)$', content, re.MULTILINE)
        
        # Get auxiliary files
        aux_files = list(skill_dir.rglob("*.md")) + list(skill_dir.rglob("*.py")) + list(skill_dir.rglob("*.ts"))
        aux_content = {}
        for af in aux_files[:5]:  # Limit to first 5 auxiliary files
            if af.name != "SKILL.md":
                try:
                    with open(af, 'r', encoding='utf-8') as f:
                        aux_content[str(af.relative_to(skill_dir))] = f.read()[:2000]  # Limit content
                except:
                    pass
        
        return {
            "name": frontmatter.get("name", skill_dir.name),
            "description": frontmatter.get("description", ""),
            "path": str(skill_path),
            "dir": str(skill_dir),
            "frontmatter": frontmatter,
            "sections": sections,
            "code_examples": code_examples,
            "instructions": instructions,
            "auxiliary_content": aux_content
        }
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract markdown sections by headers."""
        sections = {}
        current_header = "intro"
        current_content = []
        
        for line in content.split('\n'):
            header_match = re.match(r'^#+\s+(.+)$', line)
            if header_match:
                if current_content:
                    sections[current_header] = '\n'.join(current_content).strip()
                current_header = header_match.group(1).lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_header] = '\n'.join(current_content).strip()
        
        return sections
    
    def convert_skill_to_curriculum(self, skill: Dict[str, Any]) -> SkillCurriculum:
        """Convert a single skill to curriculum format."""
        items = []
        skill_name = skill["name"]
        
        # 1. Create concept items from sections
        for section_name, section_content in skill["sections"].items():
            if section_name == "intro":
                continue
            
            item = self._create_curriculum_item(
                skill_name=skill_name,
                category="concept",
                concept=f"Understanding {section_name.replace('_', ' ')}",
                instruction=section_content[:500],  # Truncate long content
                examples=skill["code_examples"][:3] if skill["code_examples"] else [],
                difficulty=self._determine_difficulty(section_content)
            )
            items.append(item)
        
        # 2. Create instruction items from bullet points
        for i, instruction in enumerate(skill["instructions"][:10]):
            item = self._create_curriculum_item(
                skill_name=skill_name,
                category="instruction",
                concept=f"Rule or guideline: {instruction[:50]}...",
                instruction=instruction,
                examples=[],
                difficulty="beginner"
            )
            items.append(item)
        
        # 3. Create code pattern items
        for i, code_example in enumerate(skill["code_examples"][:5]):
            item = self._create_curriculum_item(
                skill_name=skill_name,
                category="code_pattern",
                concept=f"Code pattern {i+1}",
                instruction=f"Learn and apply this code pattern from {skill_name}",
                examples=[code_example],
                practice_tasks=[
                    f"Write similar code using the pattern from the example",
                    f"Identify when to use this pattern",
                    f"Modify the pattern for a different use case"
                ],
                difficulty=self._determine_difficulty(code_example)
            )
            items.append(item)
        
        # 4. Create project-based assessment item
        assessment_item = self._create_curriculum_item(
            skill_name=skill_name,
            category="assessment",
            concept=f"Apply {skill_name} in a practical project",
            instruction=f"Demonstrate mastery of {skill_name} by completing a project",
            examples=[],
            practice_tasks=self._generate_practice_tasks(skill),
            difficulty="intermediate"
        )
        items.append(assessment_item)
        
        # 5. Create contextualization item (how this skill relates to others)
        context_item = self._create_curriculum_item(
            skill_name=skill_name,
            category="contextualization",
            concept=f"When to use {skill_name}",
            instruction=f"Learn when to apply {skill_name} in response to user queries",
            examples=[
                f"User asks about web development -> consider using {skill_name}",
                f"User needs help with coding -> evaluate if {skill_name} applies"
            ],
            practice_tasks=[
                f"Identify keywords that indicate {skill_name} is needed",
                f"Distinguish between {skill_name} and related skills"
            ],
            difficulty="intermediate"
        )
        items.append(context_item)
        
        return SkillCurriculum(
            skill_name=skill_name,
            skill_description=skill["description"],
            items=items,
            total_items=len(items),
            generated_at=datetime.now().isoformat(),
            source_path=skill["path"]
        )
    
    def _create_curriculum_item(
        self,
        skill_name: str,
        category: str,
        concept: str,
        instruction: str,
        examples: List[str],
        difficulty: str,
        practice_tasks: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None
    ) -> CurriculumItem:
        """Create a curriculum item with a unique ID."""
        content_hash = hashlib.md5(f"{skill_name}{category}{concept}".encode()).hexdigest()[:8]
        item_id = f"skill_{skill_name.lower().replace('-', '_')}_{category}_{content_hash}"
        
        return CurriculumItem(
            item_id=item_id,
            skill_name=skill_name,
            category=category,
            concept=concept,
            instruction=instruction,
            examples=examples,
            practice_tasks=practice_tasks or [],
            difficulty=difficulty,
            prerequisites=prerequisites or []
        )
    
    def _determine_difficulty(self, content: str) -> str:
        """Determine difficulty level based on content analysis."""
        content_lower = content.lower()
        
        for difficulty, keywords in self.DIFFICULTY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return difficulty
        
        # Default based on content length
        if len(content) < 200:
            return "novice"
        elif len(content) < 500:
            return "beginner"
        elif len(content) < 1000:
            return "intermediate"
        else:
            return "advanced"
    
    def _generate_practice_tasks(self, skill: Dict[str, Any]) -> List[str]:
        """Generate practical project-based tasks for a skill."""
        skill_name = skill["name"]
        description = skill["description"]
        
        tasks = [
            f"Complete a mini-project using {skill_name}",
            f"Explain when {skill_name} should be used",
            f"Identify the core concepts of {skill_name}",
            f"Apply {skill_name} to solve a real-world problem"
        ]
        
        # Add domain-specific tasks based on skill name
        if "web" in skill_name.lower() or "fullstack" in skill_name.lower():
            tasks.extend([
                "Build a simple web interface",
                "Connect frontend to backend",
                "Implement user authentication"
            ])
        elif "code" in skill_name.lower():
            tasks.extend([
                "Write clean, documented code",
                "Debug a given code snippet",
                "Refactor code for better readability"
            ])
        elif "doc" in skill_name.lower() or "pdf" in skill_name.lower():
            tasks.extend([
                "Create a document with proper formatting",
                "Extract content from a document",
                "Generate a report from data"
            ])
        elif "image" in skill_name.lower():
            tasks.extend([
                "Generate an image from a description",
                "Edit an existing image",
                "Analyze image content"
            ])
        
        return tasks
    
    def convert_all_skills(self) -> List[SkillCurriculum]:
        """Convert all discovered skills to curriculum."""
        if not self.skills:
            self.discover_skills()
        
        curricula = []
        for skill in self.skills:
            try:
                curriculum = self.convert_skill_to_curriculum(skill)
                curricula.append(curriculum)
                self.stats["skills_processed"] += 1
                self.stats["curriculum_items_generated"] += curriculum.total_items
            except Exception as e:
                self.stats["errors"].append(f"Error converting {skill['name']}: {str(e)}")
        
        self.curricula = curricula
        return curricula
    
    def save_curriculum(self, curriculum: SkillCurriculum) -> str:
        """Save a curriculum to a JSON file."""
        output_path = Path(self.OUTPUT_PATH)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{curriculum.skill_name.lower().replace('-', '_')}_curriculum.json"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(curriculum.to_dict(), f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def save_all_curricula(self) -> List[str]:
        """Save all curricula to JSON files."""
        saved_paths = []
        for curriculum in self.curricula:
            path = self.save_curriculum(curriculum)
            saved_paths.append(path)
        return saved_paths
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of the conversion process."""
        return {
            "total_skills_found": len(self.skills),
            "skills_processed": self.stats["skills_processed"],
            "total_curriculum_items": self.stats["curriculum_items_generated"],
            "curricula_created": len(self.curricula),
            "errors": self.stats["errors"],
            "skill_names": [s["name"] for s in self.skills],
            "generated_at": datetime.now().isoformat()
        }


def main():
    """Run the skill-to-curriculum converter."""
    print("=" * 60)
    print("SKILL-TO-CURRICULUM CONVERTER")
    print("=" * 60)
    
    converter = SkillCurriculumConverter()
    
    # Discover skills
    print("\n[1/3] Discovering skills...")
    skills = converter.discover_skills()
    print(f"Found {len(skills)} skills")
    
    # Convert to curriculum
    print("\n[2/3] Converting skills to curriculum...")
    curricula = converter.convert_all_skills()
    print(f"Generated {len(curricula)} curricula with {converter.stats['curriculum_items_generated']} items")
    
    # Save curricula
    print("\n[3/3] Saving curricula...")
    saved_paths = converter.save_all_curricula()
    print(f"Saved {len(saved_paths)} curriculum files")
    
    # Print summary
    summary = converter.generate_summary()
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Skills found: {summary['total_skills_found']}")
    print(f"Skills processed: {summary['skills_processed']}")
    print(f"Curriculum items: {summary['total_curriculum_items']}")
    
    if summary['errors']:
        print(f"\nErrors: {len(summary['errors'])}")
        for err in summary['errors'][:5]:
            print(f"  - {err}")
    
    print("\nSkill names:")
    for name in summary['skill_names']:
        print(f"  - {name}")
    
    return summary


if __name__ == "__main__":
    main()
