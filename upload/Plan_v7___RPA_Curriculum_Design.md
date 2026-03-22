I have created the following plan after thorough exploration and analysis of the codebase. Follow the below plan verbatim. Trust the files and references. Do not re-verify what's written in the plan. Explore only when absolutely necessary. First implement all the proposed file changes and then I'll review all the changes together at the end.

# Recursive Pattern Agent (RPA) — Pragmatic Scaling & Enhancement Plan

## Observations

You have a working skeleton implementation on another platform that successfully stores and retrieves patterns but lacks depth in self-assessment, proactive inquiry, and correction-based learning loops. The architecture is sound (STM/LTM/episodic memory, pattern graphs, hierarchy levels), but the "intelligence" components need substantial fleshing out. The consolidation logic is opaque (21/50 words passing), gap detection is stubbed, and there are no tests. The real opportunity is to scale curriculum complexity (words → sentences → code snippets), enhance recursive linking, and make the learning feedback loops genuinely operational.

## Approach

Rather than redesigning, this plan focuses on **pragmatic enhancement** of the existing skeleton. The strategy is: (1) make consolidation transparent with detailed validation reporting, (2) implement sophisticated self-assessment with measurable criteria, (3) build real gap detection and proactive inquiry, (4) add comprehensive tests, (5) scale curriculum complexity progressively, (6) enhance recursive pattern linking, (7) prepare the API layer for external agent integration. Work is organized into three phases: **Foundation Hardening** (weeks 1-2), **Intelligence Deepening** (weeks 3-4), and **Scaling & Integration** (weeks 5-6).

---

## Phase 1: Foundation Hardening (Weeks 1-2)

### 1.1 Consolidation Transparency & Validation Reporting

**File**: `rpa/validation/consolidation_reporter.py`

- Implement `ConsolidationReporter` class with detailed validation breakdown:
  - `report_consolidation(batch_id, session_id) -> dict` — returns:
    ```python
    {
      "batch_id": "english_batch_2",
      "total_patterns": 50,
      "consolidated": 21,
      "rejected": 15,
      "pending_review": 14,
      "breakdown": {
        "structural_valid": 21,
        "missing_references": 8,
        "circular_dependencies": 3,
        "incomplete_composition": 4,
        "other_issues": 0
      },
      "details": [
        {
          "node_id": "word:apple",
          "status": "consolidated",
          "issues": []
        },
        {
          "node_id": "word:xyz",
          "status": "rejected",
          "issues": ["missing child node: primitive:z"]
        }
      ]
    }
    ```
  - `identify_rejection_patterns(batch_id) -> dict` — groups rejections by issue type
  - `suggest_fixes(node_id) -> List[str]` — recommends how to fix a rejected pattern

**File**: `rpa/validation/validator.py` (extend)

- Add `validate_pattern_structure_detailed(node_id, ltm) -> dict` that returns:
  - `is_valid: bool`
  - `structural_issues: List[dict]` — each with `issue_type`, `description`, `affected_nodes`
  - `missing_references: List[str]` — node IDs that don't exist
  - `circular_deps: List[List[str]]` — cycles in the graph
  - `composition_depth: int` — how many levels deep the pattern is composed
  - `all_children_resolved: bool` — all child references exist

### 1.2 Enhanced Self-Assessment with Measurable Criteria

**File**: `rpa/assessment/criteria.py` (new)

- Define `AssessmentCriteria` dataclass:
  ```python
  @dataclass
  class AssessmentCriteria:
      pattern_id: str
      criteria: List[dict]  # [{"type": "reconstruct", "weight": 0.4}, ...]
      required_pass_rate: float  # 0.8 = 80% of exercises must pass
      structural_validation_required: bool
      recursive_depth_check: bool
  ```

**File**: `rpa/assessment/engine.py` (extend)

- Enhance `SelfAssessmentEngine.assess_pattern()`:
  - Generate 5-10 exercises (not 3-5) covering:
    - **Reconstruction**: generate output, compare to expected
    - **Recognition**: given output, identify pattern
    - **Composition**: given components, compose pattern
    - **Decomposition**: given pattern, identify components
    - **Recursive recall**: given pattern, traverse and verify all children exist
  - Score each exercise: `{"exercise_id": str, "type": str, "passed": bool, "expected": str, "generated": str, "issues": List[str]}`
  - Return detailed assessment:
    ```python
    {
      "node_id": str,
      "is_valid": bool,
      "exercises": List[dict],
      "pass_rate": float,  # 0.0-1.0
      "structural_issues": List[str],
      "recursive_depth": int,
      "all_children_resolved": bool,
      "assessment_summary": str  # human-readable
    }
    ```

### 1.3 Comprehensive Test Suite

**File**: `tests/test_core_graph.py`

- Test `PatternGraph`:
  - Node creation and retrieval
  - Edge creation and ordering
  - Circular dependency detection
  - Traversal correctness
  - Hierarchy level calculation

**File**: `tests/test_memory_layers.py`

- Test `ShortTermMemory`, `LongTermMemory`, `EpisodicMemory`:
  - Pattern creation in STM
  - Consolidation to LTM
  - Event logging
  - Session isolation

**File**: `tests/test_assessment.py`

- Test `SelfAssessmentEngine`:
  - Exercise generation
  - Scoring logic
  - Structural validation
  - Detailed reporting

**File**: `tests/test_validation.py`

- Test `Validator`:
  - Structural validation
  - Issue detection
  - Fix suggestions

**File**: `tests/test_consolidation.py`

- Test `ConsolidationReporter`:
  - Rejection pattern identification
  - Detailed breakdown
  - Fix recommendations

**File**: `tests/fixtures.py`

- Provide reusable test data:
  - Sample primitives (a, b, c, ...)
  - Sample patterns (apple, cat, dog, ...)
  - Sample sentences
  - Sample code snippets

---

## Phase 2: Intelligence Deepening (Weeks 3-4)

### 2.1 Sophisticated Gap Detection

**File**: `rpa/inquiry/gap_detector.py` (rewrite)

