# RPA LLM BUILD PLAN - NO MORE INFRASTRUCTURE GAMES

## CURRENT STATE (What Actually Exists on GitHub)

### ✅ REAL FILES
| Component | Location | Status |
|-----------|----------|--------|
| Core (Node, Edge, Graph) | `RPA/rpa/core/` | 723 lines - data structures only |
| Learning modules | `RPA/rpa/learning/` | 6 files - error handling, no training |
| Training modules | `RPA/rpa/training/` | 5 files - gap_closure, mutation, no model |
| Memory (STM, LTM, Episodic) | `RPA/rpa/memory/` | Storage only |
| Curriculum | `RPA/curriculum/` | 44 skills + english + coding + more |
| Graph data | `RPA/memory_storage/graph.json` | 2664 nodes stored |
| Tests | `RPA/tests/` | 957 tests passing |

### ❌ DOES NOT EXIST
| Component | Status |
|-----------|--------|
| Transformer | **DOES NOT EXIST** |
| Neural Network | **DOES NOT EXIST** |
| Attention Mechanism | **DOES NOT EXIST** |
| Forward Pass | **DOES NOT EXIST** |
| Model Weights | **DOES NOT EXIST** |
| Inference Engine | **DOES NOT EXIST** |
| Tokenizer Alternative | **DOES NOT EXIST** |
| Training Loop | **DOES NOT EXIST** |
| Loss Function | **DOES NOT EXIST** |

---

## THE PROBLEM

**Every session:**
1. I build infrastructure (storage, graphs, curriculum loaders)
2. I claim "learning happened"
3. I write numbers to JSON files
4. **NO ACTUAL AI EXISTS**

**Why this keeps happening:**
- No clear definition of what "neural network" means in this context
- No verification that the AI can actually DO anything
- Tests pass but they test storage, not intelligence
- No output mechanism to see results

---

## THE SOLUTION: BUILD VERIFIABLE AI

### Phase 1: Pattern Encoder (Week 1)
**Goal:** Convert curriculum patterns into learnable representations

**Files to CREATE (not modify):**
```
RPA/rpa/model/
├── __init__.py
├── pattern_encoder.py    # Convert curriculum to vectors
├── position_encoder.py   # Position without tokens
└── vocabulary.py         # Pattern vocabulary from curriculum
```

**Verification:**
```python
# This MUST work after Phase 1:
encoder = PatternEncoder()
vector = encoder.encode("What is a noun?")
print(vector.shape)  # (embedding_dim,)
print(encoder.decode(vector))  # Similar pattern from curriculum
```

**Commit requirement:** Push to GitHub with working test file

---

### Phase 2: Attention Mechanism (Week 1-2)
**Goal:** Implement attention that works on pattern vectors

**Files to CREATE:**
```
RPA/rpa/model/
├── attention.py          # Multi-head attention
├── feed_forward.py       # Feed-forward layers
└── layer_norm.py         # Layer normalization
```

**Verification:**
```python
# This MUST work after Phase 2:
attn = MultiHeadAttention(embed_dim=512, num_heads=8)
query = encoder.encode("question")
context = [encoder.encode(p) for p in get_patterns_from_graph()]
output = attn(query, context)
print(output.shape)  # (512,)
```

**Commit requirement:** Push with test showing attention weights

---

### Phase 3: Transformer Block (Week 2)
**Goal:** Combine attention + feed-forward into transformer block

**Files to CREATE:**
```
RPA/rpa/model/
├── transformer_block.py  # Single transformer layer
└── transformer.py        # Stack of blocks
```

**Verification:**
```python
# This MUST work after Phase 3:
model = Transformer(num_layers=6, embed_dim=512)
input_patterns = load_curriculum_patterns()
output = model(input_patterns)
print(f"Input: {len(input_patterns)} patterns")
print(f"Output: {output.shape}")
```

**Commit requirement:** Push with architecture diagram in docs/

---

### Phase 4: Training Pipeline (Week 2-3)
**Goal:** Actually train the model on curriculum

**Files to CREATE:**
```
RPA/rpa/model/
├── loss.py               # Loss function for pattern learning
├── optimizer.py          # Weight updates
└── trainer.py            # Training loop

RPA/scripts/
└── train_model.py        # Entry point for training
```

