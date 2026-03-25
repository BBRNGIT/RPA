#!/usr/bin/env python3
"""
ACTUALLY LEARN - Uses the REAL learning infrastructure to process curriculum.

This script uses the existing rpa.memory and rpa.core modules to:
1. Load curriculum JSON files
2. Create Node objects from curriculum items
3. Add to ShortTermMemory
4. Validate and consolidate to LongTermMemory
5. Save to disk with persistence

This is the REAL learning process, not just writing status files.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent))

from rpa.memory import ShortTermMemory, LongTermMemory, EpisodicMemory, EventType
from rpa.core import Node, Edge, PatternGraph, NodeType, EdgeType


def load_curriculum_file(filepath: Path) -> list:
    """Load a curriculum JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    # Handle different curriculum formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Check for common keys
        if "lessons" in data:
            return data["lessons"]
        elif "curriculum" in data:
            return data["curriculum"]
        elif "items" in data:
            return data["items"]
        elif "patterns" in data:
            return data["patterns"]
        else:
            # Single item or unknown format - try to extract
            return [data] if data else []

    return []


def create_node_from_curriculum(item: dict, domain: str) -> Node:
    """Create a Node from a curriculum item."""
    # Determine hierarchy level based on content type
    # Try multiple possible content fields
    content = (
        item.get("content") or 
        item.get("pattern") or 
        item.get("text") or
        item.get("instruction") or
        item.get("concept") or
        item.get("description") or
        item.get("code") or
        ""
    )
    
    # For items with instruction but no direct content, combine fields
    if not content:
        parts = []
        if item.get("concept"):
            parts.append(f"Concept: {item['concept']}")
        if item.get("instruction"):
            parts.append(f"Instruction: {item['instruction']}")
        if item.get("examples"):
            parts.append(f"Examples: {item['examples']}")
        content = " | ".join(parts)
    
    # Get label
    label = (
        item.get("label") or
        item.get("name") or
        item.get("title") or
        item.get("concept") or
        item.get("skill_name") or
        f"pattern_{uuid.uuid4().hex[:8]}"
    )
    
    # Determine node type
    if item.get("type") == "primitive" or len(content) <= 5:
        node_type = NodeType.PRIMITIVE
        hierarchy_level = 0
    elif item.get("type") == "pattern" or len(content.split()) <= 10:
        node_type = NodeType.PATTERN
        hierarchy_level = 1
    elif item.get("type") == "sequence" or len(content.split()) <= 50:
        node_type = NodeType.SEQUENCE
        hierarchy_level = 2
    else:
        node_type = NodeType.CONCEPT
        hierarchy_level = 3

    # Get hierarchy level from item if specified
    hierarchy_level = item.get("hierarchy_level", item.get("level", hierarchy_level))

    # Create node
    node = Node(
        node_id=item.get("id", item.get("lesson_id", f"node_{uuid.uuid4().hex[:8]}")),
        label=label[:100] if label else f"pattern_{uuid.uuid4().hex[:8]}",
        content=content,
        node_type=node_type,
        hierarchy_level=hierarchy_level,
        domain=item.get("domain", domain),
    )
    # Store composition/children in metadata if present
    children = item.get("composition", item.get("children", []))
    if children:
        node.metadata["children"] = children

    # Add metadata (preserve children if set above)
    node.metadata.update({
        "source": item.get("source", "curriculum"),
        "difficulty": item.get("difficulty", item.get("metadata", {}).get("difficulty", 1)),
        "created_at": datetime.now().isoformat(),
        "raw": {k: v for k, v in item.items() if k not in ["content", "label", "id"]}
    })

    return node