- Implement `GapDetector` with multiple detection strategies:
  - `detect_flagged_uncertain_patterns(ltm) -> List[Node]` — patterns marked `is_uncertain=True`
  - `detect_incomplete_composition(ltm) -> List[dict]` — patterns with missing child references
    - Returns: `[{"node_id": str, "missing_children": List[str], "severity": "high"|"medium"|"low"}]`
  - `detect_orphaned_patterns(ltm) -> List[Node]` — patterns not referenced by higher-level patterns
  - `detect_unresolved_references(ltm) -> List[dict]` — edges pointing to non-existent nodes
  - `detect_hierarchy_gaps(ltm, domain) -> List[dict]` — missing intermediate levels
    - Example: primitives exist, words exist, but no sentence patterns
  - `detect_cross_domain_gaps(ltm) -> List[dict]` — patterns in one domain that could link to another
    - Example: "if" (code) could link to "conditional" (English concept)
  - `prioritize_gaps(gaps: List[dict]) -> List[dict]` — rank by impact and frequency

### 2.2 Intelligent Question Generation

**File**: `rpa/inquiry/question_generator.py` (enhance)

- Extend `QuestionGenerator` with context-aware questions:
  - `generate_composition_question(node_id, missing_children) -> str`
    - Example: "I learned 'apple' from a, p, p, l, e. But I'm missing the connection to 'p'. Can you clarify?"
  - `generate_usage_question(node_id, orphaned_status) -> str`
    - Example: "I know the word 'apple'. How is it used in sentences?"
  - `generate_hierarchy_question(domain, missing_level) -> str`
    - Example: "I know letters and words in English. What comes between them?"
  - `generate_cross_domain_question(node_id_1, domain_1, node_id_2, domain_2) -> str`
    - Example: "I know 'if' in Python. How does it relate to 'conditional' in English?"
  - `generate_batch_questions(batch_id, ltm, gap_priorities) -> List[dict]`
    - Returns: `[{"inquiry_id": str, "question": str, "type": str, "gap_type": str, "priority": "high"|"medium"|"low"}]`

### 2.3 Learning from User Answers

**File**: `rpa/learning/answer_integrator.py` (new)

- Implement `AnswerIntegrator` to process inquiry responses:
  - `integrate_composition_answer(inquiry_id, response, node_id, stm, ltm) -> dict`
    - Parses response to identify missing children
    - Creates new edges or nodes as needed
    - Returns: `{"new_nodes": List[str], "new_edges": List[str], "pattern_updated": bool}`
  - `integrate_usage_answer(inquiry_id, response, node_id, stm, ltm) -> dict`
    - Identifies higher-level patterns mentioned in response
    - Creates `FOLLOWS` or `IS_INSTANCE_OF` edges
  - `integrate_hierarchy_answer(inquiry_id, response, domain, stm, ltm) -> dict`
    - Creates intermediate pattern nodes
    - Links them to existing primitives and higher-level patterns
  - `integrate_cross_domain_answer(inquiry_id, response, node_id_1, node_id_2, stm, ltm) -> dict`
    - Creates cross-domain edges (e.g., `CLARIFIES`, `EXPANDS`)
  - `validate_integrated_pattern(node_id, ltm) -> dict` — re-validates after integration

### 2.4 Correction Feedback Loop

**File**: `rpa/learning/correction_analyzer.py` (new)

- Implement `CorrectionAnalyzer`:
  - `analyze_correction(wrong_node_id, correct_node_id, feedback, ltm) -> dict`
    - Identifies what was wrong (structural, compositional, usage)
    - Suggests pattern refinements
    - Returns: `{"issue_type": str, "root_cause": str, "suggested_fixes": List[str]}`
  - `apply_correction_insights(wrong_node_id, correct_node_id, ltm) -> dict`
    - Updates related patterns to avoid similar errors
    - Marks similar patterns for review
    - Returns: `{"patterns_updated": List[str], "patterns_flagged": List[str]}`

---

## Phase 3: Scaling & Integration (Weeks 5-6)

### 3.1 Curriculum Complexity Scaling

**File**: `curriculum/english/batch_2_words_enhanced.json`

- Expand from 50 to 200+ high-frequency words
- Add metadata:
  ```json
  {
    "lesson_id": "en_2_001",
    "content": "apple",
    "type": "pattern",
    "hierarchy_level": 1,
    "composition": ["a", "p", "p", "l", "e"],
    "usage_contexts": ["fruit", "food", "noun"],
    "related_patterns": ["apples", "apple_tree"],
    "difficulty": 1,
    "frequency": "high"
  }
  ```

### 3.1a Dataset-Driven Curriculum Generation

**File**: `rpa/preprocessing/dataset_loader.py` (new)

- Implement `DatasetLoader` to ingest Hugging Face datasets:
  - `load_huggingface_dataset(dataset_name: str, split: str = "train") -> Dataset` — loads dataset from HF Hub
  - `load_local_dataset(path: str, format: str) -> Dataset` — loads local datasets (CSV, JSON, Parquet)
  - `validate_dataset_schema(dataset: Dataset, required_fields: List[str]) -> bool` — ensures dataset has required columns
  - Supported formats: text, code, structured (CSV), unstructured (JSON)

**File**: `rpa/preprocessing/dataset_interpreter.py` (new)

- Implement `DatasetInterpreter` to convert datasets into curriculum:
  - `interpret_text_dataset(dataset: Dataset, domain: str, batch_config: dict) -> List[dict]`
    - Extracts text samples from dataset
    - Segments by hierarchy (words, sentences, paragraphs)
    - Deduplicates and filters by frequency/quality
    - Returns annotated sequences ready for curriculum packaging
  - `interpret_code_dataset(dataset: Dataset, language: str, batch_config: dict) -> List[dict]`
    - Extracts code snippets from dataset
    - Parses into primitives (keywords, operators, literals)
    - Segments by complexity (expressions, statements, functions)
    - Returns annotated code patterns
  - `interpret_structured_dataset(dataset: Dataset, domain: str, batch_config: dict) -> List[dict]`
    - Extracts key-value pairs, relationships, hierarchies
    - Maps to pattern composition
    - Returns structured patterns
  - `filter_by_quality(sequences: List[dict], min_length: int, max_length: int, language: str) -> List[dict]`
    - Removes duplicates, malformed entries, non-UTF8
    - Validates against domain-specific rules
  - `rank_by_frequency(sequences: List[dict]) -> List[dict]`
    - Sorts by occurrence in dataset
    - Prioritizes high-frequency patterns for early learning

