# RPA AI - Learning by Being Taught

## Core Philosophy

**RPA AI learns by being TAUGHT via curriculum and registered data sources.**

This is NOT a system where knowledge is hard-coded. The AI:
1. **Learns from registered HuggingFace datasets** (primary source)
2. **Falls back to local curriculum files** (secondary source)
3. **Takes tests after each lesson** to reinforce learning
4. **Takes exams every 12 hours** to measure progress

## ⚠️ CRITICAL RULES FOR DEVELOPERS

### DO NOT Hard-Code Knowledge

```python
# ❌ WRONG - Never do this:
class FinanceDomain:
    def __init__(self):
        self.terms = {
            "Asset": "A resource with economic value",
            "Liability": "A financial obligation",
            # ... hard-coded terms
        }

# ✅ CORRECT - Register data sources instead:
# In config/datasets.json:
{
  "financial_phrasebank": {
    "dataset_name": "takala/financial_phrasebank",
    "domain": "finance",
    "description": "4,840 financial news sentences"
  }
}
```

### How to Add New Knowledge Domains

1. **Find a HuggingFace dataset** with the knowledge
2. **Register it in `config/datasets.json`**:
   ```json
   {
     "your_dataset": {
       "name": "Dataset Name",
       "source": "huggingface",
       "dataset_name": "org/dataset-name",
       "domain": "your_domain",
       "priority": 1,
       "fields": { "text": "content_field" },
       "curriculum_type": "natural_language",
       "hierarchy_levels": [1, 2]
     }
   }
   ```
3. **Create local curriculum fallback** in `curriculum/your_domain/`
4. **Update `learn_pipeline.py`** if needed for domain-specific processing
5. **Run the pipeline**: `python learn_pipeline.py --domain your_domain`

## Accelerated Learning Schedule

The RPA AI learns **24/7** on an accelerated schedule:

| Hour | Subject | Activity |
|------|---------|----------|
| 0:00 | English | Vocabulary + Grammar |
| 1:00 | Python | Coding Patterns |
| 2:00 | Finance | Market Terminology |
| 3:00 | Medicine | Medical Knowledge |
| 4:00 | Health | Wellness Concepts |
| 5:00 | **EXAM** | Comprehensive Test |
| 6:00 | English | Reading Comprehension |
| 7:00 | Python | Algorithm Practice |
| 8:00 | Finance | Financial Analysis |
| 9:00 | Medicine | Anatomy & Physiology |
| 10:00 | Health | Nutrition & Exercise |
| 11:00 | **EXAM** | Comprehensive Test |
| 12:00 | English | Writing Practice |
| 13:00 | Python | Code Review |
| 14:00 | Finance | Investment Concepts |
| 15:00 | Medicine | Pharmacology |
| 16:00 | Health | Mental Wellness |
| 17:00 | **EXAM** | Comprehensive Test |
| 18:00 | English | Vocabulary Review |
| 19:00 | Python | Problem Solving |
| 20:00 | Finance | Economic Indicators |
| 21:00 | Medicine | Diseases & Conditions |
| 22:00 | Health | Preventive Care |
| 23:00 | **EXAM** | Comprehensive Test |

### Learning Cycle Details

- **Every Hour**: New lesson from a different domain
- **Post-Lesson**: Automatic test to reinforce learning
- **Every 6 Hours**: Comprehensive exam covering all domains
- **4 Exams Per Day**: Progress tracking and gap identification

## Quick Start

```bash
# Start RPA
./start.sh

# Or run learning manually:
python learn_pipeline.py --domain english --samples 100
python learn_pipeline.py --domain python --samples 50
python learn_pipeline.py --domain finance --samples 80
python learn_pipeline.py --domain medicine --samples 60

# Run accelerated learning schedule:
python -m rpa.scheduling.accelerated_learning
```

## Project Structure

```
RPA/
├── config/
│   ├── datasets.json          # Registered HuggingFace datasets
│   └── self_improvement.yaml  # Self-improvement configuration
├── curriculum/
│   ├── english/               # English curriculum files
│   ├── coding/                # Python curriculum files
│   ├── finance/               # Finance curriculum files
│   ├── medicine/              # Medicine curriculum files
│   ├── health/                # Health curriculum files
│   ├── exams/                 # Exam definitions
│   └── tracks/                # Learning track definitions
├── rpa/
│   ├── memory/
│   │   ├── ltm.py            # Long-term memory (pattern storage)
│   │   ├── stm.py            # Short-term memory
│   │   └── episodic.py       # Episodic memory
│   ├── domains/
│   │   ├── english.py        # English domain handler
│   │   ├── finance.py        # Finance domain handler
│   │   ├── medicine.py       # Medicine domain handler
│   │   └── health.py         # Health domain handler
│   ├── scheduling/
│   │   ├── daily_timetable.py         # Daily schedule
│   │   └── accelerated_learning.py    # Hourly learning
│   ├── training/
│   │   ├── learn_pipeline.py          # Main learning pipeline
│   │   ├── self_improvement.py        # Self-improvement orchestrator
│   │   └── gap_closure.py             # Gap detection
│   └── assessment/
│       ├── engine.py          # Assessment engine
│       ├── exam_engine.py     # Exam system
│       └── badge_manager.py   # Achievement tracking
├── memory/learning_state/     # Persisted learning patterns
└── tests/                     # Test suite (run with pytest)
```

## Registered Data Sources

| Dataset | Domain | Size | Description |
|---------|--------|------|-------------|
| wikitext | English | 4MB | Wikipedia articles |
| squad_v2 | English | 35MB | Question answering |
| mbpp | Python | 1MB | Basic Python problems |
| humaneval | Python | 0.3MB | Code generation benchmark |
| financial_phrasebank | Finance | 2MB | Financial news sentences |
| business_economics_k12 | Finance | 5MB | K-12 economics standards |
| financial_training | Finance | 50MB | Financial analysis data |

## Current Progress

- **Patterns Learned**: 5,279+
- **Domains Active**: English, Python, Finance, Medicine, Health
- **Tests Passing**: 957
- **Learning Rate**: Accelerated (hourly rotation)

## Development Commands

```bash
# Run tests
pytest tests/ -v

# Run specific domain tests
pytest tests/test_finance_domain.py -v

# Check LTM patterns
python -c "
from rpa.memory.ltm import LongTermMemory
ltm = LongTermMemory()
ltm.load()
print(f'Total patterns: {len(ltm._graph.nodes)}')
"

# Run self-improvement cycle
python -c "
from rpa.training.self_improvement import SelfImprovementOrchestrator
orch = SelfImprovementOrchestrator()
result = orch.run_improvement_cycle()
print(result)
"
```

## Adding New Domains - Step by Step

1. **Research HuggingFace** for relevant datasets
2. **Add dataset config** to `config/datasets.json`
3. **Create curriculum directory**: `curriculum/new_domain/`
4. **Add curriculum files** (JSON format)
5. **Update pipeline** if needed in `learn_pipeline.py`
6. **Create domain handler** in `rpa/domains/new_domain.py`
7. **Add tests** in `tests/test_new_domain.py`
8. **Run learning**: `python learn_pipeline.py --domain new_domain`

## Requirements

- Python 3.12+
- Docker Desktop (for containerized deployment)
- HuggingFace datasets library: `pip install datasets`

## License

Private project - All rights reserved
