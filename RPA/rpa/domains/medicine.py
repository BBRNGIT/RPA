"""
Medicine Domain Learning Module for RPA.

This module provides comprehensive medical knowledge learning capabilities:
- Medical terminology with roots, prefixes, suffixes
- Anatomy basics by body system
- Common diseases and conditions
- Drug classifications and interactions
- Clinical reasoning patterns
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

class BodySystem(Enum):
    """Major body systems for anatomy learning."""
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    NERVOUS = "nervous"
    MUSCULOSKELETAL = "musculoskeletal"
    DIGESTIVE = "digestive"
    URINARY = "urinary"
    REPRODUCTIVE = "reproductive"
    ENDOCRINE = "endocrine"
    LYMPHATIC = "lymphatic"
    INTEGUMENTARY = "integumentary"
    IMMUNE = "immune"


class MedicalCategory(Enum):
    """Categories of medical knowledge."""
    TERMINOLOGY = "terminology"
    ANATOMY = "anatomy"
    PHYSIOLOGY = "physiology"
    PATHOLOGY = "pathology"
    PHARMACOLOGY = "pharmacology"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    PROCEDURE = "procedure"


class DrugClass(Enum):
    """Major drug classifications."""
    ANALGESIC = "analgesic"
    ANTIBIOTIC = "antibiotic"
    ANTIVIRAL = "antiviral"
    ANTIFUNGAL = "antifungal"
    ANTI_INFLAMMATORY = "anti_inflammatory"
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"
    PSYCHIATRIC = "psychiatric"
    ENDOCRINE = "endocrine"
    GASTROINTESTINAL = "gastrointestinal"
    IMMUNOLOGIC = "immunologic"


class MedicalProficiency(Enum):
    """Proficiency levels for medical knowledge."""
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# ============================================================================
# MEDICAL TERMINOLOGY
# ============================================================================

@dataclass
class MedicalTerm:
    """A medical term with etymology and context."""
    term_id: str
    term: str
    definition: str
    category: MedicalCategory
    body_system: Optional[BodySystem] = None
    
    # Etymology components
    root: str = ""
    prefix: str = ""
    suffix: str = ""
    etymology: str = ""
    
    # Learning context
    examples: List[str] = field(default_factory=list)
    related_terms: List[str] = field(default_factory=list)
    common_abbreviations: List[str] = field(default_factory=list)
    
    # Difficulty and frequency
    difficulty: int = 1  # 1-5 scale
    frequency_rank: int = 0
    
    # Learning metrics
    proficiency: MedicalProficiency = MedicalProficiency.NOVICE
    ease_factor: float = 2.5
    interval: int = 0
    repetitions: int = 0
    next_review: Optional[datetime] = None
    last_review: Optional[datetime] = None
    total_reviews: int = 0
    correct_reviews: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "term_id": self.term_id,
            "term": self.term,
            "definition": self.definition,
            "category": self.category.value,
            "body_system": self.body_system.value if self.body_system else None,
            "root": self.root,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "etymology": self.etymology,
            "examples": self.examples,
            "related_terms": self.related_terms,
            "common_abbreviations": self.common_abbreviations,
            "difficulty": self.difficulty,
            "frequency_rank": self.frequency_rank,
            "proficiency": self.proficiency.value,
            "ease_factor": self.ease_factor,
            "interval": self.interval,
            "repetitions": self.repetitions,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "last_review": self.last_review.isoformat() if self.last_review else None,
            "total_reviews": self.total_reviews,
            "correct_reviews": self.correct_reviews,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MedicalTerm":
        """Deserialize from dictionary."""
        return cls(
            term_id=data["term_id"],
            term=data["term"],
            definition=data["definition"],
            category=MedicalCategory(data["category"]),
            body_system=BodySystem(data["body_system"]) if data.get("body_system") else None,
            root=data.get("root", ""),
            prefix=data.get("prefix", ""),
            suffix=data.get("suffix", ""),
            etymology=data.get("etymology", ""),
            examples=data.get("examples", []),
            related_terms=data.get("related_terms", []),
            common_abbreviations=data.get("common_abbreviations", []),
            difficulty=data.get("difficulty", 1),
            frequency_rank=data.get("frequency_rank", 0),
            proficiency=MedicalProficiency(data.get("proficiency", "novice")),
            ease_factor=data.get("ease_factor", 2.5),
            interval=data.get("interval", 0),
            repetitions=data.get("repetitions", 0),
            next_review=datetime.fromisoformat(data["next_review"]) if data.get("next_review") else None,
            last_review=datetime.fromisoformat(data["last_review"]) if data.get("last_review") else None,
            total_reviews=data.get("total_reviews", 0),
            correct_reviews=data.get("correct_reviews", 0),
        )


@dataclass
class AnatomyStructure:
    """An anatomical structure with location and function."""
    structure_id: str
    name: str
    body_system: BodySystem
    location: str
    function: str
    related_structures: List[str] = field(default_factory=list)
    clinical_significance: str = ""
    latin_name: str = ""
    difficulty: int = 1
    
    # Learning metrics
    proficiency: MedicalProficiency = MedicalProficiency.NOVICE
    total_reviews: int = 0
    correct_reviews: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "structure_id": self.structure_id,
            "name": self.name,
            "body_system": self.body_system.value,
            "location": self.location,
            "function": self.function,
            "related_structures": self.related_structures,
            "clinical_significance": self.clinical_significance,
            "latin_name": self.latin_name,
            "difficulty": self.difficulty,
            "proficiency": self.proficiency.value,
            "total_reviews": self.total_reviews,
            "correct_reviews": self.correct_reviews,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnatomyStructure":
        """Deserialize from dictionary."""
        return cls(
            structure_id=data["structure_id"],
            name=data["name"],
            body_system=BodySystem(data["body_system"]),
            location=data["location"],
            function=data["function"],
            related_structures=data.get("related_structures", []),
            clinical_significance=data.get("clinical_significance", ""),
            latin_name=data.get("latin_name", ""),
            difficulty=data.get("difficulty", 1),
            proficiency=MedicalProficiency(data.get("proficiency", "novice")),
            total_reviews=data.get("total_reviews", 0),
            correct_reviews=data.get("correct_reviews", 0),
        )


@dataclass
class DiseaseCondition:
    """A disease or medical condition."""
    condition_id: str
    name: str
    icd_code: str = ""
    description: str = ""
    body_system: Optional[BodySystem] = None
    
    # Clinical information
    symptoms: List[str] = field(default_factory=list)
    causes: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    diagnostic_criteria: List[str] = field(default_factory=list)
    treatments: List[str] = field(default_factory=list)
    
    # Learning context
    differential_diagnosis: List[str] = field(default_factory=list)
    complications: List[str] = field(default_factory=list)
    prognosis: str = ""
    
    difficulty: int = 1
    prevalence: str = ""  # "common", "uncommon", "rare"
    
    # Learning metrics
    proficiency: MedicalProficiency = MedicalProficiency.NOVICE
    total_reviews: int = 0
    correct_reviews: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "icd_code": self.icd_code,
            "description": self.description,
            "body_system": self.body_system.value if self.body_system else None,
            "symptoms": self.symptoms,
            "causes": self.causes,
            "risk_factors": self.risk_factors,
            "diagnostic_criteria": self.diagnostic_criteria,
            "treatments": self.treatments,
            "differential_diagnosis": self.differential_diagnosis,
            "complications": self.complications,
            "prognosis": self.prognosis,
            "difficulty": self.difficulty,
            "prevalence": self.prevalence,
            "proficiency": self.proficiency.value,
            "total_reviews": self.total_reviews,
            "correct_reviews": self.correct_reviews,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiseaseCondition":
        """Deserialize from dictionary."""
        return cls(
            condition_id=data["condition_id"],
            name=data["name"],
            icd_code=data.get("icd_code", ""),
            description=data.get("description", ""),
            body_system=BodySystem(data["body_system"]) if data.get("body_system") else None,
            symptoms=data.get("symptoms", []),
            causes=data.get("causes", []),
            risk_factors=data.get("risk_factors", []),
            diagnostic_criteria=data.get("diagnostic_criteria", []),
            treatments=data.get("treatments", []),
            differential_diagnosis=data.get("differential_diagnosis", []),
            complications=data.get("complications", []),
            prognosis=data.get("prognosis", ""),
            difficulty=data.get("difficulty", 1),
            prevalence=data.get("prevalence", ""),
            proficiency=MedicalProficiency(data.get("proficiency", "novice")),
            total_reviews=data.get("total_reviews", 0),
            correct_reviews=data.get("correct_reviews", 0),
        )


@dataclass
class Drug:
    """A medication or drug."""
    drug_id: str
    name: str
    generic_name: str
    drug_class: DrugClass
    mechanism_of_action: str = ""
    indications: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    interactions: List[str] = field(default_factory=list)
    dosing: str = ""
    routes: List[str] = field(default_factory=list)
    
    difficulty: int = 1
    is_controlled: bool = False
    pregnancy_category: str = ""
    
    # Learning metrics
    proficiency: MedicalProficiency = MedicalProficiency.NOVICE
    total_reviews: int = 0
    correct_reviews: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "drug_id": self.drug_id,
            "name": self.name,
            "generic_name": self.generic_name,
            "drug_class": self.drug_class.value,
            "mechanism_of_action": self.mechanism_of_action,
            "indications": self.indications,
            "contraindications": self.contraindications,
            "side_effects": self.side_effects,
            "interactions": self.interactions,
            "dosing": self.dosing,
            "routes": self.routes,
            "difficulty": self.difficulty,
            "is_controlled": self.is_controlled,
            "pregnancy_category": self.pregnancy_category,
            "proficiency": self.proficiency.value,
            "total_reviews": self.total_reviews,
            "correct_reviews": self.correct_reviews,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Drug":
        """Deserialize from dictionary."""
        return cls(
            drug_id=data["drug_id"],
            name=data["name"],
            generic_name=data["generic_name"],
            drug_class=DrugClass(data["drug_class"]),
            mechanism_of_action=data.get("mechanism_of_action", ""),
            indications=data.get("indications", []),
            contraindications=data.get("contraindications", []),
            side_effects=data.get("side_effects", []),
            interactions=data.get("interactions", []),
            dosing=data.get("dosing", ""),
            routes=data.get("routes", []),
            difficulty=data.get("difficulty", 1),
            is_controlled=data.get("is_controlled", False),
            pregnancy_category=data.get("pregnancy_category", ""),
            proficiency=MedicalProficiency(data.get("proficiency", "novice")),
            total_reviews=data.get("total_reviews", 0),
            correct_reviews=data.get("correct_reviews", 0),
        )


# ============================================================================
# MEDICAL DOMAIN CLASS
# ============================================================================

class MedicalDomain:
    """
    Medical knowledge domain for RPA.
    
    Features:
    - Medical terminology with etymology
    - Anatomy by body system
    - Disease and condition knowledge
    - Pharmacology basics
    - Clinical reasoning patterns
    - Spaced repetition for retention
    """
    
    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """Initialize medical domain."""
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()
        
        # Knowledge stores
        self._terms: Dict[str, MedicalTerm] = {}
        self._structures: Dict[str, AnatomyStructure] = {}
        self._conditions: Dict[str, DiseaseCondition] = {}
        self._drugs: Dict[str, Drug] = {}
        
        # Review history
        self._review_history: List[Dict[str, Any]] = []
        
        # Initialize with foundational medical knowledge
        self._initialize_terminology()
        self._initialize_anatomy()
        self._initialize_conditions()
        self._initialize_drugs()
    
    def _initialize_terminology(self) -> None:
        """Initialize with common medical terminology."""
        # Common prefixes
        prefixes = [
            ("cardio-", "heart", "Cardiology, cardiovascular"),
            ("neuro-", "nerve, nervous system", "Neurology, neuroscience"),
            ("gastro-", "stomach", "Gastritis, gastrointestinal"),
            ("hepato-", "liver", "Hepatology, hepatitis"),
            ("nephro-", "kidney", "Nephrology, nephritis"),
            ("pulmo-", "lung", "Pulmonology, pulmonary"),
            ("dermato-", "skin", "Dermatology, dermatitis"),
            ("osteo-", "bone", "Osteoporosis, osteopathy"),
            ("hemo-", "blood", "Hematology, hemorrhage"),
            ("cyto-", "cell", "Cytology, cytoplasm"),
            ("endo-", "within, inner", "Endocrine, endoscopy"),
            ("exo-", "outside, outer", "Exocrine, exoskeleton"),
            ("hyper-", "above, excessive", "Hypertension, hyperglycemia"),
            ("hypo-", "below, deficient", "Hypotension, hypoglycemia"),
            ("tachy-", "fast, rapid", "Tachycardia, tachypnea"),
            ("brady-", "slow", "Bradycardia, bradypnea"),
            ("dys-", "difficult, painful, abnormal", "Dyspnea, dysphagia"),
            ("a-, an-", "without, absence of", "Anemia, aseptic"),
            ("anti-", "against", "Antibiotic, antibody"),
            ("poly-", "many, much", "Polyuria, polycystic"),
            ("oligo-", "few, little", "Oliguria, oligomenorrhea"),
            ("pan-", "all, entire", "Pancreatitis, pandemic"),
        ]
        
        for prefix, meaning, examples in prefixes:
            term = MedicalTerm(
                term_id=f"term_prefix_{uuid.uuid4().hex[:8]}",
                term=prefix,
                definition=meaning,
                category=MedicalCategory.TERMINOLOGY,
                prefix=prefix,
                etymology=f"Prefix meaning '{meaning}'",
                examples=examples.split(", "),
                difficulty=1,
            )
            self._terms[term.term_id] = term
        
        # Common suffixes
        suffixes = [
            ("-itis", "inflammation", "Appendicitis, arthritis, bronchitis"),
            ("-osis", "condition, disease state", "Osteoporosis, thrombosis"),
            ("-emia", "blood condition", "Anemia, leukemia, septicemia"),
            ("-pathy", "disease, disorder", "Neuropathy, cardiomyopathy"),
            ("-ectomy", "surgical removal", "Appendectomy, tonsillectomy"),
            ("-otomy", "surgical incision", "Tracheotomy, laparotomy"),
            ("-scopy", "visual examination", "Endoscopy, colonoscopy"),
            ("-gram", "record, image", "Electrocardiogram, angiogram"),
            ("-ology", "study of", "Cardiology, neurology"),
            ("-algia", "pain", "Neuralgia, myalgia"),
            ("-dynia", "pain", "Gastrodynia, otodynia"),
            ("-plasty", "surgical repair", "Angioplasty, rhinoplasty"),
            ("-stomy", "opening, creation of opening", "Colostomy, tracheostomy"),
            ("-penia", "deficiency", "Leukopenia, thrombocytopenia"),
        ]
        
        for suffix, meaning, examples in suffixes:
            term = MedicalTerm(
                term_id=f"term_suffix_{uuid.uuid4().hex[:8]}",
                term=suffix,
                definition=meaning,
                category=MedicalCategory.TERMINOLOGY,
                suffix=suffix,
                etymology=f"Suffix meaning '{meaning}'",
                examples=examples.split(", "),
                difficulty=1,
            )
            self._terms[term.term_id] = term
        
        # Common roots
        roots = [
            ("cardi", "heart", "Cardiac, cardiologist, cardiomyopathy"),
            ("neur", "nerve", "Neural, neurologist, neuropathy"),
            ("gastr", "stomach", "Gastric, gastrologist, gastrectomy"),
            ("hepat", "liver", "Hepatic, hepatology, hepatoma"),
            ("nephr", "kidney", "Nephric, nephrologist, nephrectomy"),
            ("ren", "kidney", "Renal, adrenaline"),
            ("pulmon", "lung", "Pulmonary, pulmonologist"),
            ("pneum", "lung, air", "Pneumonia, pneumothorax"),
            ("dermat", "skin", "Dermal, dermatologist, dermatitis"),
            ("oste", "bone", "Osteal, osteopath, osteomyelitis"),
            ("hem, hemat", "blood", "Hemoglobin, hematoma, hematology"),
            ("cyt", "cell", "Cytoplasm, cytology, leukocyte"),
            ("arthr", "joint", "Arthritis, arthroscopy, arthropathy"),
            ("my", "muscle", "Myocardium, myalgia, myopathy"),
            ("cephal", "head", "Cephalic, encephalitis, hydrocephalus"),
            ("cran", "skull", "Cranial, craniotomy"),
            ("enter", "intestine", "Enteritis, enterocolitis"),
            ("col", "colon", "Colitis, colectomy, colonoscopy"),
            ("ur", "urine, urinary tract", "Urology, urethritis, urinalysis"),
            ("vas", "vessel", "Vascular, vasectomy, vasoconstriction"),
        ]
        
        for root, meaning, examples in roots:
            term = MedicalTerm(
                term_id=f"term_root_{uuid.uuid4().hex[:8]}",
                term=root,
                definition=meaning,
                category=MedicalCategory.TERMINOLOGY,
                root=root,
                etymology=f"Root meaning '{meaning}'",
                examples=examples.split(", "),
                difficulty=1,
            )
            self._terms[term.term_id] = term
    
    def _initialize_anatomy(self) -> None:
        """Initialize with foundational anatomy knowledge."""
        # Cardiovascular system
        cv_structures = [
            ("Heart", BodySystem.CARDIOVASCULAR, "Mediastinum, between lungs", 
             "Pumps blood throughout the body", 
             ["Aorta", "Vena cava", "Pulmonary arteries"],
             "Cardiac arrest, myocardial infarction", "Cor"),
            ("Aorta", BodySystem.CARDIOVASCULAR, "Arises from left ventricle",
             "Main artery distributing oxygenated blood",
             ["Heart", "Carotid arteries", "Renal arteries"],
             "Aortic aneurysm, aortic dissection"),
            ("Left ventricle", BodySystem.CARDIOVASCULAR, "Inferior left heart",
             "Pumps oxygenated blood to systemic circulation",
             ["Left atrium", "Aortic valve", "Mitral valve"],
             "Left ventricular hypertrophy"),
            ("Right atrium", BodySystem.CARDIOVASCULAR, "Upper right heart",
             "Receives deoxygenated blood from body",
             ["Superior vena cava", "Tricuspid valve"],
             "Right atrial enlargement"),
        ]
        
        for name, system, location, function, related, clinical, *latin in cv_structures:
            structure = AnatomyStructure(
                structure_id=f"anat_{uuid.uuid4().hex[:8]}",
                name=name,
                body_system=system,
                location=location,
                function=function,
                related_structures=related,
                clinical_significance=clinical,
                latin_name=latin[0] if latin else "",
                difficulty=1,
            )
            self._structures[structure.structure_id] = structure
        
        # Respiratory system
        resp_structures = [
            ("Lungs", BodySystem.RESPIRATORY, "Thoracic cavity",
             "Gas exchange - oxygen in, carbon dioxide out",
             ["Trachea", "Bronchi", "Diaphragm"],
             "Pneumonia, COPD, lung cancer", "Pulmo"),
            ("Trachea", BodySystem.RESPIRATORY, "Neck to thorax, anterior to esophagus",
             "Air passage to lungs, filters inhaled particles",
             ["Larynx", "Bronchi", "Esophagus"],
             "Tracheitis, tracheal stenosis"),
            ("Diaphragm", BodySystem.RESPIRATORY, "Between thoracic and abdominal cavities",
             "Main muscle of respiration",
             ["Lungs", "Liver", "Stomach"],
             "Diaphragmatic hernia, phrenic nerve injury"),
        ]
        
        for name, system, location, function, related, clinical, *latin in resp_structures:
            structure = AnatomyStructure(
                structure_id=f"anat_{uuid.uuid4().hex[:8]}",
                name=name,
                body_system=system,
                location=location,
                function=function,
                related_structures=related,
                clinical_significance=clinical,
                latin_name=latin[0] if latin else "",
                difficulty=1,
            )
            self._structures[structure.structure_id] = structure
        
        # Nervous system
        neuro_structures = [
            ("Brain", BodySystem.NERVOUS, "Cranial cavity",
             "Control center for body functions, thought, memory",
             ["Spinal cord", "Cranial nerves", "Meninges"],
             "Stroke, traumatic brain injury, dementia", "Cerebrum"),
            ("Spinal cord", BodySystem.NERVOUS, "Vertebral canal",
             "Conduit for signals between brain and body, reflexes",
             ["Brain", "Spinal nerves", "Vertebrae"],
             "Spinal cord injury, myelopathy"),
            ("Peripheral nerves", BodySystem.NERVOUS, "Throughout body",
             "Transmit signals between CNS and body",
             ["Spinal cord", "Muscles", "Skin"],
             "Peripheral neuropathy, nerve injury"),
        ]
        
        for name, system, location, function, related, clinical, *latin in neuro_structures:
            structure = AnatomyStructure(
                structure_id=f"anat_{uuid.uuid4().hex[:8]}",
                name=name,
                body_system=system,
                location=location,
                function=function,
                related_structures=related,
                clinical_significance=clinical,
                latin_name=latin[0] if latin else "",
                difficulty=2,
            )
            self._structures[structure.structure_id] = structure
    
    def _initialize_conditions(self) -> None:
        """Initialize with common medical conditions."""
        conditions = [
            # Cardiovascular
            ("Hypertension", BodySystem.CARDIOVASCULAR, "I10",
             ["Headache", "Dizziness", "Blurred vision"],
             ["Genetics", "Obesity", "Salt intake", "Stress"],
             ["Heart disease", "Stroke", "Kidney damage"],
             "High blood pressure - BP > 130/80 mmHg",
             "Lifestyle changes, antihypertensives", "common", 1),
            
            ("Myocardial infarction", BodySystem.CARDIOVASCULAR, "I21",
             ["Chest pain", "Shortness of breath", "Nausea", "Diaphoresis"],
             ["Coronary artery disease", "Hypertension", "Smoking", "Diabetes"],
             ["Heart failure", "Arrhythmias", "Death"],
             "Heart attack - blocked coronary artery",
             "Aspirin, thrombolytics, PCI, CABG", "common", 2),
            
            # Respiratory
            ("Pneumonia", BodySystem.RESPIRATORY, "J18",
             ["Cough", "Fever", "Dyspnea", "Chest pain"],
             ["Bacteria", "Viruses", "Fungi"],
             ["Respiratory failure", "Sepsis", "Lung abscess"],
             "Infection of lung parenchyma",
             "Antibiotics, supportive care", "common", 1),
            
            ("Asthma", BodySystem.RESPIRATORY, "J45",
             ["Wheezing", "Shortness of breath", "Cough", "Chest tightness"],
             ["Allergens", "Irritants", "Exercise", "Genetics"],
             ["Status asthmaticus", "Respiratory failure"],
             "Chronic inflammatory airway disease",
             "Bronchodilators, inhaled corticosteroids", "common", 1),
            
            # Nervous
            ("Stroke", BodySystem.NERVOUS, "I63",
             ["Sudden weakness", "Speech difficulty", "Facial droop", "Vision changes"],
             ["Ischemia", "Hemorrhage", "Hypertension", "Atrial fibrillation"],
             ["Permanent disability", "Death"],
             "Brain injury from interrupted blood supply",
             "Thrombolytics, thrombectomy, supportive care", "common", 2),
            
            # Endocrine
            ("Diabetes mellitus type 2", BodySystem.ENDOCRINE, "E11",
             ["Polyuria", "Polydipsia", "Weight loss", "Fatigue"],
             ["Insulin resistance", "Obesity", "Genetics", "Sedentary lifestyle"],
             ["Neuropathy", "Retinopathy", "Nephropathy", "Cardiovascular disease"],
             "Metabolic disorder with elevated blood glucose",
             "Diet, exercise, oral medications, insulin", "common", 1),
        ]
        
        for name, system, icd, symptoms, causes, complications, desc, treatments, prevalence, difficulty in conditions:
            condition = DiseaseCondition(
                condition_id=f"cond_{uuid.uuid4().hex[:8]}",
                name=name,
                icd_code=icd,
                description=desc,
                body_system=system,
                symptoms=symptoms,
                causes=causes,
                complications=complications,
                treatments=treatments.split(", "),
                prevalence=prevalence,
                difficulty=difficulty,
            )
            self._conditions[condition.condition_id] = condition
    
    def _initialize_drugs(self) -> None:
        """Initialize with common medications."""
        drugs = [
            # Analgesics
            ("Acetaminophen", "Paracetamol", DrugClass.ANALGESIC,
             "Inhibits COX enzymes in CNS",
             ["Pain", "Fever"],
             ["Liver disease", "Alcoholism"],
             ["Liver toxicity", "Nausea"],
             "325-650mg q4-6h, max 4g/day",
             ["Oral", "Rectal", "IV"], 1),
            
            ("Ibuprofen", "Ibuprofen", DrugClass.ANTI_INFLAMMATORY,
             "Inhibits COX-1 and COX-2, reduces prostaglandins",
             ["Pain", "Inflammation", "Fever", "Arthritis"],
             ["Active bleeding", "Peptic ulcer", "Kidney disease"],
             ["GI bleeding", "Nausea", "Dizziness"],
             "200-800mg q6-8h, max 3.2g/day",
             ["Oral", "IV", "Topical"], 1),
            
            # Antibiotics
            ("Amoxicillin", "Amoxicillin", DrugClass.ANTIBIOTIC,
             "Inhibits bacterial cell wall synthesis",
             ["Bacterial infections", "Otitis media", "Sinusitis", "UTI"],
             ["Penicillin allergy"],
             ["Rash", "Diarrhea", "Nausea"],
             "250-500mg q8h",
             ["Oral"], 1),
            
            ("Azithromycin", "Azithromycin", DrugClass.ANTIBIOTIC,
             "Inhibits bacterial protein synthesis",
             ["Respiratory infections", "Skin infections", "STIs"],
             ["Macrolide allergy", "QT prolongation"],
             ["GI upset", "Diarrhea", "Arrhythmia"],
             "500mg day 1, then 250mg days 2-5",
             ["Oral", "IV"], 1),
            
            # Cardiovascular
            ("Lisinopril", "Lisinopril", DrugClass.CARDIOVASCULAR,
             "ACE inhibitor - blocks angiotensin II formation",
             ["Hypertension", "Heart failure", "Post-MI"],
             ["Angioedema", "Pregnancy", "Bilateral renal stenosis"],
             ["Cough", "Hyperkalemia", "Angioedema"],
             "10-40mg daily",
             ["Oral"], 2),
            
            ("Metoprolol", "Metoprolol", DrugClass.CARDIOVASCULAR,
             "Beta-1 selective blocker - reduces heart rate and contractility",
             ["Hypertension", "Angina", "Heart failure", "Post-MI"],
             ["Severe bradycardia", "Heart block", "Decompensated HF"],
             ["Fatigue", "Bradycardia", "Hypotension"],
             "25-200mg daily",
             ["Oral", "IV"], 2),
            
            # Respiratory
            ("Albuterol", "Salbutamol", DrugClass.RESPIRATORY,
             "Beta-2 agonist - bronchodilation",
             ["Asthma", "COPD", "Bronchospasm"],
             ["Hypersensitivity"],
             ["Tremor", "Tachycardia", "Nervousness"],
             "1-2 puffs q4-6h prn",
             ["Inhaler", "Nebulizer", "Oral"], 1),
        ]
        
        for brand, generic, drug_class, moa, indications, contraindications, side_effects, dosing, routes, difficulty in drugs:
            drug = Drug(
                drug_id=f"drug_{uuid.uuid4().hex[:8]}",
                name=brand,
                generic_name=generic,
                drug_class=drug_class,
                mechanism_of_action=moa,
                indications=indications,
                contraindications=contraindications,
                side_effects=side_effects,
                dosing=dosing,
                routes=routes,
                difficulty=difficulty,
            )
            self._drugs[drug.drug_id] = drug
    
    # ========================================================================
    # TERM MANAGEMENT
    # ========================================================================
    
    def add_term(
        self,
        term: str,
        definition: str,
        category: MedicalCategory,
        body_system: Optional[BodySystem] = None,
        examples: Optional[List[str]] = None,
        root: str = "",
        prefix: str = "",
        suffix: str = "",
        difficulty: int = 1,
    ) -> MedicalTerm:
        """Add a new medical term."""
        new_term = MedicalTerm(
            term_id=f"term_{uuid.uuid4().hex[:8]}",
            term=term,
            definition=definition,
            category=category,
            body_system=body_system,
            examples=examples or [],
            root=root,
            prefix=prefix,
            suffix=suffix,
            difficulty=difficulty,
        )
        self._terms[new_term.term_id] = new_term
        return new_term
    
    def get_term(self, term_id: str) -> Optional[MedicalTerm]:
        """Get a medical term by ID."""
        return self._terms.get(term_id)
    
    def search_terms(self, query: str) -> List[MedicalTerm]:
        """Search terms by text."""
        query_lower = query.lower()
        return [
            t for t in self._terms.values()
            if query_lower in t.term.lower() or query_lower in t.definition.lower()
        ]
    
    def get_terms_by_category(self, category: MedicalCategory) -> List[MedicalTerm]:
        """Get terms by category."""
        return [t for t in self._terms.values() if t.category == category]
    
    def get_terms_by_body_system(self, system: BodySystem) -> List[MedicalTerm]:
        """Get terms related to a body system."""
        return [t for t in self._terms.values() if t.body_system == system]
    
    # ========================================================================
    # ANATOMY MANAGEMENT
    # ========================================================================
    
    def add_structure(
        self,
        name: str,
        body_system: BodySystem,
        location: str,
        function: str,
        related_structures: Optional[List[str]] = None,
        clinical_significance: str = "",
        difficulty: int = 1,
    ) -> AnatomyStructure:
        """Add a new anatomical structure."""
        structure = AnatomyStructure(
            structure_id=f"anat_{uuid.uuid4().hex[:8]}",
            name=name,
            body_system=body_system,
            location=location,
            function=function,
            related_structures=related_structures or [],
            clinical_significance=clinical_significance,
            difficulty=difficulty,
        )
        self._structures[structure.structure_id] = structure
        return structure
    
    def get_structure(self, structure_id: str) -> Optional[AnatomyStructure]:
        """Get an anatomical structure by ID."""
        return self._structures.get(structure_id)
    
    def get_structures_by_system(self, system: BodySystem) -> List[AnatomyStructure]:
        """Get structures by body system."""
        return [s for s in self._structures.values() if s.body_system == system]
    
    # ========================================================================
    # CONDITION MANAGEMENT
    # ========================================================================
    
    def add_condition(
        self,
        name: str,
        body_system: Optional[BodySystem] = None,
        icd_code: str = "",
        description: str = "",
        symptoms: Optional[List[str]] = None,
        causes: Optional[List[str]] = None,
        treatments: Optional[List[str]] = None,
        difficulty: int = 1,
    ) -> DiseaseCondition:
        """Add a new disease condition."""
        condition = DiseaseCondition(
            condition_id=f"cond_{uuid.uuid4().hex[:8]}",
            name=name,
            body_system=body_system,
            icd_code=icd_code,
            description=description,
            symptoms=symptoms or [],
            causes=causes or [],
            treatments=treatments or [],
            difficulty=difficulty,
        )
        self._conditions[condition.condition_id] = condition
        return condition
    
    def get_condition(self, condition_id: str) -> Optional[DiseaseCondition]:
        """Get a condition by ID."""
        return self._conditions.get(condition_id)
    
    def search_conditions(self, query: str) -> List[DiseaseCondition]:
        """Search conditions by name or description."""
        query_lower = query.lower()
        return [
            c for c in self._conditions.values()
            if query_lower in c.name.lower() or query_lower in c.description.lower()
        ]
    
    def get_conditions_by_system(self, system: BodySystem) -> List[DiseaseCondition]:
        """Get conditions by body system."""
        return [c for c in self._conditions.values() if c.body_system == system]
    
    # ========================================================================
    # DRUG MANAGEMENT
    # ========================================================================
    
    def add_drug(
        self,
        name: str,
        generic_name: str,
        drug_class: DrugClass,
        mechanism_of_action: str = "",
        indications: Optional[List[str]] = None,
        contraindications: Optional[List[str]] = None,
        side_effects: Optional[List[str]] = None,
        difficulty: int = 1,
    ) -> Drug:
        """Add a new drug."""
        drug = Drug(
            drug_id=f"drug_{uuid.uuid4().hex[:8]}",
            name=name,
            generic_name=generic_name,
            drug_class=drug_class,
            mechanism_of_action=mechanism_of_action,
            indications=indications or [],
            contraindications=contraindications or [],
            side_effects=side_effects or [],
            difficulty=difficulty,
        )
        self._drugs[drug.drug_id] = drug
        return drug
    
    def get_drug(self, drug_id: str) -> Optional[Drug]:
        """Get a drug by ID."""
        return self._drugs.get(drug_id)
    
    def search_drugs(self, query: str) -> List[Drug]:
        """Search drugs by name or generic name."""
        query_lower = query.lower()
        return [
            d for d in self._drugs.values()
            if query_lower in d.name.lower() or query_lower in d.generic_name.lower()
        ]
    
    def get_drugs_by_class(self, drug_class: DrugClass) -> List[Drug]:
        """Get drugs by classification."""
        return [d for d in self._drugs.values() if d.drug_class == drug_class]
    
    # ========================================================================
    # EXERCISE GENERATION
    # ========================================================================
    
    def generate_term_exercise(
        self,
        term: Optional[MedicalTerm] = None,
        exercise_type: str = "multiple_choice",
    ) -> Dict[str, Any]:
        """Generate a terminology exercise."""
        if term is None:
            terms = list(self._terms.values())
            if not terms:
                return {"error": "No terms available"}
            term = random.choice(terms)
        
        if exercise_type == "multiple_choice":
            return self._generate_term_mc(term)
        elif exercise_type == "etymology":
            return self._generate_etymology_exercise(term)
        elif exercise_type == "build_term":
            return self._generate_build_term_exercise(term)
        else:
            return self._generate_term_mc(term)
    
    def _generate_term_mc(self, term: MedicalTerm) -> Dict[str, Any]:
        """Generate multiple choice for terminology."""
        # Get distractors
        all_definitions = [t.definition for t in self._terms.values() if t.term_id != term.term_id]
        distractors = random.sample(all_definitions, min(3, len(all_definitions)))
        
        options = [term.definition] + distractors
        random.shuffle(options)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "multiple_choice",
            "question": f"What does the medical term '{term.term}' mean?",
            "options": options,
            "correct_answer": term.definition,
            "correct_index": options.index(term.definition),
            "explanation": term.etymology or term.definition,
            "difficulty": term.difficulty,
        }
    
    def _generate_etymology_exercise(self, term: MedicalTerm) -> Dict[str, Any]:
        """Generate etymology breakdown exercise."""
        if not term.root and not term.prefix and not term.suffix:
            return self._generate_term_mc(term)
        
        parts = []
        if term.prefix:
            parts.append(("prefix", term.prefix))
        if term.root:
            parts.append(("root", term.root))
        if term.suffix:
            parts.append(("suffix", term.suffix))
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "etymology",
            "question": f"Break down the medical term '{term.term}' and explain its meaning:",
            "term": term.term,
            "definition": term.definition,
            "parts": parts,
            "explanation": term.etymology,
            "difficulty": term.difficulty,
        }
    
    def _generate_build_term_exercise(self, term: MedicalTerm) -> Dict[str, Any]:
        """Generate term building exercise."""
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "build_term",
            "question": f"Build a medical term that means: '{term.definition}'",
            "answer": term.term,
            "hints": {
                "prefix": term.prefix if term.prefix else None,
                "root": term.root if term.root else None,
                "suffix": term.suffix if term.suffix else None,
            },
            "difficulty": term.difficulty,
        }
    
    def generate_anatomy_exercise(
        self,
        structure: Optional[AnatomyStructure] = None,
        exercise_type: str = "multiple_choice",
    ) -> Dict[str, Any]:
        """Generate an anatomy exercise."""
        if structure is None:
            structures = list(self._structures.values())
            if not structures:
                return {"error": "No structures available"}
            structure = random.choice(structures)
        
        # Generate multiple choice for function
        all_functions = [s.function for s in self._structures.values() if s.structure_id != structure.structure_id]
        distractors = random.sample(all_functions, min(3, len(all_functions)))
        
        options = [structure.function] + distractors
        random.shuffle(options)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "anatomy_function",
            "question": f"What is the function of the {structure.name}?",
            "body_system": structure.body_system.value,
            "options": options,
            "correct_answer": structure.function,
            "correct_index": options.index(structure.function),
            "location": structure.location,
            "difficulty": structure.difficulty,
        }
    
    def generate_diagnosis_exercise(
        self,
        condition: Optional[DiseaseCondition] = None,
    ) -> Dict[str, Any]:
        """Generate a clinical diagnosis exercise."""
        if condition is None:
            conditions = list(self._conditions.values())
            if not conditions:
                return {"error": "No conditions available"}
            condition = random.choice(conditions)
        
        # Generate case-based question
        symptom_text = ", ".join(random.sample(condition.symptoms, min(3, len(condition.symptoms))))
        
        # Get distractors (other conditions)
        other_conditions = [c for c in self._conditions.values() if c.condition_id != condition.condition_id]
        distractors = random.sample(other_conditions, min(3, len(other_conditions)))
        
        options = [condition.name] + [d.name for d in distractors]
        random.shuffle(options)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "diagnosis",
            "question": f"A patient presents with: {symptom_text}. What is the most likely diagnosis?",
            "options": options,
            "correct_answer": condition.name,
            "correct_index": options.index(condition.name),
            "symptoms": condition.symptoms,
            "explanation": condition.description,
            "body_system": condition.body_system.value if condition.body_system else None,
            "difficulty": condition.difficulty,
        }
    
    def generate_drug_exercise(
        self,
        drug: Optional[Drug] = None,
        exercise_type: str = "indication",
    ) -> Dict[str, Any]:
        """Generate a pharmacology exercise."""
        if drug is None:
            drugs = list(self._drugs.values())
            if not drugs:
                return {"error": "No drugs available"}
            drug = random.choice(drugs)
        
        if exercise_type == "indication":
            return self._generate_indication_exercise(drug)
        elif exercise_type == "side_effects":
            return self._generate_side_effects_exercise(drug)
        elif exercise_type == "mechanism":
            return self._generate_mechanism_exercise(drug)
        else:
            return self._generate_indication_exercise(drug)
    
    def _generate_indication_exercise(self, drug: Drug) -> Dict[str, Any]:
        """Generate drug indication exercise."""
        # Get other drugs' indications as distractors
        other_drugs = [d for d in self._drugs.values() if d.drug_id != drug.drug_id]
        all_indications = []
        for d in other_drugs:
            all_indications.extend(d.indications)
        
        distractors = random.sample(all_indications, min(3, len(all_indications)))
        correct_indication = random.choice(drug.indications)
        
        options = [correct_indication] + distractors
        random.shuffle(options)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "drug_indication",
            "question": f"What is {drug.name} ({drug.generic_name}) used to treat?",
            "drug_class": drug.drug_class.value,
            "options": options,
            "correct_answer": correct_indication,
            "correct_index": options.index(correct_indication),
            "all_indications": drug.indications,
            "difficulty": drug.difficulty,
        }
    
    def _generate_side_effects_exercise(self, drug: Drug) -> Dict[str, Any]:
        """Generate side effects exercise."""
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "side_effects",
            "question": f"What are common side effects of {drug.name}?",
            "drug_name": drug.name,
            "side_effects": drug.side_effects,
            "difficulty": drug.difficulty,
        }
    
    def _generate_mechanism_exercise(self, drug: Drug) -> Dict[str, Any]:
        """Generate mechanism of action exercise."""
        if not drug.mechanism_of_action:
            return self._generate_indication_exercise(drug)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "mechanism",
            "question": f"How does {drug.name} work?",
            "drug_name": drug.name,
            "mechanism": drug.mechanism_of_action,
            "drug_class": drug.drug_class.value,
            "difficulty": drug.difficulty,
        }
    
    # ========================================================================
    # REVIEW AND SPACED REPETITION
    # ========================================================================
    
    def review_term(
        self,
        term_id: str,
        quality: int,
        response: str = "",
        time_spent: float = 0.0,
    ) -> Dict[str, Any]:
        """Review a medical term using SM-2 algorithm."""
        term = self._terms.get(term_id)
        if not term:
            return {"error": f"Term not found: {term_id}"}
        
        now = datetime.now()
        
        # SM-2 Algorithm
        if quality >= 3:
            if term.repetitions == 0:
                term.interval = 1
            elif term.repetitions == 1:
                term.interval = 6
            else:
                term.interval = math.ceil(term.interval * term.ease_factor)
            term.repetitions += 1
            term.correct_reviews += 1
        else:
            term.repetitions = 0
            term.interval = 1
        
        # Update ease factor
        term.ease_factor = max(
            1.3,
            term.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        )
        
        # Update proficiency
        self._update_proficiency(term)
        
        term.next_review = now + timedelta(days=term.interval)
        term.last_review = now
        term.total_reviews += 1
        
        result = {
            "term_id": term_id,
            "correct": quality >= 3,
            "quality": quality,
            "new_proficiency": term.proficiency.value,
            "next_review": term.next_review.isoformat(),
            "interval": term.interval,
        }
        
        self._review_history.append(result)
        
        # Log to episodic memory
        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id="medicine",
            data={
                "action": "term_review",
                "term": term.term,
                "quality": quality,
                "correct": quality >= 3,
            },
        )
        
        return result
    
    def _update_proficiency(self, item: Any) -> None:
        """Update proficiency level based on learning progress."""
        accuracy = item.correct_reviews / max(item.total_reviews, 1)
        
        if item.repetitions >= 5 and accuracy >= 0.9:
            item.proficiency = MedicalProficiency.EXPERT
        elif item.repetitions >= 3 and accuracy >= 0.8:
            item.proficiency = MedicalProficiency.ADVANCED
        elif item.repetitions >= 2 and accuracy >= 0.7:
            item.proficiency = MedicalProficiency.INTERMEDIATE
        elif item.repetitions >= 1 or item.total_reviews >= 1:
            item.proficiency = MedicalProficiency.BEGINNER
        else:
            item.proficiency = MedicalProficiency.NOVICE
    
    def get_due_reviews(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get items due for review."""
        now = datetime.now()
        due = []
        
        # Check terms
        for term in self._terms.values():
            if term.next_review is None or term.next_review <= now:
                due.append({
                    "type": "term",
                    "id": term.term_id,
                    "item": term.term,
                    "proficiency": term.proficiency.value,
                })
        
        # Sort by proficiency (novice first)
        proficiency_order = [p.value for p in MedicalProficiency]
        due.sort(key=lambda x: proficiency_order.index(x["proficiency"]))
        
        return due[:limit]
    
    # ========================================================================
    # STATISTICS AND EXPORT
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get medical domain learning statistics."""
        term_stats = {
            "total": len(self._terms),
            "by_proficiency": {},
        }
        for level in MedicalProficiency:
            term_stats["by_proficiency"][level.value] = sum(
                1 for t in self._terms.values() if t.proficiency == level
            )
        
        structure_stats = {
            "total": len(self._structures),
            "by_system": {},
        }
        for system in BodySystem:
            structure_stats["by_system"][system.value] = sum(
                1 for s in self._structures.values() if s.body_system == system
            )
        
        condition_stats = {
            "total": len(self._conditions),
        }
        
        drug_stats = {
            "total": len(self._drugs),
            "by_class": {},
        }
        for drug_class in DrugClass:
            drug_stats["by_class"][drug_class.value] = sum(
                1 for d in self._drugs.values() if d.drug_class == drug_class
            )
        
        return {
            "terms": term_stats,
            "structures": structure_stats,
            "conditions": condition_stats,
            "drugs": drug_stats,
            "total_reviews": len(self._review_history),
        }
    
    def export_progress(self) -> Dict[str, Any]:
        """Export learning progress for persistence."""
        return {
            "terms": {k: v.to_dict() for k, v in self._terms.items()},
            "structures": {k: v.to_dict() for k, v in self._structures.items()},
            "conditions": {k: v.to_dict() for k, v in self._conditions.items()},
            "drugs": {k: v.to_dict() for k, v in self._drugs.items()},
            "review_history": self._review_history,
            "statistics": self.get_statistics(),
        }
    
    def import_progress(self, data: Dict[str, Any]) -> None:
        """Import learning progress from persistence."""
        if "terms" in data:
            for term_id, term_data in data["terms"].items():
                self._terms[term_id] = MedicalTerm.from_dict(term_data)
        
        if "structures" in data:
            for struct_id, struct_data in data["structures"].items():
                self._structures[struct_id] = AnatomyStructure.from_dict(struct_data)
        
        if "conditions" in data:
            for cond_id, cond_data in data["conditions"].items():
                self._conditions[cond_id] = DiseaseCondition.from_dict(cond_data)
        
        if "drugs" in data:
            for drug_id, drug_data in data["drugs"].items():
                self._drugs[drug_id] = Drug.from_dict(drug_data)
        
        if "review_history" in data:
            self._review_history = data["review_history"]
    
    def save_patterns_to_ltm(self) -> int:
        """Save learned medical patterns to Long-Term Memory."""
        from rpa.core.node import Node, NodeType
        
        count = 0
        
        # Save terms as patterns
        for term in self._terms.values():
            node = Node(
                node_id=f"med_term:{term.term_id}",
                label=term.term,
                node_type=NodeType.CONCEPT,
                content=term.definition,
                domain="medicine",
                hierarchy_level=1,
                metadata={
                    "type": "medical_term",
                    "category": term.category.value,
                    "body_system": term.body_system.value if term.body_system else None,
                    "etymology": term.etymology,
                    "proficiency": term.proficiency.value,
                },
            )
            self.ltm.consolidate(node, source="medicine_domain")
            count += 1
        
        # Save conditions as patterns
        for condition in self._conditions.values():
            node = Node(
                node_id=f"med_cond:{condition.condition_id}",
                label=condition.name,
                node_type=NodeType.CONCEPT,
                content=condition.description,
                domain="medicine",
                hierarchy_level=2,
                metadata={
                    "type": "medical_condition",
                    "icd_code": condition.icd_code,
                    "symptoms": condition.symptoms,
                    "treatments": condition.treatments,
                    "body_system": condition.body_system.value if condition.body_system else None,
                },
            )
            self.ltm.consolidate(node, source="medicine_domain")
            count += 1
        
        # Save drugs as patterns
        for drug in self._drugs.values():
            node = Node(
                node_id=f"med_drug:{drug.drug_id}",
                label=drug.name,
                node_type=NodeType.CONCEPT,
                content=f"{drug.generic_name}: {drug.mechanism_of_action}",
                domain="medicine",
                hierarchy_level=2,
                metadata={
                    "type": "drug",
                    "generic_name": drug.generic_name,
                    "drug_class": drug.drug_class.value,
                    "indications": drug.indications,
                },
            )
            self.ltm.consolidate(node, source="medicine_domain")
            count += 1
        
        logger.info(f"Saved {count} medical patterns to LTM")
        return count