**File**: `rpa/preprocessing/dataset_curriculum_builder.py` (new)

- Implement `DatasetCurriculumBuilder` to create batches from interpreted data:
  - `build_curriculum_from_dataset(dataset_name: str, domain: str, num_batches: int, batch_size: int) -> List[dict]`
    - Loads dataset via `DatasetLoader`
    - Interprets via `DatasetInterpreter`
    - Organizes into progressive batches (primitives → patterns → complex)
    - Returns list of curriculum batch dicts
  - `create_batch(sequences: List[dict], batch_id: str, hierarchy_level: int, difficulty: int) -> dict`
    - Packages sequences into a lesson batch
    - Adds success metrics based on hierarchy level
    - Returns curriculum batch JSON
  - `validate_curriculum_progression(batches: List[dict]) -> dict`
    - Ensures each batch builds on previous
    - Checks for gaps in hierarchy
    - Returns: `{"is_valid": bool, "issues": List[str], "recommendations": List[str]}`
  - `export_curriculum(batches: List[dict], output_dir: str) -> List[str]`
    - Saves batches to `curriculum/<domain>/` directory
    - Returns list of exported file paths

**File**: `rpa/preprocessing/dataset_config.py` (new)

- Define dataset interpretation configurations:
  ```python
  @dataclass
  class DatasetConfig:
      dataset_name: str  # e.g., "wikitext", "openwebtext", "code_search_net"
      domain: str  # "english", "python", "javascript"
      split: str  # "train", "validation", "test"
      text_field: str  # column name containing text/code
      metadata_fields: List[str]  # optional: category, language, etc.
      min_length: int  # minimum sequence length
      max_length: int  # maximum sequence length
      sample_size: int  # number of samples to use (None = all)
      deduplication: bool  # remove duplicates
      language_filter: str  # filter by language (for multilingual datasets)
      quality_threshold: float  # 0.0-1.0, filter low-quality samples
  ```

**File**: `rpa/preprocessing/dataset_examples.py` (new)

- Provide pre-configured dataset interpretations:
  ```python
  DATASET_CONFIGS = {
      "english_wikitext": DatasetConfig(
          dataset_name="wikitext",
          domain="english",
          split="train",
          text_field="text",
          min_length=10,
          max_length=500,
          sample_size=10000,
          deduplication=True,
          quality_threshold=0.8
      ),
      "python_code_search_net": DatasetConfig(
          dataset_name="code_search_net",
          domain="python",
          split="train",
          text_field="code",
          min_length=5,
          max_length=200,
          sample_size=5000,
          deduplication=True,
          quality_threshold=0.9
      ),
      "english_common_voice": DatasetConfig(
          dataset_name="common_voice",
          domain="english",
          split="train",
          text_field="sentence",
          min_length=5,
          max_length=100,
          sample_size=5000,
          language_filter="en",
          deduplication=True
      )
  }
  ```

**File**: `curriculum/english/batch_3_sentences_new.json`

- Create 100+ simple sentences with explicit structure (auto-generated from datasets):
  ```json
  {
    "lesson_id": "en_3_001",
    "content": "The cat sat.",
    "type": "pattern",
    "hierarchy_level": 2,
    "composition": ["the", "cat", "sat"],
    "structure": {
      "subject": "cat",
      "verb": "sat",
      "article": "the"
    },
    "related_patterns": ["The dog sat.", "The cat ran."],
    "difficulty": 2,
    "frequency": "high",
    "source_dataset": "wikitext",
    "dataset_frequency": 1250
  }
  ```

**File**: `curriculum/coding/batch_2_python_patterns_enhanced.json`

- Expand Python patterns with explicit composition (auto-generated from datasets):
  ```json
  {
    "lesson_id": "py_2_001",
    "content": "x = 5",
    "type": "pattern",
    "hierarchy_level": 1,
    "composition": ["x", "=", "5"],
    "pattern_type": "assignment",
    "related_patterns": ["y = 10", "name = 'Alice'"],
    "difficulty": 1,
    "frequency": "high",
    "source_dataset": "code_search_net",
    "dataset_frequency": 8750
  }
  ```

**File**: `curriculum/coding/batch_3_code_snippets_new.json`

- Add code snippet patterns (3-5 lines, auto-generated from datasets):
  ```json
  {
    "lesson_id": "py_3_001",
    "content": "for i in range(5):\n    print(i)",
    "type": "pattern",
    "hierarchy_level": 2,
    "composition": ["for", "i", "in", "range", "(", "5", ")", ":", "print", "(", "i", ")"],
    "structure": {
      "loop_type": "for",
      "variable": "i",
      "range": "5",
      "body": "print(i)"
    },
    "related_patterns": ["for i in range(10):", "for item in list:"],
    "difficulty": 2,
    "frequency": "high",
    "source_dataset": "code_search_net",
    "dataset_frequency": 3420
  }
  ```

### 3.2 Enhanced Recursive Pattern Linking

**File**: `rpa/learning/recursive_linker.py` (new)

- Implement `RecursiveLinker`:
  - `link_pattern_hierarchy(node_id, ltm) -> dict` — creates explicit links between hierarchy levels
    - Links primitives → words → sentences → paragraphs
    - Links code primitives → expressions → statements → functions
  - `identify_compound_patterns(ltm, domain) -> List[dict]` — finds patterns that can be composed
    - Example: "apple" + "tree" → "apple tree"
  - `create_compound_pattern(component_ids, compound_label, ltm) -> Node` — creates new pattern from components
  - `verify_recursive_integrity(node_id, ltm) -> dict` — ensures all levels are properly linked
    - Returns: `{"is_valid": bool, "missing_links": List[str], "orphaned_nodes": List[str]}`