def learn_from_curriculum(storage_path: Path, verbose: bool = True):
    """
    Actually learn from curriculum files using the real infrastructure.
    """
    curriculum_dir = Path(__file__).parent / "curriculum"

    if verbose:
        print("="*70)
        print("  RPA ACTUAL LEARNING - Using Real Infrastructure")
        print("="*70)
        print(f"  Storage: {storage_path}")
        print(f"  Curriculum dir: {curriculum_dir}")
        print()

    # Initialize memory systems WITH PERSISTENCE
    stm = ShortTermMemory()
    ltm = LongTermMemory(storage_path=storage_path)
    episodic = EpisodicMemory()

    # Load existing LTM if available
    ltm.load()
    existing_patterns = len(ltm)
    if verbose:
        print(f"  Existing patterns in LTM: {existing_patterns}")

    # Create session
    session_id = stm.create_session(metadata={
        "learning": True,
        "started_at": datetime.now().isoformat(),
        "source": "actually_learn.py"
    })

    # Track statistics
    stats = {
        "files_processed": 0,
        "items_found": 0,
        "learned": 0,
        "validated": 0,
        "consolidated": 0,
        "rejected": 0,
        "errors": 0,
    }

    # Find all curriculum files
    curriculum_files = []
    for subdir in ["skills", "english", "coding", "reasoning", "medicine", "finance", "health", "generated"]:
        subdir_path = curriculum_dir / subdir
        if subdir_path.exists():
            curriculum_files.extend(subdir_path.glob("*.json"))

    if verbose:
        print(f"\n  Found {len(curriculum_files)} curriculum files")
        print()

    # Process each file
    for filepath in curriculum_files:
        try:
            domain = filepath.parent.name
            items = load_curriculum_file(filepath)
            stats["files_processed"] += 1
            stats["items_found"] += len(items)

            if verbose and len(items) > 0:
                print(f"  📁 {filepath.name}: {len(items)} items ({domain})")

            for item in items:
                try:
                    # Create node from curriculum item
                    node = create_node_from_curriculum(item, domain)

                    # Add to STM
                    stm.add_pattern(node)
                    stats["learned"] += 1

                    # Validate (basic checks)
                    is_valid = bool(node.content and len(node.content.strip()) >= 2)

                    if is_valid:
                        # Mark as validated
                        stm.mark_validated(node.node_id)
                        stats["validated"] += 1

                        # CONSOLIDATE TO LTM (THIS IS THE KEY STEP)
                        ltm.consolidate(
                            node=node,
                            session_id=session_id,
                            validation_score=1.0,
                            source=f"curriculum/{domain}/{filepath.name}"
                        )
                        stats["consolidated"] += 1
                    else:
                        stm.mark_rejected(node.node_id)
                        stats["rejected"] += 1

                except Exception as e:
                    stats["errors"] += 1
                    if verbose and stats["errors"] <= 5:
                        print(f"    ⚠️ Error processing item: {e}")

        except Exception as e:
            if verbose:
                print(f"  ❌ Error loading {filepath.name}: {e}")

    # SAVE TO DISK - THIS IS CRITICAL
    if verbose:
        print(f"\n  💾 Saving LTM to disk...")

    ltm.save()

    # Record session in episodic memory
    episodic.log_event(
        event_type=EventType.SESSION_ENDED,
        data={
            "session_id": session_id,
            "stats": stats,
            "patterns_in_ltm": len(ltm),
        }
    )

    # Print summary
    if verbose:
        print()
        print("="*70)
        print("  LEARNING COMPLETE - REAL DATA NOW IN GRAPH")
        print("="*70)
        print(f"  Files processed:    {stats['files_processed']}")
        print(f"  Items found:        {stats['items_found']}")
        print(f"  Learned (STM):      {stats['learned']}")
        print(f"  Validated:          {stats['validated']}")
        print(f"  Consolidated (LTM): {stats['consolidated']}")
        print(f"  Rejected:           {stats['rejected']}")
        print(f"  Errors:             {stats['errors']}")
        print()
        print(f"  BEFORE: {existing_patterns} patterns in LTM")
        print(f"  AFTER:  {len(ltm)} patterns in LTM")
        print(f"  GAIN:   {len(ltm) - existing_patterns} new patterns")
        print()
        print(f"  Storage: {storage_path}")
        print("="*70)

    return {
        "session_id": session_id,
        "stats": stats,
        "patterns_before": existing_patterns,
        "patterns_after": len(ltm),
        "ltm": ltm
    }


def verify_learning(storage_path: Path):
    """Verify that learning actually happened by checking the files."""
    print("\n" + "="*70)
    print("  VERIFICATION - Checking Saved Files")
    print("="*70)

    # Check graph.json
    graph_path = storage_path / "graph.json"
    if graph_path.exists():
        with open(graph_path) as f:
            graph_data = json.load(f)
        nodes = graph_data.get("nodes", {})
        edges = graph_data.get("edges", {})
        print(f"  graph.json: {len(nodes)} nodes, {len(edges)} edges")

        # Sample some nodes
        if nodes:
            print("\n  Sample nodes:")
            for i, (nid, node) in enumerate(list(nodes.items())[:3]):
                print(f"    {i+1}. {node.get('label', 'unnamed')[:40]}")
                print(f"       Domain: {node.get('domain', 'unknown')}, Level: {node.get('hierarchy_level', '?')}")

    # Check metadata.json
    meta_path = storage_path / "metadata.json"
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        stats = meta.get("stats", {})
        print(f"\n  metadata.json:")
        print(f"    patterns_consolidated: {stats.get('patterns_consolidated', 0)}")
        print(f"    queries_total: {stats.get('queries_total', 0)}")

    # Check consolidation_records.json
    records_path = storage_path / "consolidation_records.json"
    if records_path.exists():
        with open(records_path) as f:
            records = json.load(f)
        print(f"\n  consolidation_records.json: {len(records)} records")

    print("="*70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Actually learn from curriculum")
    parser.add_argument("--storage", type=str, default="memory_storage",
                       help="Storage directory for LTM")
    parser.add_argument("--quiet", action="store_true",
                       help="Less verbose output")

    args = parser.parse_args()

    storage_path = Path(__file__).parent / args.storage

    # Run actual learning
    result = learn_from_curriculum(storage_path, verbose=not args.quiet)

    # Verify it worked
    verify_learning(storage_path)

    print(f"\n✅ Done. LTM now has {result['patterns_after']} patterns.")
