# RPA Dataset Connections - Summary Report

## Connection Test Results

| Status | Dataset | Items Available | Curriculum Potential |
|--------|---------|-----------------|---------------------|
| ✅ | **MBPP** | 374 | ~374 Python problems |
| ✅ | **HumanEval** | 164 | ~164 Python functions |
| ✅ | **WikiText-2** | 36,718 | ~11,015 text segments |
| ✅ | **SQuAD v2** | 130,319 | ~13,031 QA pairs |
| ✅ | **LeetCode** | 2,360 | ~708 algorithm problems |
| ✅ | **CodeSearchNet** | Streaming | ~100,000+ code functions |
| ❌ | CodeAlpaca | - | Dataset unavailable |
| ❌ | Simple Wikipedia | - | Script format deprecated |
| ❌ | Python Docs | - | Dataset unavailable |
| ❌ | WordNet | - | Dataset unavailable |

**Total Connected: 6/10 datasets**
**Estimated Curriculum Items: ~25,000+**

---

## Sample Curriculum Outputs

### 1. MBPP - Python Problems

**Raw Input:**
```
task_id: 602
text: Write a python function to find the first repeated character in a given string.
code: def first_repeated_char(str1):
        for index,c in enumerate(str1):
          if str1[:index+1].count(c) > 1:
            return c 
        return "None"
```

**Generated Curriculum:**
```json
{
  "lesson_id": "py_cod_0001_e06322b2",
  "content": "def first_repeated_char(str1):\n  for index,c in enumerate(str1):\n    if str1[:index+1].count(c) > 1:\n      return c \n  return \"None\"",
  "type": "pattern",
  "hierarchy_level": 2,
  "domain": "python",
  "composition": ["d", "e", "f", "␣", "f", "i", "r", "s", "t", "_", ...],
  "metadata": {
    "source": "mbpp",
    "curriculum_type": "coding_problems",
    "description": "Write a python function to find the first repeated character...",
    "difficulty": 2
  }
}
```

---

### 2. HumanEval - Code Functions

**Raw Input:**
```
task_id: HumanEval/0
prompt: def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """Check if there are two elements closer than threshold."""
canonical_solution: 
    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = abs(elem - elem2)
                if distance < threshold:
                    return True
    return False
```

**Generated Curriculum:**
```json
{
  "lesson_id": "py_cod_0000_833c0946",
  "content": "for idx, elem in enumerate(numbers):\n    for idx2, elem2 in enumerate(numbers):\n        if idx != idx2:\n            distance = abs(elem - elem2)\n            if distance < threshold:\n                return True\n    return False",
  "type": "pattern",
  "hierarchy_level": 3,
  "domain": "python",
  "metadata": {
    "source": "openai_humaneval",
    "curriculum_type": "coding_functions",
    "difficulty": 3
  }
}
```

---

### 3. WikiText-2 - Natural Language

**Generated Curriculum:**
```json
{
  "lesson_id": "en_nat_0001_4af50eed",
  "content": "= Valkyria Chronicles III = \n",
  "type": "pattern",
  "hierarchy_level": 1,
  "domain": "english",
  "composition": ["=", "Valkyria", "Chronicles", "III", "="],
  "metadata": {
    "source": "wikitext",
    "curriculum_type": "natural_language",
    "difficulty": 1
  }
}
```

---

### 4. SQuAD v2 - Question Answering

**Raw Input:**
```
context: Beyoncé Giselle Knowles-Carter is an American singer...
question: When did Beyonce start becoming popular?
answers: ['in the late 1990s']
```

**Generated Curriculum:**
```json
{
  "lesson_id": "en_qa__0000_beb6b736",
  "content": "Beyoncé Giselle Knowles-Carter... rose to fame in the late 1990s...",
  "type": "pattern",
  "hierarchy_level": 2,
  "domain": "english",
  "metadata": {
    "source": "squad_v2",
    "curriculum_type": "qa_pairs",
    "question": "When did Beyonce start becoming popular?",
    "answer": "in the late 1990s",
    "difficulty": 2
  }
}
```

---

### 5. LeetCode - Algorithm Problems

**Generated Curriculum:**
```json
{
  "lesson_id": "py_cod_0000_552c1306",
  "content": "def twoSum(nums, target):\n    map = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in map:\n            return [map[complement], i]\n        map[num] = i",
  "type": "pattern",
  "hierarchy_level": 2,
  "domain": "python",
  "metadata": {
    "source": "greengerong/leetcode",
    "curriculum_type": "coding_problems",
    "title": "Two Sum",
    "difficulty": 2
  }
}
```

---

### 6. CodeSearchNet - Code with Documentation

**Generated Curriculum:**
```json
{
  "lesson_id": "py_cod_0000_15e2a4f1",
  "content": "def __msgc_step3_discontinuity_localization(self):\n    \"\"\"Estimate discontinuity...\"\"\"\n    import scipy\n    start = self._start_time\n    seg = 1 - self.segmentation.astype(np.int8)\n    ...",
  "type": "pattern",
  "hierarchy_level": 3,
  "domain": "python",
  "metadata": {
    "source": "code_search_net",
    "curriculum_type": "code_with_docstring",
    "docstring": "Estimate discontinuity in basis of low resolution...",
    "difficulty": 3
  }
}
```

---

## Recommended Training Order

### Phase 1: Foundations (Level 0-1)
| Dataset | Items | Focus |
|---------|-------|-------|
| WikiText-2 | 1,000 | Basic English patterns |
| MBPP | 374 | Simple Python patterns |

### Phase 2: Intermediate (Level 1-2)
| Dataset | Items | Focus |
|---------|-------|-------|
| HumanEval | 164 | Function patterns |
| SQuAD v2 | 2,000 | Q&A comprehension |

### Phase 3: Advanced (Level 2-3)
| Dataset | Items | Focus |
|---------|-------|-------|
| LeetCode | 1,000 | Algorithm patterns |
| CodeSearchNet | 10,000 | Real-world code |

---

## Next Steps

1. **Run full training pipeline** - Process all connected datasets into curriculum files
2. **Fix failed datasets** - Find alternative sources for CodeAlpaca, Simple Wikipedia
3. **Add dataset caching** - Speed up repeated training runs
4. **Create training dashboard** - Monitor learning progress in real-time

---

## Files Created

```
/home/z/my-project/RPA/
├── config/
│   └── datasets.json      # Dataset configuration
└── test_datasets.py       # Connection test script
```

**To run tests again:**
```bash
/usr/bin/python3 /home/z/my-project/RPA/test_datasets.py
```