### 3.3 Enhanced Practice & Exercise Loop

**File**: `rpa/assessment/exercise_generator.py` (enhance)

- Expand exercise types:
  - **Reconstruction**: generate output from pattern
  - **Recognition**: identify pattern from output
  - **Composition**: compose pattern from components
  - **Decomposition**: decompose pattern into components
  - **Recursive recall**: traverse and verify all children
  - **Contextual usage**: use pattern in a sentence or code snippet
  - **Error detection**: identify and fix errors in a pattern
  - **Analogy**: find similar patterns in same or different domain
  - **Transformation**: transform pattern (e.g., singular → plural, lowercase → uppercase)

**File**: `rpa/assessment/exercise_scorer.py` (new)

- Implement `ExerciseScorer`:
  - `score_exercise(exercise, response, ltm) -> dict`
    - Returns: `{"is_correct": bool, "score": 0.0-1.0, "feedback": str, "issues": List[str]}`
  - `aggregate_exercise_scores(exercises: List[dict]) -> dict`
    - Returns: `{"overall_score": float, "by_type": dict, "strengths": List[str], "weaknesses": List[str]}`

### 3.4 API Layer for External Agent Integration

**File**: `rpa/api/agent_interface.py` (new)

- Implement `AgentInterface` for external agents:
  ```python
  class AgentInterface:
      def query_pattern(self, label: str, domain: str) -> dict
      def teach_pattern(self, content: str, domain: str, hierarchy_level: int) -> dict
      def assess_pattern(self, label: str, domain: str) -> dict
      def get_inquiries(self, domain: str = None) -> List[dict]
      def answer_inquiry(self, inquiry_id: str, response: str) -> dict
      def get_curriculum_status(self) -> dict
      def get_memory_status(self) -> dict
  ```

**File**: `rpa/api/rest_server.py` (new)

- Implement REST API using Flask or FastAPI:
  - `GET /pattern/<label>/<domain>` — query pattern
  - `POST /pattern` — teach pattern
  - `GET /pattern/<label>/<domain>/assess` — assess pattern
  - `GET /inquiries` — get pending inquiries
  - `POST /inquiries/<inquiry_id>/answer` — answer inquiry
  - `GET /status/curriculum` — curriculum status
  - `GET /status/memory` — memory status

**File**: `rpa/api/websocket_server.py` (new)

- Implement WebSocket server for real-time interaction:
  - Agents can subscribe to inquiry events
  - Agents can push answers in real-time
  - Agents can stream pattern learning

---

## Implementation Roadmap

### Week 1: Foundation Hardening
- [ ] Implement `ConsolidationReporter` with detailed validation breakdown
- [ ] Enhance `SelfAssessmentEngine` with 5-10 exercises and measurable criteria
- [ ] Create comprehensive test suite (core, memory, assessment, validation, consolidation)
- [ ] Document why 21/50 words consolidated (run reporter on existing data)

### Week 2: Foundation Hardening (continued)
- [ ] Fix any issues identified by tests
- [ ] Achieve 80%+ test coverage on core modules
- [ ] Create test fixtures and sample data
- [ ] Document test results and coverage

### Week 3: Intelligence Deepening
- [ ] Implement sophisticated `GapDetector` with 6 detection strategies
- [ ] Enhance `QuestionGenerator` with context-aware questions
- [ ] Implement `AnswerIntegrator` to learn from user responses
- [ ] Test gap detection and question generation on existing curriculum

### Week 4: Intelligence Deepening (continued)
- [ ] Implement `CorrectionAnalyzer` for correction feedback loop
- [ ] Create end-to-end test: teach → assess → identify gaps → ask questions → integrate answers
- [ ] Document learning loop effectiveness
- [ ] Refine question generation based on test results

### Week 5: Scaling & Integration
- [ ] Expand English curriculum (batch 2: 200+ words, batch 3: 100+ sentences)
- [ ] Expand Python curriculum (batch 2: patterns, batch 3: code snippets)
- [ ] Implement `RecursiveLinker` for hierarchy linking
- [ ] Enhance exercise generator with 9 exercise types

### Week 6: Scaling & Integration (continued)
- [ ] Implement `ExerciseScorer` with detailed feedback
- [ ] Implement `AgentInterface` for external agent integration
- [ ] Implement REST API server
- [ ] Implement WebSocket server for real-time interaction
- [ ] End-to-end testing with external agent simulation

### Week 7: Dataset-Driven Curriculum (NEW)
- [ ] Implement `DatasetLoader` to ingest Hugging Face datasets
- [ ] Implement `DatasetInterpreter` for text, code, and structured data
- [ ] Create pre-configured dataset interpretations (wikitext, code_search_net, common_voice)
- [ ] Test dataset loading and interpretation on 3-5 datasets

### Week 8: Dataset-Driven Curriculum (continued)
- [ ] Implement `DatasetCurriculumBuilder` to create batches from datasets
- [ ] Auto-generate English curriculum from wikitext (1000+ words, 500+ sentences)
- [ ] Auto-generate Python curriculum from code_search_net (500+ patterns, 200+ snippets)
- [ ] Validate curriculum progression and quality
- [ ] Export auto-generated curricula to `curriculum/` directory

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Consolidation transparency | 100% of rejections explained | Unknown |
| Self-assessment coverage | 9 exercise types | 3-5 |
| Gap detection strategies | 6 types | 0 (stubbed) |
| Test coverage | 80%+ | 0% |
| Curriculum complexity | Words → Sentences → Code snippets | Words only |
| Recursive linking | All hierarchy levels linked | Partial |
| Learning from answers | Integrated into LTM | Minimal |
| API readiness | REST + WebSocket | None |
| Dataset integration | 5+ datasets supported | 0 |
| Auto-generated curriculum | 1000+ words, 500+ sentences, 500+ code patterns | 0 |
| Dataset quality filtering | 90%+ valid patterns | N/A |
| Curriculum progression validation | 100% of batches validated | N/A |

