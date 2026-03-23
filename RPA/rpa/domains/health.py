"""
Health and Wellness Domain Learning Module for RPA.

This module provides comprehensive health and wellness knowledge:
- Nutrition fundamentals and dietary guidelines
- Exercise science and fitness principles
- Mental health basics and stress management
- Preventive care and wellness strategies
- Cross-domain integration with medicine
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
import json
import math
import random
import re
import uuid
import logging

from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.core.graph import Node, NodeType

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class HealthCategory(Enum):
    """Categories of health knowledge."""
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    MENTAL_HEALTH = "mental_health"
    PREVENTIVE = "preventive"
    LIFESTYLE = "lifestyle"
    WELLNESS = "wellness"


class NutrientType(Enum):
    """Types of nutrients."""
    MACRONUTRIENT = "macronutrient"  # Carbs, proteins, fats
    MICRONUTRIENT = "micronutrient"  # Vitamins, minerals
    WATER = "water"
    FIBER = "fiber"


class ExerciseType(Enum):
    """Types of exercise."""
    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    BALANCE = "balance"
    HIIT = "hiit"


class MentalHealthTopic(Enum):
    """Mental health topics."""
    STRESS = "stress"
    ANXIETY = "anxiety"
    DEPRESSION = "depression"
    SLEEP = "sleep"
    MINDFULNESS = "mindfulness"
    RESILIENCE = "resilience"


class HealthProficiency(Enum):
    """Proficiency levels for health knowledge."""
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# ============================================================================
# NUTRITION DATA STRUCTURES
# ============================================================================

@dataclass
class Nutrient:
    """A nutrient with nutritional information."""
    nutrient_id: str
    name: str
    nutrient_type: NutrientType
    daily_value: str = ""  # Recommended daily amount
    function: str = ""
    food_sources: List[str] = field(default_factory=list)
    deficiency_symptoms: List[str] = field(default_factory=list)
    excess_symptoms: List[str] = field(default_factory=list)
    
    # Learning metrics
    proficiency: HealthProficiency = HealthProficiency.NOVICE
    total_reviews: int = 0
    correct_reviews: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nutrient_id": self.nutrient_id,
            "name": self.name,
            "nutrient_type": self.nutrient_type.value,
            "daily_value": self.daily_value,
            "function": self.function,
            "food_sources": self.food_sources,
            "deficiency_symptoms": self.deficiency_symptoms,
            "excess_symptoms": self.excess_symptoms,
            "proficiency": self.proficiency.value,
            "total_reviews": self.total_reviews,
            "correct_reviews": self.correct_reviews,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Nutrient":
        return cls(
            nutrient_id=data["nutrient_id"],
            name=data["name"],
            nutrient_type=NutrientType(data["nutrient_type"]),
            daily_value=data.get("daily_value", ""),
            function=data.get("function", ""),
            food_sources=data.get("food_sources", []),
            deficiency_symptoms=data.get("deficiency_symptoms", []),
            excess_symptoms=data.get("excess_symptoms", []),
            proficiency=HealthProficiency(data.get("proficiency", "novice")),
            total_reviews=data.get("total_reviews", 0),
            correct_reviews=data.get("correct_reviews", 0),
        )


@dataclass
class Food:
    """A food item with nutritional profile."""
    food_id: str
    name: str
    category: str  # fruits, vegetables, proteins, grains, dairy, etc.
    calories_per_serving: int = 0
    serving_size: str = ""
    macronutrients: Dict[str, float] = field(default_factory=dict)  # protein, carbs, fat in grams
    micronutrients: Dict[str, float] = field(default_factory=dict)  # vitamins, minerals
    health_benefits: List[str] = field(default_factory=list)
    considerations: List[str] = field(default_factory=list)  # allergies, interactions
    
    # Cross-domain links
    related_medical_conditions: List[str] = field(default_factory=list)
    
    # Learning metrics
    proficiency: HealthProficiency = HealthProficiency.NOVICE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "food_id": self.food_id,
            "name": self.name,
            "category": self.category,
            "calories_per_serving": self.calories_per_serving,
            "serving_size": self.serving_size,
            "macronutrients": self.macronutrients,
            "micronutrients": self.micronutrients,
            "health_benefits": self.health_benefits,
            "considerations": self.considerations,
            "related_medical_conditions": self.related_medical_conditions,
            "proficiency": self.proficiency.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Food":
        return cls(
            food_id=data["food_id"],
            name=data["name"],
            category=data["category"],
            calories_per_serving=data.get("calories_per_serving", 0),
            serving_size=data.get("serving_size", ""),
            macronutrients=data.get("macronutrients", {}),
            micronutrients=data.get("micronutrients", {}),
            health_benefits=data.get("health_benefits", []),
            considerations=data.get("considerations", []),
            related_medical_conditions=data.get("related_medical_conditions", []),
            proficiency=HealthProficiency(data.get("proficiency", "novice")),
        )


# ============================================================================
# EXERCISE DATA STRUCTURES
# ============================================================================

@dataclass
class Exercise:
    """An exercise with instructions and benefits."""
    exercise_id: str
    name: str
    exercise_type: ExerciseType
    muscle_groups: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    difficulty: int = 1  # 1-5
    
    instructions: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    precautions: List[str] = field(default_factory=list)
    variations: List[str] = field(default_factory=list)
    
    # Cross-domain links
    related_conditions: List[str] = field(default_factory=list)  # Conditions this helps
    
    # Learning metrics
    proficiency: HealthProficiency = HealthProficiency.NOVICE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exercise_id": self.exercise_id,
            "name": self.name,
            "exercise_type": self.exercise_type.value,
            "muscle_groups": self.muscle_groups,
            "equipment": self.equipment,
            "difficulty": self.difficulty,
            "instructions": self.instructions,
            "benefits": self.benefits,
            "precautions": self.precautions,
            "variations": self.variations,
            "related_conditions": self.related_conditions,
            "proficiency": self.proficiency.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Exercise":
        return cls(
            exercise_id=data["exercise_id"],
            name=data["name"],
            exercise_type=ExerciseType(data["exercise_type"]),
            muscle_groups=data.get("muscle_groups", []),
            equipment=data.get("equipment", []),
            difficulty=data.get("difficulty", 1),
            instructions=data.get("instructions", []),
            benefits=data.get("benefits", []),
            precautions=data.get("precautions", []),
            variations=data.get("variations", []),
            related_conditions=data.get("related_conditions", []),
            proficiency=HealthProficiency(data.get("proficiency", "novice")),
        )


@dataclass
class WorkoutPlan:
    """A structured workout plan."""
    plan_id: str
    name: str
    description: str
    goal: str  # weight loss, muscle gain, endurance, flexibility
    duration_weeks: int = 4
    sessions_per_week: int = 3
    exercises: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "goal": self.goal,
            "duration_weeks": self.duration_weeks,
            "sessions_per_week": self.sessions_per_week,
            "exercises": self.exercises,
        }


# ============================================================================
# MENTAL HEALTH DATA STRUCTURES
# ============================================================================

@dataclass
class MentalHealthConcept:
    """A mental health concept or technique."""
    concept_id: str
    name: str
    topic: MentalHealthTopic
    description: str = ""
    techniques: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    when_to_use: List[str] = field(default_factory=list)
    
    # Cross-domain links
    related_conditions: List[str] = field(default_factory=list)
    
    # Learning metrics
    proficiency: HealthProficiency = HealthProficiency.NOVICE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "topic": self.topic.value,
            "description": self.description,
            "techniques": self.techniques,
            "benefits": self.benefits,
            "when_to_use": self.when_to_use,
            "related_conditions": self.related_conditions,
            "proficiency": self.proficiency.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MentalHealthConcept":
        return cls(
            concept_id=data["concept_id"],
            name=data["name"],
            topic=MentalHealthTopic(data["topic"]),
            description=data.get("description", ""),
            techniques=data.get("techniques", []),
            benefits=data.get("benefits", []),
            when_to_use=data.get("when_to_use", []),
            related_conditions=data.get("related_conditions", []),
            proficiency=HealthProficiency(data.get("proficiency", "novice")),
        )


# ============================================================================
# WELLNESS TIP
# ============================================================================

@dataclass
class WellnessTip:
    """A wellness tip or recommendation."""
    tip_id: str
    title: str
    category: HealthCategory
    description: str
    actionable_steps: List[str] = field(default_factory=list)
    evidence_level: str = ""  # strong, moderate, limited
    references: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tip_id": self.tip_id,
            "title": self.title,
            "category": self.category.value,
            "description": self.description,
            "actionable_steps": self.actionable_steps,
            "evidence_level": self.evidence_level,
            "references": self.references,
        }


# ============================================================================
# HEALTH DOMAIN CLASS
# ============================================================================

class HealthDomain:
    """
    Health and wellness knowledge domain for RPA.
    
    Features:
    - Nutrition knowledge with macro/micronutrients
    - Exercise library with instructions
    - Mental health concepts and techniques
    - Preventive care recommendations
    - Cross-domain integration with medicine
    - Spaced repetition for retention
    """
    
    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
        medical_domain: Optional[Any] = None,  # MedicalDomain for cross-linking
    ):
        """Initialize health domain."""
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()
        self.medical_domain = medical_domain
        
        # Knowledge stores
        self._nutrients: Dict[str, Nutrient] = {}
        self._foods: Dict[str, Food] = {}
        self._exercises: Dict[str, Exercise] = {}
        self._workout_plans: Dict[str, WorkoutPlan] = {}
        self._mental_health: Dict[str, MentalHealthConcept] = {}
        self._wellness_tips: Dict[str, WellnessTip] = {}
        
        # Cross-domain links: health_item_id -> [medical_condition_names]
        self._medicine_links: Dict[str, List[str]] = {}
        
        # Review history
        self._review_history: List[Dict[str, Any]] = []
        
        # Initialize with foundational knowledge
        self._initialize_nutrients()
        self._initialize_foods()
        self._initialize_exercises()
        self._initialize_mental_health()
        self._initialize_wellness_tips()
    
    def _initialize_nutrients(self) -> None:
        """Initialize with essential nutrients."""
        # Macronutrients
        macronutrients = [
            ("Protein", "Builds and repairs tissues, makes enzymes", "46-56g/day",
             ["Meat", "Fish", "Eggs", "Legumes", "Nuts"], ["Muscle loss", "Weakness"], ["Kidney strain (excess)"]),
            ("Carbohydrates", "Primary energy source", "130g/day",
             ["Grains", "Fruits", "Vegetables", "Legumes"], ["Fatigue", "Headache"], ["Weight gain (excess)"]),
            ("Fats", "Energy storage, hormone production, nutrient absorption", "20-35% of calories",
             ["Oils", "Nuts", "Avocado", "Fatty fish"], ["Dry skin", "Hair loss"], ["Heart disease (excess saturated)"]),
            ("Fiber", "Digestive health, blood sugar regulation", "25-38g/day",
             ["Whole grains", "Vegetables", "Fruits", "Legumes"], ["Constipation", "High cholesterol"], ["Bloating (excess)"]),
        ]
        
        for name, function, dv, sources, deficiency, excess in macronutrients:
            nutrient = Nutrient(
                nutrient_id=f"macro_{uuid.uuid4().hex[:8]}",
                name=name,
                nutrient_type=NutrientType.MACRONUTRIENT,
                daily_value=dv,
                function=function,
                food_sources=sources,
                deficiency_symptoms=deficiency,
                excess_symptoms=excess,
            )
            self._nutrients[nutrient.nutrient_id] = nutrient
        
        # Key Vitamins
        vitamins = [
            ("Vitamin A", "Vision, immune function, skin health", "700-900 mcg",
             ["Carrots", "Sweet potatoes", "Spinach", "Liver"], ["Night blindness", "Dry skin"], ["Liver damage (excess)"]),
            ("Vitamin B12", "Nerve function, DNA synthesis, red blood cells", "2.4 mcg",
             ["Meat", "Fish", "Eggs", "Dairy"], ["Anemia", "Nerve damage"], ["Generally safe"]),
            ("Vitamin C", "Immune function, collagen synthesis, antioxidant", "75-90 mg",
             ["Citrus fruits", "Berries", "Peppers", "Broccoli"], ["Scurvy", "Poor wound healing"], ["Kidney stones (excess)"]),
            ("Vitamin D", "Calcium absorption, bone health, immune function", "600-800 IU",
             ["Sunlight", "Fatty fish", "Fortified foods"], ["Rickets", "Bone pain"], ["Calcium buildup (excess)"]),
            ("Vitamin E", "Antioxidant, immune function", "15 mg",
             ["Nuts", "Seeds", "Vegetable oils"], ["Nerve damage", "Weakness"], ["Bleeding risk (excess)"]),
            ("Vitamin K", "Blood clotting, bone metabolism", "90-120 mcg",
             ["Leafy greens", "Broccoli", "Brussels sprouts"], ["Excessive bleeding"], ["Generally safe"]),
            ("Folate", "DNA synthesis, cell division, pregnancy health", "400 mcg",
             ["Leafy greens", "Legumes", "Fortified grains"], ["Anemia", "Birth defects"], ["Masks B12 deficiency"]),
        ]
        
        for name, function, dv, sources, deficiency, excess in vitamins:
            nutrient = Nutrient(
                nutrient_id=f"vit_{uuid.uuid4().hex[:8]}",
                name=name,
                nutrient_type=NutrientType.MICRONUTRIENT,
                daily_value=dv,
                function=function,
                food_sources=sources,
                deficiency_symptoms=deficiency,
                excess_symptoms=excess,
            )
            self._nutrients[nutrient.nutrient_id] = nutrient
        
        # Key Minerals
        minerals = [
            ("Iron", "Oxygen transport, energy production", "8-18 mg",
             ["Red meat", "Spinach", "Legumes", "Fortified cereals"], ["Anemia", "Fatigue"], ["Organ damage (excess)"]),
            ("Calcium", "Bone health, muscle function, nerve signaling", "1000-1200 mg",
             ["Dairy", "Leafy greens", "Fortified foods"], ["Osteoporosis", "Muscle cramps"], ["Kidney stones (excess)"]),
            ("Magnesium", "Muscle and nerve function, energy production", "310-420 mg",
             ["Nuts", "Seeds", "Whole grains", "Leafy greens"], ["Muscle cramps", "Fatigue"], ["Diarrhea (excess)"]),
            ("Potassium", "Fluid balance, nerve signals, muscle contractions", "2600-3400 mg",
             ["Bananas", "Potatoes", "Leafy greens"], ["Muscle weakness", "Arrhythmia"], ["Heart problems (excess)"]),
            ("Zinc", "Immune function, wound healing, protein synthesis", "8-11 mg",
             ["Meat", "Shellfish", "Legumes", "Nuts"], ["Delayed healing", "Hair loss"], ["Nausea (excess)"]),
            ("Sodium", "Fluid balance, nerve function", "1500-2300 mg",
             ["Salt", "Processed foods"], ["Hyponatremia (rare)"], ["Hypertension (excess)"]),
        ]
        
        for name, function, dv, sources, deficiency, excess in minerals:
            nutrient = Nutrient(
                nutrient_id=f"min_{uuid.uuid4().hex[:8]}",
                name=name,
                nutrient_type=NutrientType.MICRONUTRIENT,
                daily_value=dv,
                function=function,
                food_sources=sources,
                deficiency_symptoms=deficiency,
                excess_symptoms=excess,
            )
            self._nutrients[nutrient.nutrient_id] = nutrient
    
    def _initialize_foods(self) -> None:
        """Initialize with common healthy foods."""
        foods = [
            # Fruits
            ("Apple", "fruits", 95, "1 medium",
             {"carbs": 25, "fiber": 4}, {"vitamin_c": 8},
             ["Heart health", "Blood sugar regulation"], ["Fructose sensitivity"]),
            ("Banana", "fruits", 105, "1 medium",
             {"carbs": 27, "fiber": 3}, {"potassium": 422},
             ["Potassium source", "Quick energy"], ["High sugar content"]),
            ("Blueberries", "fruits", 85, "1 cup",
             {"carbs": 21, "fiber": 4}, {"vitamin_c": 14, "vitamin_k": 28},
             ["Antioxidants", "Brain health"], []),
            
            # Vegetables
            ("Broccoli", "vegetables", 55, "1 cup",
             {"protein": 4, "carbs": 11, "fiber": 5}, {"vitamin_c": 135, "vitamin_k": 116},
             ["Cancer prevention", "Heart health"], ["Thyroid concerns (raw)"]),
            ("Spinach", "vegetables", 7, "1 cup raw",
             {"protein": 1, "carbs": 1, "fiber": 0.5}, {"vitamin_a": 56, "vitamin_k": 181, "iron": 0.8},
             ["Iron source", "Eye health"], ["Kidney stones (oxalates)"]),
            ("Sweet Potato", "vegetables", 115, "1 medium",
             {"carbs": 27, "fiber": 4}, {"vitamin_a": 438, "vitamin_c": 37},
             ["Blood sugar friendly", "Vitamin A source"], []),
            
            # Proteins
            ("Salmon", "proteins", 206, "3.5 oz",
             {"protein": 22, "fat": 13}, {"vitamin_d": 66, "selenium": 59},
             ["Heart health", "Brain function"], ["Mercury (limit intake)"]),
            ("Chicken Breast", "proteins", 165, "3.5 oz",
             {"protein": 31, "fat": 4}, {},
             ["Lean protein", "Muscle building"], []),
            ("Eggs", "proteins", 78, "1 large",
             {"protein": 6, "fat": 5}, {"vitamin_d": 11, "vitamin_b12": 23},
             ["Complete protein", "Nutrient dense"], ["Cholesterol (some concern)"]),
            ("Lentils", "proteins", 230, "1 cup cooked",
             {"protein": 18, "carbs": 40, "fiber": 16}, {"iron": 6.6, "folate": 358},
             ["Plant protein", "Heart health"], ["Gas/bloating"]),
            
            # Grains
            ("Oatmeal", "grains", 158, "1 cup cooked",
             {"protein": 6, "carbs": 27, "fiber": 4}, {"iron": 1.7, "magnesium": 61},
             ["Heart health", "Blood sugar control"], ["Gluten (some brands)"]),
            ("Quinoa", "grains", 222, "1 cup cooked",
             {"protein": 8, "carbs": 39, "fiber": 5}, {"iron": 2.8, "magnesium": 118},
             ["Complete protein", "Gluten-free"], []),
            
            # Nuts and seeds
            ("Almonds", "nuts", 164, "1 oz",
             {"protein": 6, "fat": 14, "fiber": 4}, {"vitamin_e": 37, "magnesium": 19},
             ["Heart health", "Blood sugar control"], ["High calorie", "Allergies"]),
            ("Walnuts", "nuts", 185, "1 oz",
             {"protein": 4, "fat": 18, "fiber": 2}, {"omega3": 2.5},
             ["Brain health", "Heart health"], ["Allergies"]),
        ]
        
        for name, category, calories, serving, macros, micros, benefits, considerations in foods:
            food = Food(
                food_id=f"food_{uuid.uuid4().hex[:8]}",
                name=name,
                category=category,
                calories_per_serving=calories,
                serving_size=serving,
                macronutrients=macros,
                micronutrients=micros,
                health_benefits=benefits,
                considerations=considerations,
            )
            self._foods[food.food_id] = food
    
    def _initialize_exercises(self) -> None:
        """Initialize with common exercises."""
        exercises = [
            # Cardio
            ("Walking", ExerciseType.CARDIO, ["legs", "core"], [], 1,
             ["Start at comfortable pace", "Swing arms naturally", "Keep head up"],
             ["Heart health", "Weight management", "Mood improvement"],
             ["Wear supportive shoes", "Start gradually"],
             ["Brisk walking", "Incline walking", "Nordic walking"],
             ["Heart disease", "Diabetes", "Depression"]),
            
            ("Running", ExerciseType.CARDIO, ["legs", "core"], [], 3,
             ["Land on midfoot", "Keep strides short", "Maintain upright posture"],
             ["Cardiovascular fitness", "Weight loss", "Mental health"],
             ["Proper footwear essential", "Gradually increase distance"],
             ["Jogging", "Sprinting", "Trail running"],
             ["Heart disease", "Obesity", "Anxiety"]),
            
            ("Cycling", ExerciseType.CARDIO, ["legs", "glutes"], ["Bicycle"], 2,
             ["Adjust seat height properly", "Keep back straight", "Pedal in circular motion"],
             ["Low impact cardio", "Leg strength", "Endurance"],
             ["Wear helmet", "Follow traffic rules"],
             ["Stationary bike", "Mountain biking", "Road cycling"],
             ["Heart disease", "Joint issues"]),
            
            # Strength
            ("Push-ups", ExerciseType.STRENGTH, ["chest", "shoulders", "triceps", "core"], [], 2,
             ["Hands shoulder-width apart", "Lower chest to ground", "Keep body straight"],
             ["Upper body strength", "Core stability", "No equipment needed"],
             ["Modify if needed", "Avoid if shoulder injury"],
             ["Knee push-ups", "Incline push-ups", "Diamond push-ups"],
             ["Posture problems", "Weak upper body"]),
            
            ("Squats", ExerciseType.STRENGTH, ["quads", "glutes", "hamstrings", "core"], [], 2,
             ["Feet shoulder-width apart", "Push hips back", "Keep chest up", "Knees track over toes"],
             ["Lower body strength", "Functional movement", "Core engagement"],
             ["Maintain proper form", "Start with bodyweight"],
             ["Goblet squats", "Jump squats", "Sumo squats"],
             ["Knee problems (with caution)", "Mobility issues"]),
            
            ("Deadlifts", ExerciseType.STRENGTH, ["back", "glutes", "hamstrings", "core"], ["Barbell"], 4,
             ["Feet hip-width apart", "Bend at hips and knees", "Keep back straight", "Drive through heels"],
             ["Full body strength", "Posture improvement", "Functional strength"],
             ["Proper form critical", "Start light", "Avoid with back issues"],
             ["Romanian deadlift", "Sumo deadlift", "Single-leg deadlift"],
             []),
            
            # Flexibility
            ("Yoga", ExerciseType.FLEXIBILITY, ["full body"], ["Yoga mat"], 2,
             ["Focus on breath", "Move slowly", "Listen to your body", "Hold poses 30-60 seconds"],
             ["Flexibility", "Stress reduction", "Balance", "Mindfulness"],
             ["Use props if needed", "Don't force stretches"],
             ["Hatha yoga", "Vinyasa", "Restorative yoga"],
             ["Stress", "Anxiety", "Back pain", "Poor flexibility"]),
            
            ("Stretching", ExerciseType.FLEXIBILITY, ["full body"], [], 1,
             ["Hold each stretch 15-30 seconds", "Don't bounce", "Breathe deeply", "Feel gentle tension, not pain"],
             ["Flexibility", "Injury prevention", "Recovery", "Stress relief"],
             ["Warm up first", "Never force a stretch"],
             ["Static stretching", "Dynamic stretching", "PNF stretching"],
             ["Muscle tightness", "Post-workout recovery"]),
            
            # Balance
            ("Tai Chi", ExerciseType.BALANCE, ["full body"], [], 1,
             ["Move slowly and deliberately", "Focus on breath", "Maintain good posture", "Transfer weight smoothly"],
             ["Balance", "Stress reduction", "Flexibility", "Strength"],
             ["Start with basic movements"],
             ["Yang style", "Chen style", "Sun style"],
             ["Balance problems", "Stress", "Older adults"]),
        ]
        
        for name, ex_type, muscles, equipment, difficulty, instructions, benefits, precautions, variations, conditions in exercises:
            exercise = Exercise(
                exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
                name=name,
                exercise_type=ex_type,
                muscle_groups=muscles,
                equipment=equipment,
                difficulty=difficulty,
                instructions=instructions,
                benefits=benefits,
                precautions=precautions,
                variations=variations,
                related_conditions=conditions,
            )
            self._exercises[exercise.exercise_id] = exercise
    
    def _initialize_mental_health(self) -> None:
        """Initialize with mental health concepts."""
        concepts = [
            # Stress Management
            ("Deep Breathing", MentalHealthTopic.STRESS,
             "Controlled breathing technique to activate relaxation response",
             ["4-7-8 breathing", "Box breathing", "Diaphragmatic breathing"],
             ["Reduces stress hormones", "Lowers blood pressure", "Calms nervous system"],
             ["Before stressful events", "During anxiety", "Before sleep"],
             ["Anxiety", "Hypertension", "Insomnia"]),
            
            ("Progressive Muscle Relaxation", MentalHealthTopic.STRESS,
             "Systematically tensing and relaxing muscle groups",
             ["Start from feet", "Tense for 5 seconds", "Release and notice difference", "Work up body"],
             ["Physical relaxation", "Body awareness", "Sleep improvement"],
             ["Before bed", "After stressful day", "During tension"],
             ["Insomnia", "Chronic pain", "Anxiety"]),
            
            # Anxiety
            ("Grounding Techniques", MentalHealthTopic.ANXIETY,
             "Techniques to anchor to present moment during anxiety",
             ["5-4-3-2-1 technique", "Physical grounding", "Mental grounding"],
             ["Reduces anxiety", "Interrupts panic", "Present moment focus"],
             ["During panic attacks", "Feeling overwhelmed", "Dissociation"],
             ["Panic disorder", "PTSD", "GAD"]),
            
            ("Cognitive Reframing", MentalHealthTopic.ANXIETY,
             "Changing perspective on anxiety-provoking thoughts",
             ["Identify thought", "Challenge evidence", "Consider alternatives", "Create balanced thought"],
             ["Reduces anxiety", "Improves thinking patterns", "Empowerment"],
             ["Negative self-talk", "Catastrophizing", "Overthinking"],
             ["GAD", "Depression", "Social anxiety"]),
            
            # Depression
            ("Behavioral Activation", MentalHealthTopic.DEPRESSION,
             "Scheduling enjoyable activities to improve mood",
             ["List enjoyable activities", "Schedule daily", "Start small", "Track mood"],
             ["Improves mood", "Increases motivation", "Builds routine"],
             ["Low motivation", "Depression episodes", "Anhedonia"],
             ["Depression", "Anxiety"]),
            
            ("Gratitude Practice", MentalHealthTopic.DEPRESSION,
             "Regular practice of acknowledging positive aspects of life",
             ["Gratitude journal", "Three good things", "Gratitude letter", "Mental gratitude"],
             ["Improves mood", "Increases positivity", "Better sleep"],
             ["Daily (morning or evening)", "During difficult times"],
             ["Depression", "Anxiety", "Stress"]),
            
            # Sleep
            ("Sleep Hygiene", MentalHealthTopic.SLEEP,
             "Practices to improve sleep quality",
             ["Consistent sleep schedule", "Dark cool room", "No screens before bed", "Relaxing bedtime routine"],
             ["Better sleep quality", "More energy", "Improved mood"],
             ["Daily implementation", "Sleep difficulties"],
             ["Insomnia", "Poor sleep quality"]),
            
            # Mindfulness
            ("Mindfulness Meditation", MentalHealthTopic.MINDFULNESS,
             "Practice of present moment awareness without judgment",
             ["Focus on breath", "Observe thoughts", "Return to present", "Body scan"],
             ["Reduced stress", "Better focus", "Emotional regulation", "Self-awareness"],
             ["Daily practice", "Before stressful events", "During difficult emotions"],
             ["Anxiety", "Depression", "Chronic pain", "Stress"]),
            
            # Resilience
            ("Building Resilience", MentalHealthTopic.RESILIENCE,
             "Developing capacity to recover from difficulties",
             ["Maintain connections", "Practice self-care", "Set realistic goals", "Embrace change"],
             ["Better coping", "Mental toughness", "Faster recovery from setbacks"],
             ["Ongoing practice", "After difficult experiences"],
             ["Depression", "Anxiety", "PTSD"]),
        ]
        
        for name, topic, description, techniques, benefits, when_use, conditions in concepts:
            concept = MentalHealthConcept(
                concept_id=f"mh_{uuid.uuid4().hex[:8]}",
                name=name,
                topic=topic,
                description=description,
                techniques=techniques,
                benefits=benefits,
                when_to_use=when_use,
                related_conditions=conditions,
            )
            self._mental_health[concept.concept_id] = concept
    
    def _initialize_wellness_tips(self) -> None:
        """Initialize with wellness tips."""
        tips = [
            ("Stay Hydrated", HealthCategory.NUTRITION,
             "Drink adequate water throughout the day for optimal health",
             ["Carry a water bottle", "Set reminders", "Drink before meals", "Eat water-rich foods"],
             "strong"),
            ("Prioritize Sleep", HealthCategory.LIFESTYLE,
             "Aim for 7-9 hours of quality sleep per night",
             ["Maintain consistent schedule", "Create sleep-friendly environment", "Limit caffeine after noon"],
             "strong"),
            ("Move Daily", HealthCategory.EXERCISE,
             "Incorporate physical activity into your daily routine",
             ["Take walking breaks", "Use stairs", "Stand during calls", "Schedule workouts"],
             "strong"),
            ("Manage Stress", HealthCategory.MENTAL_HEALTH,
             "Develop healthy coping strategies for stress",
             ["Practice deep breathing", "Take breaks", "Maintain hobbies", "Connect with others"],
             "strong"),
            ("Eat Mindfully", HealthCategory.NUTRITION,
             "Pay attention to what and how you eat",
             ["Eat slowly", "Avoid distractions", "Listen to hunger cues", "Enjoy your food"],
             "moderate"),
            ("Stay Connected", HealthCategory.MENTAL_HEALTH,
             "Maintain social connections for mental well-being",
             ["Schedule regular contact", "Join groups", "Volunteer", "Reach out when struggling"],
             "strong"),
            ("Practice Prevention", HealthCategory.PREVENTIVE,
             "Engage in preventive health measures",
             ["Regular check-ups", "Screenings", "Vaccinations", "Self-examinations"],
             "strong"),
            ("Limit Processed Foods", HealthCategory.NUTRITION,
             "Reduce intake of highly processed foods",
             ["Cook at home", "Read labels", "Choose whole foods", "Plan meals"],
             "moderate"),
        ]
        
        for title, category, description, steps, evidence in tips:
            tip = WellnessTip(
                tip_id=f"tip_{uuid.uuid4().hex[:8]}",
                title=title,
                category=category,
                description=description,
                actionable_steps=steps,
                evidence_level=evidence,
            )
            self._wellness_tips[tip.tip_id] = tip
    
    # ========================================================================
    # CROSS-DOMAIN INTEGRATION
    # ========================================================================
    
    def set_medical_domain(self, medical_domain: Any) -> None:
        """Set the medical domain for cross-domain integration."""
        self.medical_domain = medical_domain
        self._update_medicine_links()
    
    def _update_medicine_links(self) -> None:
        """Update cross-domain links with medicine."""
        if not self.medical_domain:
            return
        
        # Link foods to medical conditions
        for food_id, food in self._foods.items():
            links = []
            for condition in food.related_medical_conditions:
                conditions = self.medical_domain.search_conditions(condition)
                links.extend([c.name for c in conditions])
            if links:
                self._medicine_links[food_id] = links
        
        # Link exercises to medical conditions
        for ex_id, exercise in self._exercises.items():
            if exercise.related_conditions:
                self._medicine_links[ex_id] = exercise.related_conditions
        
        # Link mental health concepts to conditions
        for mh_id, concept in self._mental_health.items():
            if concept.related_conditions:
                self._medicine_links[mh_id] = concept.related_conditions
    
    def get_medical_links(self, item_id: str) -> List[str]:
        """Get medical conditions linked to a health item."""
        return self._medicine_links.get(item_id, [])
    
    # ========================================================================
    # NUTRIENT MANAGEMENT
    # ========================================================================
    
    def add_nutrient(self, name: str, nutrient_type: NutrientType,
                     function: str = "", daily_value: str = "",
                     food_sources: Optional[List[str]] = None) -> Nutrient:
        """Add a new nutrient."""
        nutrient = Nutrient(
            nutrient_id=f"nutrient_{uuid.uuid4().hex[:8]}",
            name=name,
            nutrient_type=nutrient_type,
            daily_value=daily_value,
            function=function,
            food_sources=food_sources or [],
        )
        self._nutrients[nutrient.nutrient_id] = nutrient
        return nutrient
    
    def get_nutrient(self, nutrient_id: str) -> Optional[Nutrient]:
        """Get a nutrient by ID."""
        return self._nutrients.get(nutrient_id)
    
    def search_nutrients(self, query: str) -> List[Nutrient]:
        """Search nutrients by name or function."""
        query_lower = query.lower()
        return [
            n for n in self._nutrients.values()
            if query_lower in n.name.lower() or query_lower in n.function.lower()
        ]
    
    def get_nutrients_by_type(self, nutrient_type: NutrientType) -> List[Nutrient]:
        """Get nutrients by type."""
        return [n for n in self._nutrients.values() if n.nutrient_type == nutrient_type]
    
    # ========================================================================
    # FOOD MANAGEMENT
    # ========================================================================
    
    def add_food(self, name: str, category: str, calories: int = 0,
                 serving_size: str = "", macronutrients: Optional[Dict] = None,
                 health_benefits: Optional[List[str]] = None) -> Food:
        """Add a new food."""
        food = Food(
            food_id=f"food_{uuid.uuid4().hex[:8]}",
            name=name,
            category=category,
            calories_per_serving=calories,
            serving_size=serving_size,
            macronutrients=macronutrients or {},
            health_benefits=health_benefits or [],
        )
        self._foods[food.food_id] = food
        return food
    
    def get_food(self, food_id: str) -> Optional[Food]:
        """Get a food by ID."""
        return self._foods.get(food_id)
    
    def search_foods(self, query: str) -> List[Food]:
        """Search foods by name."""
        query_lower = query.lower()
        return [f for f in self._foods.values() if query_lower in f.name.lower()]
    
    def get_foods_by_category(self, category: str) -> List[Food]:
        """Get foods by category."""
        return [f for f in self._foods.values() if f.category == category]
    
    # ========================================================================
    # EXERCISE MANAGEMENT
    # ========================================================================
    
    def add_exercise(self, name: str, exercise_type: ExerciseType,
                     muscle_groups: Optional[List[str]] = None,
                     instructions: Optional[List[str]] = None,
                     difficulty: int = 1) -> Exercise:
        """Add a new exercise."""
        exercise = Exercise(
            exercise_id=f"ex_{uuid.uuid4().hex[:8]}",
            name=name,
            exercise_type=exercise_type,
            muscle_groups=muscle_groups or [],
            instructions=instructions or [],
            difficulty=difficulty,
        )
        self._exercises[exercise.exercise_id] = exercise
        return exercise
    
    def get_exercise(self, exercise_id: str) -> Optional[Exercise]:
        """Get an exercise by ID."""
        return self._exercises.get(exercise_id)
    
    def search_exercises(self, query: str) -> List[Exercise]:
        """Search exercises by name."""
        query_lower = query.lower()
        return [e for e in self._exercises.values() if query_lower in e.name.lower()]
    
    def get_exercises_by_type(self, exercise_type: ExerciseType) -> List[Exercise]:
        """Get exercises by type."""
        return [e for e in self._exercises.values() if e.exercise_type == exercise_type]
    
    def get_exercises_by_muscle(self, muscle: str) -> List[Exercise]:
        """Get exercises targeting a specific muscle group."""
        return [e for e in self._exercises.values() if muscle.lower() in [m.lower() for m in e.muscle_groups]]
    
    # ========================================================================
    # MENTAL HEALTH MANAGEMENT
    # ========================================================================
    
    def add_mental_health_concept(self, name: str, topic: MentalHealthTopic,
                                  description: str = "",
                                  techniques: Optional[List[str]] = None) -> MentalHealthConcept:
        """Add a new mental health concept."""
        concept = MentalHealthConcept(
            concept_id=f"mh_{uuid.uuid4().hex[:8]}",
            name=name,
            topic=topic,
            description=description,
            techniques=techniques or [],
        )
        self._mental_health[concept.concept_id] = concept
        return concept
    
    def get_mental_health_concept(self, concept_id: str) -> Optional[MentalHealthConcept]:
        """Get a mental health concept by ID."""
        return self._mental_health.get(concept_id)
    
    def get_mental_health_by_topic(self, topic: MentalHealthTopic) -> List[MentalHealthConcept]:
        """Get mental health concepts by topic."""
        return [c for c in self._mental_health.values() if c.topic == topic]
    
    # ========================================================================
    # EXERCISE GENERATION
    # ========================================================================
    
    def generate_nutrition_exercise(self, nutrient: Optional[Nutrient] = None) -> Dict[str, Any]:
        """Generate a nutrition exercise."""
        if nutrient is None:
            nutrients = list(self._nutrients.values())
            if not nutrients:
                return {"error": "No nutrients available"}
            nutrient = random.choice(nutrients)
        
        # Generate multiple choice for function
        all_functions = [n.function for n in self._nutrients.values() if n.nutrient_id != nutrient.nutrient_id and n.function]
        distractors = random.sample(all_functions, min(3, len(all_functions)))
        
        options = [nutrient.function] + distractors
        random.shuffle(options)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "nutrient_function",
            "question": f"What is the primary function of {nutrient.name}?",
            "options": options,
            "correct_answer": nutrient.function,
            "correct_index": options.index(nutrient.function),
            "food_sources": nutrient.food_sources,
            "difficulty": 1,
        }
    
    def generate_food_exercise(self, food: Optional[Food] = None) -> Dict[str, Any]:
        """Generate a food knowledge exercise."""
        if food is None:
            foods = list(self._foods.values())
            if not foods:
                return {"error": "No foods available"}
            food = random.choice(foods)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "food_knowledge",
            "question": f"What are the health benefits of {food.name}?",
            "food_name": food.name,
            "category": food.category,
            "calories": food.calories_per_serving,
            "serving_size": food.serving_size,
            "macronutrients": food.macronutrients,
            "health_benefits": food.health_benefits,
            "considerations": food.considerations,
            "difficulty": 1,
        }
    
    def generate_exercise_exercise(self, exercise: Optional[Exercise] = None) -> Dict[str, Any]:
        """Generate an exercise knowledge exercise."""
        if exercise is None:
            exercises = list(self._exercises.values())
            if not exercises:
                return {"error": "No exercises available"}
            exercise = random.choice(exercises)
        
        # Generate multiple choice for benefits
        if exercise.benefits:
            correct_benefit = random.choice(exercise.benefits)
            all_benefits = []
            for e in self._exercises.values():
                all_benefits.extend(e.benefits)
            distractors = [b for b in all_benefits if b not in exercise.benefits]
            distractors = random.sample(distractors, min(3, len(distractors)))
            
            options = [correct_benefit] + distractors
            random.shuffle(options)
            
            return {
                "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
                "type": "exercise_benefits",
                "question": f"Which is a benefit of {exercise.name}?",
                "options": options,
                "correct_answer": correct_benefit,
                "correct_index": options.index(correct_benefit),
                "muscle_groups": exercise.muscle_groups,
                "difficulty": exercise.difficulty,
            }
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "exercise_instructions",
            "question": f"How do you perform {exercise.name}?",
            "exercise_name": exercise.name,
            "instructions": exercise.instructions,
            "muscle_groups": exercise.muscle_groups,
            "difficulty": exercise.difficulty,
        }
    
    def generate_mental_health_exercise(self, concept: Optional[MentalHealthConcept] = None) -> Dict[str, Any]:
        """Generate a mental health knowledge exercise."""
        if concept is None:
            concepts = list(self._mental_health.values())
            if not concepts:
                return {"error": "No mental health concepts available"}
            concept = random.choice(concepts)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "mental_health_technique",
            "question": f"What techniques are used in {concept.name}?",
            "concept_name": concept.name,
            "topic": concept.topic.value,
            "description": concept.description,
            "techniques": concept.techniques,
            "benefits": concept.benefits,
            "when_to_use": concept.when_to_use,
            "difficulty": 1,
        }
    
    # ========================================================================
    # STATISTICS AND EXPORT
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get health domain learning statistics."""
        return {
            "nutrients": {
                "total": len(self._nutrients),
                "by_type": {
                    nt.value: sum(1 for n in self._nutrients.values() if n.nutrient_type == nt)
                    for nt in NutrientType
                },
            },
            "foods": {
                "total": len(self._foods),
                "by_category": self._count_by_category(self._foods, "category"),
            },
            "exercises": {
                "total": len(self._exercises),
                "by_type": {
                    et.value: sum(1 for e in self._exercises.values() if e.exercise_type == et)
                    for et in ExerciseType
                },
            },
            "mental_health": {
                "total": len(self._mental_health),
                "by_topic": {
                    mt.value: sum(1 for c in self._mental_health.values() if c.topic == mt)
                    for mt in MentalHealthTopic
                },
            },
            "wellness_tips": len(self._wellness_tips),
            "medicine_links": len(self._medicine_links),
            "total_reviews": len(self._review_history),
        }
    
    def _count_by_category(self, items: Dict, attr: str) -> Dict[str, int]:
        """Count items by category attribute."""
        counts = {}
        for item in items.values():
            cat = getattr(item, attr, "unknown")
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    def export_progress(self) -> Dict[str, Any]:
        """Export learning progress for persistence."""
        return {
            "nutrients": {k: v.to_dict() for k, v in self._nutrients.items()},
            "foods": {k: v.to_dict() for k, v in self._foods.items()},
            "exercises": {k: v.to_dict() for k, v in self._exercises.items()},
            "mental_health": {k: v.to_dict() for k, v in self._mental_health.items()},
            "wellness_tips": {k: v.to_dict() for k, v in self._wellness_tips.items()},
            "medicine_links": self._medicine_links,
            "review_history": self._review_history,
            "statistics": self.get_statistics(),
        }
    
    def import_progress(self, data: Dict[str, Any]) -> None:
        """Import learning progress from persistence."""
        if "nutrients" in data:
            for k, v in data["nutrients"].items():
                self._nutrients[k] = Nutrient.from_dict(v)
        
        if "foods" in data:
            for k, v in data["foods"].items():
                self._foods[k] = Food.from_dict(v)
        
        if "exercises" in data:
            for k, v in data["exercises"].items():
                self._exercises[k] = Exercise.from_dict(v)
        
        if "mental_health" in data:
            for k, v in data["mental_health"].items():
                self._mental_health[k] = MentalHealthConcept.from_dict(v)
        
        if "wellness_tips" in data:
            for k, v in data["wellness_tips"].items():
                self._wellness_tips[k] = WellnessTip(**v)
        
        if "medicine_links" in data:
            self._medicine_links = data["medicine_links"]
        
        if "review_history" in data:
            self._review_history = data["review_history"]
    
    def save_patterns_to_ltm(self) -> int:
        """Save learned health patterns to Long-Term Memory."""
        from rpa.core.node import Node, NodeType
        
        count = 0
        
        # Save nutrients
        for nutrient in self._nutrients.values():
            node = Node(
                node_id=f"health_nutrient:{nutrient.nutrient_id}",
                label=nutrient.name,
                node_type=NodeType.CONCEPT,
                content=nutrient.function,
                domain="health",
                hierarchy_level=1,
                metadata={
                    "type": "nutrient",
                    "nutrient_type": nutrient.nutrient_type.value,
                    "daily_value": nutrient.daily_value,
                    "food_sources": nutrient.food_sources,
                },
            )
            self.ltm.consolidate(node, source="health_domain")
            count += 1
        
        # Save foods
        for food in self._foods.values():
            node = Node(
                node_id=f"health_food:{food.food_id}",
                label=food.name,
                node_type=NodeType.CONCEPT,
                content=f"{food.category}: {food.calories_per_serving} cal per {food.serving_size}",
                domain="health",
                hierarchy_level=1,
                metadata={
                    "type": "food",
                    "category": food.category,
                    "macronutrients": food.macronutrients,
                    "health_benefits": food.health_benefits,
                },
            )
            self.ltm.consolidate(node, source="health_domain")
            count += 1
        
        # Save exercises
        for exercise in self._exercises.values():
            node = Node(
                node_id=f"health_exercise:{exercise.exercise_id}",
                label=exercise.name,
                node_type=NodeType.CONCEPT,
                content=f"{exercise.exercise_type.value}: {', '.join(exercise.muscle_groups)}",
                domain="health",
                hierarchy_level=1,
                metadata={
                    "type": "exercise",
                    "exercise_type": exercise.exercise_type.value,
                    "muscle_groups": exercise.muscle_groups,
                    "benefits": exercise.benefits,
                },
            )
            self.ltm.consolidate(node, source="health_domain")
            count += 1
        
        # Save mental health concepts
        for concept in self._mental_health.values():
            node = Node(
                node_id=f"health_mh:{concept.concept_id}",
                label=concept.name,
                node_type=NodeType.CONCEPT,
                content=concept.description,
                domain="health",
                hierarchy_level=1,
                metadata={
                    "type": "mental_health",
                    "topic": concept.topic.value,
                    "techniques": concept.techniques,
                    "benefits": concept.benefits,
                },
            )
            self.ltm.consolidate(node, source="health_domain")
            count += 1
        
        logger.info(f"Saved {count} health patterns to LTM")
        return count