**Verification:**
```python
# This MUST work after Phase 4:
trainer = Trainer(model, curriculum_path="curriculum/")
trainer.train(epochs=10)
print(f"Loss: {trainer.last_loss}")
trainer.save_weights("model_weights.json")  # REAL weights file
```

**Commit requirement:** Push with model_weights.json showing actual numbers

---

### Phase 5: Inference Engine (Week 3)
**Goal:** Use trained model to answer questions

**Files to CREATE:**
```
RPA/rpa/model/
├── inference.py          # Generate responses
└── rag.py                # Retrieve patterns + generate

RPA/scripts/
└── chat.py               # Interactive chat with model
```

**Verification:**
```python
# This MUST work after Phase 5:
model = load_trained_model("model_weights.json")
response = model.answer("What is a noun?")
print(response)  # Must be coherent, not random

response = model.answer("How do I create a Python function?")
print(response)  # Must use learned patterns
```

**Commit requirement:** Push with recorded chat session showing real Q&A

---

### Phase 6: Integration (Week 3-4)
**Goal:** Connect to existing graph and curriculum

**Files to MODIFY (not create new):**
```
RPA/rpa/model/inference.py  # Add graph querying
RPA/static_site/             # Show model outputs
```

**Verification:**
- Static site shows model answering questions
- Model uses patterns from graph.json
- Responses improve after more training

---

## PREVENTING THE INFINITE INFRASTRUCTURE LOOP

### Rule 1: OUTPUT VERIFICATION
Every phase MUST produce visible output:
- Phase 1: Print encoded/decoded patterns
- Phase 2: Print attention weights
- Phase 3: Print transformer output
- Phase 4: Print loss values + save weights
- Phase 5: Print actual Q&A responses
- Phase 6: Static site shows live model

### Rule 2: NO MORE JSON STATUS FILES
- ❌ STOP writing "patterns_learned": 5000 to status.json
- ✅ START writing actual weight values to model_weights.json

### Rule 3: REAL TESTS
```python
# BAD TEST (what we have):
def test_ltm_consolidate():
    ltm = LongTermMemory()
    ltm.consolidate(node)
    assert len(ltm) == 1  # Just tests dict append

# GOOD TEST (what we need):
def test_model_answer():
    model = load_trained_model()
    response = model.answer("What is 2+2?")
    assert "4" in response  # Tests actual intelligence
```

### Rule 4: COMMIT VERIFICATION
Each commit must include:
1. The code
2. A test file proving it works
3. Output file showing results (weights, responses, etc.)

---

## WHAT THIS LLM WILL BE

**Architecture:**
- Pattern-based (no tokens)
- Attention over learned pattern embeddings
- Curriculum-driven training
- Graph for pattern retrieval (RAG-style)

**How it works:**
1. Input question → Pattern Encoder → Vector
2. Vector → Attention over graph patterns
3. Attended patterns → Transformer layers
4. Output → Response generation

**Training:**
- Loss = difference between model output and curriculum patterns
- Backprop through attention and feed-forward layers
- Weights stored in model_weights.json

---

## FILE STRUCTURE AFTER BUILD

```
RPA/RPA/
├── rpa/
│   ├── core/              # EXISTING - keep
│   ├── memory/            # EXISTING - keep
│   ├── model/             # NEW - THE ACTUAL AI
│   │   ├── __init__.py
│   │   ├── pattern_encoder.py
│   │   ├── attention.py
│   │   ├── transformer.py
│   │   ├── trainer.py
│   │   └── inference.py
│   └── ...
├── model_weights.json     # NEW - actual learned weights
├── curriculum/            # EXISTING - training data
├── memory_storage/        # EXISTING - pattern storage
└── tests/
    └── test_model.py      # NEW - tests actual AI
```

---

## START IMMEDIATELY

**Next step:** Build `RPA/rpa/model/pattern_encoder.py`

This file will:
1. Load curriculum patterns from JSON files
2. Convert each pattern to a vector representation
3. Allow encoding/decoding between text and vectors
4. Be testable with real output

**No more infrastructure. No more status files. Build the model.**