---

## Key Deliverables

1. **Consolidation Transparency**: Detailed reports explaining why patterns pass/fail
2. **Enhanced Self-Assessment**: 5-10 exercises per pattern with measurable criteria
3. **Comprehensive Tests**: 80%+ coverage with fixtures and sample data
4. **Sophisticated Gap Detection**: 6 detection strategies with prioritization
5. **Intelligent Inquiry**: Context-aware questions based on gap type
6. **Learning Loop**: Integrate user answers into LTM with validation
7. **Correction Feedback**: Analyze corrections and refine related patterns
8. **Scaled Curriculum**: 200+ words, 100+ sentences, code snippets
9. **Recursive Linking**: All hierarchy levels properly connected
10. **API Layer**: REST + WebSocket for external agent integration
11. **Dataset Integration**: Load and interpret Hugging Face datasets
12. **Auto-Generated Curriculum**: 1000+ words, 500+ sentences, 500+ code patterns from real datasets
13. **Quality Filtering**: Deduplication, validation, frequency-based ranking
14. **Curriculum Validation**: Ensure progression and completeness across batches

---

## Technical Notes

- **No breaking changes**: All enhancements are additive; existing code remains functional
- **Backward compatible**: New fields in Node/Edge are optional with sensible defaults
- **Incremental testing**: Each component tested independently before integration
- **Documentation**: Each module includes docstrings, examples, and test cases
- **Performance**: Optimize graph traversal and validation for 1000+ patterns
- **Dataset caching**: Cache downloaded datasets locally to avoid repeated downloads
- **Streaming support**: Process large datasets in batches to minimize memory usage
- **Deduplication**: Use hashing to efficiently remove duplicate patterns
- **Quality metrics**: Track dataset quality scores and filter by threshold

---

## Dataset Integration Architecture

```mermaid
graph TD
    A[Hugging Face Hub] --> B[DatasetLoader]
    B --> C[DatasetInterpreter]
    C --> D[Text Interpreter]
    C --> E[Code Interpreter]
    C --> F[Structured Interpreter]
    D --> G[Segmentation<br/>Words / Sentences / Paragraphs]
    E --> H[Parsing<br/>Primitives / Expressions / Statements]
    F --> I[Relationship Extraction<br/>Hierarchies / Mappings]
    G --> J[DatasetCurriculumBuilder]
    H --> J
    I --> J
    J --> K[Quality Filtering<br/>Deduplication / Validation]
    K --> L[Frequency Ranking<br/>High → Low]
    L --> M[Batch Organization<br/>Primitives → Patterns → Complex]
    M --> N[Curriculum Export<br/>JSON to curriculum/]
    N --> O[RPA Learning<br/>Teach → Assess → Consolidate]
```

---

## Why This Approach Works

1. **Builds on existing skeleton**: Doesn't redesign, just deepens
2. **Addresses identified gaps**: Consolidation transparency, gap detection, learning loops
3. **Pragmatic scaling**: Curriculum complexity increases gradually
4. **Testable**: Each component has clear success criteria
5. **Agent-ready**: API layer prepared for external integration
6. **Measurable progress**: Weekly deliverables with clear metrics
7. **Data-driven learning**: Leverage massive, curated datasets from Hugging Face
8. **Scalable curriculum**: Auto-generate curricula for any domain with available datasets
9. **Quality assured**: Filter, deduplicate, and rank patterns by frequency
10. **Extensible**: Easy to add new dataset types and interpretation strategies

---

## Phase 4: Production Hardening & Execution Environment (Weeks 9-10)

### 4.1 Sandboxed Code Execution Layer

**File**: `rpa/execution/sandbox.py` (new)

- Implement `CodeSandbox` class for safe code execution:
  - `execute_code(code: str, language: str, timeout: int = 5) -> dict`
    - Executes code in isolated container
    - Captures stdout, stderr, return value
    - Returns: `{"success": bool, "output": str, "error": str, "execution_time": float}`
  - `execute_with_feedback(code: str, language: str, expected_output: str = None) -> dict`
    - Executes code and compares to expected output
    - Returns: `{"success": bool, "output": str, "matches_expected": bool, "feedback": str}`
  - `reset_environment()` — clears state between executions
  - Supported languages: Python, JavaScript, SQL (extensible)

**File**: `rpa/execution/container_manager.py` (new)

- Implement `ContainerManager` for Docker-based isolation:
  - `create_container(language: str) -> str` — creates isolated container
  - `execute_in_container(container_id: str, code: str) -> dict` — runs code
  - `cleanup_container(container_id: str)` — removes container
  - Resource limits: CPU, memory, disk, execution time
  - Network isolation: no external access

**File**: `rpa/execution/execution_logger.py` (new)

- Implement `ExecutionLogger` to track code execution:
  - `log_execution(code: str, language: str, result: dict, session_id: str, pattern_id: str)`
    - Logs to episodic memory: `event_type="code_execution"`
    - Stores: code, language, output, errors, execution time
  - `get_execution_history(pattern_id: str) -> List[dict]` — all executions of a pattern
  - `analyze_execution_patterns(pattern_id: str) -> dict` — success rate, common errors

### 4.2 Error Understanding & Classification System

**File**: `rpa/learning/error_classifier.py` (new)

- Implement `ErrorClassifier` to categorize errors:
  - `classify_error(error_message: str, language: str) -> dict`
    - Returns: `{"error_type": str, "category": str, "severity": str, "description": str}`
    - Error types: syntax, runtime, logical, structural, type, reference
    - Categories: missing_syntax, wrong_operator, undefined_variable, type_mismatch, etc.
  - `extract_error_pattern(error: dict) -> dict` — extracts generalizable error pattern
  - `link_error_to_pattern(error: dict, pattern_id: str, ltm: LongTermMemory)` — creates error node

