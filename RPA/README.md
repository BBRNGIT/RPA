# Recursive Pattern Agent (RPA)

A token-free AI learning system that builds knowledge hierarchically from characters to complex patterns.

## Architecture

```
rpa/
├── core/           # Node, Edge, Pattern Graph
├── memory/         # STM, LTM, Episodic Memory
├── learning/       # Ingestion, Correction, Integration
├── inquiry/        # Gap Detection, Question Generation
├── assessment/     # Self-Assessment, Validation
├── datasets/       # Gutenberg, Wikipedia Loaders
├── advanced/       # Cross-Domain Links, Auto-Generation
└── performance/    # Metrics Tracking
```

## Key Features

- **Token-Free Learning**: No vocabulary, no tokenizer vulnerabilities
- **Hierarchical Knowledge**: Characters → Words → Phrases → Sentences
- **Memory Systems**: STM for new patterns, LTM for validated knowledge
- **Gap Detection**: Proactively identifies knowledge gaps
- **Cross-Domain Linking**: Connects concepts across domains

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Core System (Memory, Graph, Validation) | Pending |
| 2 | Proactive Inquiry System | Pending |
| 3 | Enhanced Learning | Pending |
| 4 | Dataset Integration | Pending |
| 5 | Advanced Features | Pending |

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
RPA/
├── .git/           # Version control
├── .gitignore      # Ignore patterns
├── README.md       # This file
├── WORKLOG.md      # Detailed progress log
├── rpa/            # Main package
├── tests/          # Test suite
└── backups/        # Phase backups
```

## Safety Features

- All patterns validated before LTM storage
- Human review queue for flagged content
- No external tokenization = no token-based attacks
- Character-level validation with unicode normalization

---

*Built with security-first, token-free architecture.*
