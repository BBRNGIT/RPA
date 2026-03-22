#!/usr/bin/env python3
"""
RPA Training Script - Train with dataset samples.

Usage:
    python train.py --dataset mbpp --sample 10 --verbose
    python train.py --dataset humaneval --sample 5 --verbose
    python train.py --phase 1 --output curriculum/trained/
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import hashlib

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
CONFIG_PATH = Path(__file__).parent / "config" / "datasets.json"


def load_config():
    """Load dataset configuration."""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_dataset_sample(dataset_name, sample_size=10, verbose=True):
    """Load a sample from a Hugging Face dataset."""
    if verbose:
        print(f"\n📡 Loading dataset: {dataset_name}")
        print(f"   Sample size: {sample_size}")
    
    from datasets import load_dataset
    
    config = load_config()["datasets"].get(dataset_name)
    if not config:
        print(f"❌ Dataset '{dataset_name}' not found in config")
        return None
    
    # Build kwargs
    kwargs = {
        "path": config.get("dataset_name"),
        "split": config.get("split", "train"),
    }
    if config.get("config_name"):
        kwargs["name"] = config["config_name"]
    
    if verbose:
        print(f"   HF path: {kwargs['path']}")
    
    # Load dataset
    dataset = load_dataset(**kwargs)
    
    # Get sample
    if config.get("streaming", False):
        items = []
        for i, item in enumerate(dataset):
            if i >= sample_size:
                break
            items.append(item)
    else:
        items = [dataset[i] for i in range(min(sample_size, len(dataset)))]
    
    if verbose:
        print(f"   ✅ Loaded {len(items)} items")
    
    return items, config


def convert_to_curriculum(items, dataset_config, verbose=True):
    """Convert raw dataset items to curriculum format."""
    curriculum = []
    domain = dataset_config.get("domain", "general")
    curriculum_type = dataset_config.get("curriculum_type", "unknown")
    fields = dataset_config.get("fields", {})
    
    if verbose:
        print(f"\n🔄 Converting to curriculum format...")
        print(f"   Domain: {domain}")
        print(f"   Type: {curriculum_type}")
    
    for i, item in enumerate(items):
        # Extract content based on curriculum type
        if curriculum_type == "coding_problems":
            content = item.get(fields.get("code", "code"), "")
            # Try multiple text fields (MBPP uses 'text', others may use 'prompt')
            description = item.get(fields.get("text", "text"), "") or item.get("prompt", "")
            hierarchy_level = 2
            
        elif curriculum_type == "coding_functions":
            content = item.get(fields.get("code", "canonical_solution"), "")
            description = item.get(fields.get("description", "prompt"), "")
            hierarchy_level = 3
            
        elif curriculum_type == "natural_language":
            content = item.get(fields.get("text", "text"), "")
            description = item.get(fields.get("title", "title"), "")
            hierarchy_level = 1
            
        elif curriculum_type == "qa_pairs":
            content = item.get(fields.get("context", "context"), "")
            description = item.get(fields.get("question", "question"), "")
            hierarchy_level = 2
            
        elif curriculum_type == "code_with_docstring":
            content = item.get(fields.get("code", "func_code_string"), "")
            description = item.get(fields.get("docstring", "func_documentation_string"), "")
            hierarchy_level = 3
            
        else:
            content = str(item.get("text", item.get("code", "")))
            description = ""
            hierarchy_level = 1
        
        # Skip empty content
        if not content or not content.strip():
            continue
        
        # Generate composition (tokens)
        if domain == "english":
            composition = content.split()[:50]
        else:
            # For code, use character-level with space marker
            composition = list(content.replace(" ", "␣"))[:100]
        
        # Generate unique ID
        unique_id = hashlib.md5(f"{domain}_{curriculum_type}_{i}".encode()).hexdigest()[:8]
        
        # Build curriculum item
        curriculum_item = {
            "lesson_id": f"{domain[:2]}_{curriculum_type[:3]}_{i:04d}_{unique_id}",
            "content": content[:500] if content else "",
            "label": description[:50] if description else f"pattern_{i}",
            "type": "pattern",
            "hierarchy_level": hierarchy_level,
            "domain": domain,
            "composition": composition,
            "metadata": {
                "source": dataset_config.get("dataset_name", "unknown"),
                "curriculum_type": curriculum_type,
                "description": description[:200] if description else "",
                "difficulty": min(hierarchy_level, 4),
                "raw_fields": list(item.keys())[:5]
            },
            "created_at": datetime.now().isoformat()
        }
        
        curriculum.append(curriculum_item)
    
    if verbose:
        print(f"   ✅ Converted {len(curriculum)} curriculum items")
    
    return curriculum


def train_rpa(curriculum, verbose=True, storage_path=None):
    """Train RPA with curriculum items."""
    from rpa.memory import ShortTermMemory, LongTermMemory, EpisodicMemory, EventType
    from rpa.core import Node, PatternGraph
    from rpa.validation import Validator
    
    if verbose:
        print(f"\n🧠 Training RPA System...")
        print(f"   Initializing memory systems...")
    
    # Initialize with optional storage path for persistence
    stm = ShortTermMemory()
    ltm = LongTermMemory(storage_path=storage_path)
    episodic = EpisodicMemory()
    
    # Load existing memory if available
    if storage_path:
        ltm.load()
        if verbose:
            print(f"   Existing patterns in LTM: {len(ltm)}")
    
    # Create a pattern graph for validation
    graph = PatternGraph(domain="training")
    
    # Create session
    session_id = stm.create_session(metadata={
        "training": True,
        "curriculum_size": len(curriculum),
        "started_at": datetime.now().isoformat()
    })
    
    if verbose:
        print(f"   Session: {session_id}")
        print(f"\n   {'─'*56}")
        print(f"   {'Item':<6} {'Label':<25} {'Level':<6} {'Status'}")
        print(f"   {'─'*56}")
    
    stats = {
        "learned": 0,
        "validated": 0,
        "consolidated": 0,
        "rejected": 0
    }
    
    for i, item in enumerate(curriculum):
        # Create node
        node = Node.create_pattern(
            label=item.get("label", f"pattern_{i}"),
            content=item.get("content", ""),
            hierarchy_level=item.get("hierarchy_level", 1),
            domain=item.get("domain", "general")
        )
        node.metadata = item.get("metadata", {})
        
        # Add to STM
        stm.add_pattern(node)
        stats["learned"] += 1
        
        # Add to graph for validation
        graph.add_node(node)
        
        # Basic validation (content exists, has label)
        is_valid = bool(node.content and node.content.strip())
        
        # Additional checks
        issues = []
        if not node.label:
            issues.append("Missing label")
        if len(node.content) < 5:
            issues.append("Content too short")
        
        if is_valid and not issues:
            # Mark as validated
            stm.mark_validated(node.node_id)
            stats["validated"] += 1
            
            # Consolidate to LTM
            ltm.consolidate(
                node=node,
                session_id=session_id,
                validation_score=1.0,
                source=item.get("metadata", {}).get("source", "curriculum")
            )
            stats["consolidated"] += 1
            status = "✅ Consolidated"
        else:
            stm.mark_rejected(node.node_id)
            stats["rejected"] += 1
            status = f"❌ Rejected ({', '.join(issues) if issues else 'validation failed'})"
        
        if verbose:
            label_short = node.label[:22] + "..." if len(node.label) > 22 else node.label
            print(f"   {i+1:<6} {label_short:<25} {node.hierarchy_level:<6} {status}")
    
    # Save to disk if storage path provided
    if storage_path:
        ltm.save()
        if verbose:
            print(f"\n   💾 Saved to: {storage_path}")
    
    if verbose:
        print(f"   {'─'*56}")
        print(f"\n   📊 Training Statistics:")
        print(f"      Learned:     {stats['learned']}")
        print(f"      Validated:   {stats['validated']}")
        print(f"      Consolidated:{stats['consolidated']}")
        print(f"      Rejected:    {stats['rejected']}")
        
        print(f"\n   📈 Memory State:")
        print(f"      STM:  {len(stm)} patterns")
        print(f"      LTM:  {len(ltm)} patterns")
        print(f"      Episodic: {len(episodic)} events")
    
    return {
        "session_id": session_id,
        "stats": stats,
        "stm_size": len(stm),
        "ltm_size": len(ltm),
        "episodic_size": len(episodic),
        "ltm_object": ltm
    }


def show_learned_patterns(dataset_name, verbose=True):
    """Show patterns learned from a dataset."""
    if not verbose:
        return
    
    from rpa.memory import LongTermMemory
    
    ltm = LongTermMemory()
    
    print(f"\n🔍 Sample Learned Patterns:")
    print(f"   {'─'*56}")
    
    # Get patterns by domain
    domain = "python" if dataset_name in ["mbpp", "humaneval", "leetcode"] else "english"
    patterns = ltm.find_by_domain(domain)
    
    for i, pattern in enumerate(patterns[:3]):
        content_short = pattern.content[:60] + "..." if len(pattern.content) > 60 else pattern.content
        print(f"   Pattern {i+1}: {pattern.label}")
        print(f"      Content: {content_short}")
        print(f"      Level: {pattern.hierarchy_level}")
        print()


def main():
    parser = argparse.ArgumentParser(description="RPA Training Script")
    parser.add_argument("--dataset", type=str, default="mbpp",
                       help="Dataset to use (mbpp, humaneval, wikitext, squad, leetcode)")
    parser.add_argument("--sample", type=int, default=10,
                       help="Number of samples to process")
    parser.add_argument("--verbose", "-v", action="store_true", default=True,
                       help="Show detailed output")
    parser.add_argument("--output", type=str, default=None,
                       help="Output curriculum to file")
    parser.add_argument("--persist", type=str, default=None,
                       help="Persist memory to directory")
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    RPA TRAINING PIPELINE                       ║
║              Learn from Hugging Face Datasets                  ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    start_time = datetime.now()
    
    # Step 1: Load dataset sample
    result = load_dataset_sample(args.dataset, args.sample, args.verbose)
    if not result:
        return
    items, config = result
    
    # Step 2: Convert to curriculum
    curriculum = convert_to_curriculum(items, config, args.verbose)
    
    # Step 3: Train RPA
    storage_path = Path(args.persist) if args.persist else None
    training_result = train_rpa(curriculum, args.verbose, storage_path)
    
    # Step 4: Save curriculum if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(curriculum, f, indent=2)
        print(f"\n💾 Curriculum saved to: {output_path}")
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"\n" + "="*60)
    print(f"  ✅ TRAINING COMPLETE")
    print("="*60)
    print(f"  Dataset:     {args.dataset}")
    print(f"  Samples:     {args.sample}")
    print(f"  Time:        {elapsed:.2f}s")
    print(f"  Session:     {training_result['session_id']}")
    print("="*60)
    
    return training_result


if __name__ == "__main__":
    main()