**File**: `rpa/learning/error_corrector.py` (new)

- Implement `ErrorCorrector` to learn from mistakes:
  - `analyze_correction(wrong_code: str, correct_code: str, error: dict, language: str) -> dict`
    - Identifies what changed
    - Classifies the fix type (add syntax, fix operator, rename variable, etc.)
    - Returns: `{"fix_type": str, "changes": List[str], "explanation": str}`
  - `store_error_pattern(error: dict, correction: dict, session_id: str, episodic: EpisodicMemory)`
    - Logs error and correction to episodic memory
    - Creates error node in LTM with correction link
  - `suggest_similar_patterns(error: dict, ltm: LongTermMemory) -> List[Node]`
    - Finds patterns that might have similar errors

**File**: `rpa/learning/error_prevention.py` (new)

- Implement `ErrorPrevention` to avoid repeating mistakes:
  - `flag_similar_patterns(error: dict, ltm: LongTermMemory) -> List[Node]`
    - Finds patterns with similar structure to error
    - Marks for review or re-validation
  - `suggest_validation_rules(error: dict, language: str) -> List[str]`
    - Recommends validation rules to prevent similar errors
  - `apply_validation_rules(pattern_id: str, rules: List[str], ltm: LongTermMemory) -> dict`
    - Adds validation rules to pattern metadata

### 4.3 Abstraction Layer for Concept Formation

**File**: `rpa/learning/abstraction_engine.py` (new)

- Implement `AbstractionEngine` to form higher-level concepts:
  - `detect_pattern_similarity(pattern_ids: List[str], ltm: LongTermMemory) -> dict`
    - Finds structural or semantic similarities
    - Returns: `{"similarity_score": float, "common_elements": List[str], "differences": List[str]}`
  - `form_abstract_concept(pattern_ids: List[str], concept_label: str, domain: str, ltm: LongTermMemory) -> Node`
    - Creates abstract node representing common concept
    - Links concrete patterns to abstract concept
    - Example: `for_loop_python`, `for_loop_javascript` → `iteration_concept`
  - `identify_abstraction_opportunities(ltm: LongTermMemory, domain: str) -> List[dict]`
    - Scans LTM for patterns that could be abstracted
    - Returns: `[{"patterns": List[str], "suggested_concept": str, "confidence": str}]`
  - `link_concrete_to_abstract(concrete_id: str, abstract_id: str, ltm: LongTermMemory)`
    - Creates `IS_INSTANCE_OF` edge from concrete to abstract

**File**: `rpa/learning/concept_validator.py` (new)

- Implement `ConceptValidator` to ensure abstractions are valid:
  - `validate_abstraction(abstract_id: str, concrete_ids: List[str], ltm: LongTermMemory) -> dict`
    - Checks that all concrete patterns truly share the abstract concept
    - Returns: `{"is_valid": bool, "issues": List[str], "coverage": float}`
  - `test_abstraction(abstract_id: str, ltm: LongTermMemory) -> dict`
    - Generates test cases for abstract concept
    - Validates that all concrete instances pass
    - Returns: `{"all_pass": bool, "failures": List[str]}`

### 4.4 Truth Management & Knowledge Integrity

**File**: `rpa/memory/pattern_versioning.py` (new)

- Implement `PatternVersioning` for knowledge evolution:
  - `create_pattern_version(pattern_id: str, changes: dict, reason: str, session_id: str, ltm: LongTermMemory) -> str`
    - Creates new version of pattern with changes
    - Stores old version as deprecated
    - Returns new version ID
  - `get_pattern_history(pattern_id: str, ltm: LongTermMemory) -> List[dict]`
    - Returns all versions of a pattern with timestamps and reasons
  - `rollback_pattern(pattern_id: str, version_id: str, ltm: LongTermMemory)`
    - Reverts pattern to previous version
  - `merge_pattern_versions(pattern_id_1: str, pattern_id_2: str, ltm: LongTermMemory) -> str`
    - Merges two conflicting patterns into unified version

**File**: `rpa/memory/source_tracking.py` (new)

- Implement `SourceTracker` to maintain knowledge provenance:
  - `track_pattern_source(pattern_id: str, source: dict, ltm: LongTermMemory)`
    - Records: dataset name, curriculum batch, session ID, timestamp, reviewer
  - `get_pattern_sources(pattern_id: str, ltm: LongTermMemory) -> List[dict]`
    - Returns all sources that contributed to pattern
  - `identify_conflicting_sources(pattern_id: str, ltm: LongTermMemory) -> List[dict]`
    - Finds sources with conflicting information
  - `deprecate_source(source_id: str, reason: str, ltm: LongTermMemory)`
    - Marks all patterns from source as needing review

**File**: `rpa/memory/knowledge_integrity.py` (new)

- Implement `KnowledgeIntegrity` to detect and resolve conflicts:
  - `detect_conflicts(ltm: LongTermMemory) -> List[dict]`
    - Finds patterns with conflicting definitions or relationships
    - Returns: `[{"pattern_id": str, "conflicts": List[str], "severity": str}]`
  - `resolve_conflict(pattern_id: str, conflict_id: str, resolution: str, ltm: LongTermMemory)`
    - Resolves conflict by choosing one version or merging
    - Logs resolution to episodic memory
  - `validate_knowledge_consistency(ltm: LongTermMemory) -> dict`
    - Checks entire LTM for consistency
    - Returns: `{"is_consistent": bool, "conflicts": int, "issues": List[str]}`

### 4.5 Memory Management & Optimization

**File**: `rpa/memory/memory_optimizer.py` (new)

- Implement `MemoryOptimizer` for efficiency:
  - `analyze_memory_usage(ltm: LongTermMemory) -> dict`
    - Returns: `{"total_nodes": int, "total_edges": int, "unused_patterns": int, "redundant_patterns": int}`
  - `identify_unused_patterns(ltm: LongTermMemory, min_age_days: int = 30) -> List[Node]`
    - Finds patterns not used in recent sessions
  - `identify_redundant_patterns(ltm: LongTermMemory) -> List[tuple]`
    - Finds patterns with identical or near-identical composition
  - `compress_redundant_patterns(pattern_ids: List[str], ltm: LongTermMemory) -> dict`
    - Merges redundant patterns, updates references
    - Returns: `{"merged_count": int, "references_updated": int}`
  - `prune_unused_patterns(pattern_ids: List[str], ltm: LongTermMemory, archive: bool = True)`
    - Removes unused patterns (optionally archives)

**File**: `rpa/memory/reinforcement_tracker.py` (new)

- Implement `ReinforcementTracker` to measure pattern usage:
  - `track_pattern_usage(pattern_id: str, session_id: str, context: str)`
    - Logs each time pattern is used
  - `get_usage_frequency(pattern_id: str, time_window: str = "all") -> int`
    - Returns usage count in time window
  - `get_most_used_patterns(ltm: LongTermMemory, limit: int = 10) -> List[tuple]`
    - Returns patterns ranked by usage frequency
  - `identify_learning_gaps(ltm: LongTermMemory) -> List[dict]`
    - Finds patterns with low usage (might indicate gaps)

---

## Phase 5: Multi-Agent System & Orchestration (Weeks 11-12)

### 5.1 Domain-Specific Agent Framework

**File**: `rpa/agents/base_agent.py` (new)

- Implement `BaseAgent` as template for specialized agents:
  ```python
  class BaseAgent:
      def __init__(self, domain: str, agent_id: str):
          self.domain = domain
          self.agent_id = agent_id
          self.ltm = LongTermMemory()
          self.episodic = EpisodicMemory()
      
      def query(self, question: str) -> str
      def teach(self, lesson: dict) -> dict
      def assess(self, pattern_id: str) -> dict
      def ask_inquiry(self) -> str
      def answer_inquiry(self, inquiry_id: str, response: str) -> dict
      def execute_code(self, code: str) -> dict  # for coding agents
      def get_status(self) -> dict
  ```

**File**: `rpa/agents/coding_agent.py` (new)

- Implement `CodingAgent` for code generation and analysis:
  - Extends `BaseAgent` with:
    - `generate_code(task: str, language: str) -> str`
    - `refactor_code(code: str, language: str) -> str`
    - `review_code(code: str, language: str) -> dict`
    - `debug_code(code: str, error: str, language: str) -> str`
    - `execute_code(code: str) -> dict` — uses sandbox

**File**: `rpa/agents/language_agent.py` (new)

- Implement `LanguageAgent` for natural language understanding:
  - Extends `BaseAgent` with:
    - `parse_sentence(sentence: str) -> dict`
    - `generate_sentence(components: dict) -> str`
    - `explain_concept(concept: str) -> str`
    - `translate_concept(concept: str, from_domain: str, to_domain: str) -> str`

**File**: `rpa/agents/domain_agent.py` (new)

- Implement `DomainAgent` as extensible template:
  - Allows creation of agents for any domain (business, legal, design, etc.)
  - Inherits all base functionality
  - Customizable output generation per domain

### 5.2 Agent Registry & Discovery

**File**: `rpa/agents/agent_registry.py` (new)

- Implement `AgentRegistry` for agent management:
  - `register_agent(agent: BaseAgent) -> str` — registers agent, returns ID
  - `get_agent(agent_id: str) -> BaseAgent` — retrieves agent
  - `list_agents(domain: str = None) -> List[BaseAgent]` — lists all or domain-specific agents
  - `get_agent_capabilities(agent_id: str) -> dict` — returns agent's methods and domains
  - `deregister_agent(agent_id: str)` — removes agent

### 5.3 Agent Communication & Orchestration

**File**: `rpa/agents/agent_messenger.py` (new)

- Implement `AgentMessenger` for inter-agent communication:
  - `send_query(from_agent_id: str, to_agent_id: str, query: str) -> str`
    - One agent queries another
  - `send_teaching(from_agent_id: str, to_agent_id: str, lesson: dict) -> dict`
    - One agent teaches another
  - `broadcast_inquiry(inquiry: str, domains: List[str]) -> List[tuple]`
    - Sends inquiry to all agents in specified domains
  - `coordinate_task(task: str, agents: List[str]) -> dict`
    - Orchestrates multi-agent task execution

**File**: `rpa/agents/orchestrator.py` (new)

- Implement `Orchestrator` for task delegation:
  - `decompose_task(task: str) -> List[dict]`
    - Breaks task into subtasks
  - `assign_subtasks(subtasks: List[dict], agents: List[BaseAgent]) -> dict`
    - Assigns subtasks to appropriate agents
  - `execute_orchestrated_task(task: str, agents: List[BaseAgent]) -> dict`
    - Coordinates full task execution across agents
  - `aggregate_results(results: List[dict]) -> dict`
    - Combines results from multiple agents

### 5.4 Shared Knowledge Graph

**File**: `rpa/agents/shared_knowledge.py` (new)

- Implement `SharedKnowledge` for cross-agent learning:
  - `share_pattern(pattern_id: str, from_agent_id: str, to_agent_ids: List[str], ltm: LongTermMemory)`
    - Shares pattern from one agent to others
  - `link_cross_domain_patterns(pattern_id_1: str, agent_id_1: str, pattern_id_2: str, agent_id_2: str)`
    - Creates cross-domain links between patterns
  - `get_shared_patterns(agent_id: str) -> List[Node]`
    - Returns patterns shared with agent
  - `track_knowledge_flow(from_agent_id: str, to_agent_id: str) -> dict`
    - Tracks what knowledge flows between agents

---

## Phase 6: System Integrity & Safety (Weeks 13-14)

### 6.1 Curriculum Ingestion Discipline

**File**: `rpa/preprocessing/ingestion_validator.py` (new)

- Implement `IngestionValidator` to enforce quality:
  - `validate_curriculum_batch(batch: dict) -> dict`
    - Checks: structure, completeness, consistency
    - Returns: `{"is_valid": bool, "issues": List[str], "warnings": List[str]}`
  - `validate_dataset_source(dataset_name: str, sample_size: int = 100) -> dict`
    - Validates dataset before full ingestion
    - Checks: format, encoding, content quality
  - `pre_approve_batch(batch: dict, reviewer_id: str, approval_notes: str)`
    - Requires human approval before ingestion
  - `track_ingestion_source(batch_id: str, source: dict, ltm: LongTermMemory)`
    - Records source and approval for audit trail

### 6.2 Recursive Loop Prevention

**File**: `rpa/learning/loop_detector.py` (new)

- Implement `LoopDetector` to prevent infinite recursion:
  - `detect_circular_references(node_id: str, ltm: LongTermMemory) -> List[List[str]]`
    - Finds cycles in pattern graph
  - `detect_infinite_recursion(pattern_id: str, max_depth: int = 100) -> bool`
    - Checks if pattern would recurse infinitely
  - `break_circular_reference(cycle: List[str], ltm: LongTermMemory) -> dict`
    - Suggests how to break cycle
  - `validate_recursion_depth(pattern_id: str, ltm: LongTermMemory) -> dict`
    - Ensures recursion depth is reasonable

### 6.3 Pattern Validation Framework

**File**: `rpa/validation/pattern_validator.py` (new)

- Implement `PatternValidator` for comprehensive validation:
  - `validate_pattern_complete(pattern_id: str, ltm: LongTermMemory) -> dict`
    - Checks: all children exist, all edges resolve, no orphans
  - `validate_pattern_consistent(pattern_id: str, ltm: LongTermMemory) -> dict`
    - Checks: no conflicting definitions, consistent hierarchy
  - `validate_pattern_executable(pattern_id: str, ltm: LongTermMemory) -> dict`
    - For code patterns: checks syntax, runs tests
  - `validate_pattern_semantically(pattern_id: str, ltm: LongTermMemory) -> dict`
    - Checks: meaning is clear, no ambiguity

### 6.4 System Health Monitoring

**File**: `rpa/monitoring/system_health.py` (new)

- Implement `SystemHealth` for continuous monitoring:
  - `check_memory_health(ltm: LongTermMemory) -> dict`
    - Returns: `{"is_healthy": bool, "issues": List[str], "metrics": dict}`
  - `check_pattern_health(ltm: LongTermMemory) -> dict`
    - Checks for orphaned, circular, or invalid patterns
  - `check_learning_health(episodic: EpisodicMemory) -> dict`
    - Checks learning rate, error patterns, consolidation success
  - `generate_health_report(ltm: LongTermMemory, episodic: EpisodicMemory) -> dict`
    - Comprehensive system health report

---

## Phase 7: Benchmarking & Progress Tracking (Weeks 15-16)

### 7.1 Standardized Test Suite

**File**: `rpa/benchmarking/test_suite.py` (new)

- Implement `BenchmarkSuite` with standard tests:
  - **Language Tests**:
    - Vocabulary recall (100 words)
    - Sentence construction (50 sentences)
    - Grammar rules (20 rules)
    - Paragraph understanding (10 paragraphs)
  - **Coding Tests**:
    - Syntax validation (50 code snippets)
    - Code generation (20 tasks)
    - Code review (10 code samples)
    - Debugging (10 broken code samples)
  - **Cross-Domain Tests**:
    - Concept linking (10 concept pairs)
    - Multi-agent coordination (5 tasks)

### 7.2 Progress Tracking

**File**: `rpa/benchmarking/progress_tracker.py` (new)

- Implement `ProgressTracker`:
  - `run_benchmark(agent: BaseAgent, test_suite: BenchmarkSuite) -> dict`
    - Runs all tests, returns results
  - `track_progress_over_time(agent_id: str) -> List[dict]`
    - Returns benchmark results over time
  - `compare_agents(agent_ids: List[str]) -> dict`
    - Compares performance across agents
  - `identify_improvement_areas(agent_id: str) -> List[str]`
    - Suggests where agent needs improvement

---

## Updated Implementation Roadmap

### Week 9-10: Production Hardening & Execution
- [ ] Implement sandboxed code execution layer
- [ ] Implement error classification and correction system
- [ ] Implement execution logging and analysis
- [ ] Test code execution with 50+ Python snippets

### Week 11-12: Multi-Agent System
- [ ] Implement base agent framework
- [ ] Implement coding agent and language agent
- [ ] Implement agent registry and discovery
- [ ] Implement agent communication and orchestration
- [ ] Test multi-agent coordination on 5 tasks

### Week 13-14: System Integrity & Safety
- [ ] Implement curriculum ingestion validator
- [ ] Implement recursive loop detector
- [ ] Implement comprehensive pattern validator
- [ ] Implement system health monitoring
- [ ] Validate system integrity across all components

### Week 15-16: Benchmarking & Progress
- [ ] Implement standardized test suite
- [ ] Implement progress tracking
- [ ] Run initial benchmarks on all agents
- [ ] Document baseline performance metrics
- [ ] Create performance improvement roadmap

---

## Updated Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Tests passing | 300+ | 261 ✓ |
| Code execution success rate | 95%+ | TBD |
| Error classification accuracy | 90%+ | TBD |
| Abstraction formation | 10+ concepts | TBD |
| Multi-agent coordination | 5+ tasks | TBD |
| System health score | 95%+ | TBD |
| Benchmark baseline | Established | TBD |
| Agent scalability | 10+ agents | TBD |

---

## Core Philosophy (Preserved Throughout)

✓ **Deterministic** — no probabilistic outputs
✓ **Memory-driven** — STM, LTM, episodic memory
✓ **Curriculum-fed** — only verified, structured data
✓ **Teachable** — human + system guidance
✓ **Token-free** — immune to tokenization attacks
✓ **Secure** — sandboxed execution, validated knowledge
✓ **Scalable** — multi-agent architecture
✓ **Intelligent** — abstraction, error understanding, truth management
