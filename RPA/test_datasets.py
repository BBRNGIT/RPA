#!/usr/bin/env python3
"""
Dataset Connection Test - Verify Hugging Face dataset access.

This script tests connectivity to each configured dataset and shows
sample curriculum output that would be generated.

Run: python /home/z/my-project/RPA/test_datasets.py
"""

import json
import sys
import os
from pathlib import Path

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent))

# Use system Python for datasets
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Configuration
CONFIG_PATH = Path(__file__).parent / "config" / "datasets.json"


def load_config():
    """Load dataset configuration."""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def test_huggingface_import():
    """Test that datasets library is available."""
    print("\n" + "="*60)
    print("  1. TESTING HUGGING FACE DATASETS LIBRARY")
    print("="*60)
    
    try:
        from datasets import load_dataset, Dataset
        print("\n  ✅ 'datasets' library imported successfully")
        print(f"     Version: {__import__('datasets').__version__}")
        return True
    except ImportError as e:
        print(f"\n  ❌ Failed to import 'datasets': {e}")
        print("\n  To install: pip install datasets")
        return False


def test_dataset_access(dataset_name, config, sample_size=3):
    """Test access to a specific dataset."""
    print(f"\n  Testing: {config.get('name', dataset_name)}")
    print(f"  Source: {config.get('source', 'unknown')}")
    print(f"  HF Dataset: {config.get('dataset_name', 'unknown')}")
    
    try:
        from datasets import load_dataset
        
        # Build kwargs
        kwargs = {
            "path": config.get("dataset_name"),
            "split": config.get("split", "train"),
        }
        
        # Add config name if specified
        if config.get("config_name"):
            kwargs["name"] = config["config_name"]
        
        # Use streaming for large datasets
        if config.get("streaming", False):
            kwargs["streaming"] = True
        
        # Load with trust_remote_code for some datasets
        kwargs["trust_remote_code"] = True
        
        print(f"  Loading dataset...")
        
        # Timeout handling
        import signal
        
        class TimeoutError(Exception):
            pass
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Dataset load timed out")
        
        # Set 60 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)
        
        try:
            dataset = load_dataset(**kwargs)
            signal.alarm(0)  # Cancel timeout
        except TimeoutError:
            print(f"  ⚠️  Timeout loading dataset (>60s)")
            return None
        
        # Get info
        if config.get("streaming", False):
            # Streaming dataset - get first few items
            items = []
            for i, item in enumerate(dataset):
                if i >= sample_size:
                    break
                items.append(item)
            total = "streaming"
            sample = items
        else:
            total = len(dataset)
            sample = [dataset[i] for i in range(min(sample_size, len(dataset)))]
        
        print(f"  ✅ Connected! Total items: {total}")
        
        return {
            "dataset_name": dataset_name,
            "total_items": total,
            "sample": sample,
            "config": config
        }
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        return None


def show_sample_curriculum(dataset_info):
    """Show sample curriculum that would be generated."""
    if not dataset_info or not dataset_info.get("sample"):
        return
    
    print(f"\n  {'─'*56}")
    print(f"  SAMPLE CURRICULUM OUTPUT FOR: {dataset_info['dataset_name'].upper()}")
    print(f"  {'─'*56}")
    
    config = dataset_info["config"]
    curriculum_type = config.get("curriculum_type", "unknown")
    domain = config.get("domain", "general")
    
    for i, item in enumerate(dataset_info["sample"][:2]):
        print(f"\n  Raw Item {i+1}:")
        print(f"  {'─'*40}")
        
        # Show raw fields
        for key, value in item.items():
            if isinstance(value, str):
                display_val = value[:100] + "..." if len(value) > 100 else value
                print(f"    {key}: {display_val}")
            elif isinstance(value, list):
                print(f"    {key}: [{len(value)} items]")
            else:
                print(f"    {key}: {value}")
        
        # Show generated curriculum item
        print(f"\n  Generated Curriculum Item:")
        print(f"  {'─'*40}")
        
        curriculum_item = generate_curriculum_item(item, config, i)
        print(json.dumps(curriculum_item, indent=4)[:500])
        if len(json.dumps(curriculum_item)) > 500:
            print("  ... (truncated)")


def generate_curriculum_item(raw_item, config, index):
    """Generate a curriculum item from raw dataset item."""
    import hashlib
    from datetime import datetime
    
    domain = config.get("domain", "general")
    curriculum_type = config.get("curriculum_type", "unknown")
    fields = config.get("fields", {})
    
    # Extract content based on curriculum type
    if curriculum_type == "coding_problems":
        content = raw_item.get(fields.get("code", "code"), "")
        description = raw_item.get(fields.get("text", "prompt"), "")
        hierarchy_level = 2
        
    elif curriculum_type == "coding_functions":
        content = raw_item.get(fields.get("code", "canonical_solution"), "")
        description = raw_item.get(fields.get("description", "prompt"), "")
        hierarchy_level = 3
        
    elif curriculum_type == "instruction_code":
        content = raw_item.get(fields.get("output", "output"), "")
        description = raw_item.get(fields.get("instruction", "instruction"), "")
        hierarchy_level = 2
        
    elif curriculum_type == "natural_language":
        content = raw_item.get(fields.get("text", "text"), "")
        description = raw_item.get(fields.get("title", "title"), "")
        hierarchy_level = 1
        
    elif curriculum_type == "qa_pairs":
        content = raw_item.get(fields.get("context", "context"), "")
        description = raw_item.get(fields.get("question", "question"), "")
        hierarchy_level = 2
        
    elif curriculum_type == "code_with_docstring":
        content = raw_item.get(fields.get("code", "func_code_string"), "")
        description = raw_item.get(fields.get("docstring", "func_documentation_string"), "")
        hierarchy_level = 3
        
    elif curriculum_type == "word_definitions":
        content = raw_item.get(fields.get("definition", "definition"), "")
        description = raw_item.get(fields.get("word", "word"), "")
        hierarchy_level = 1
        
    else:
        content = str(raw_item.get("text", raw_item.get("code", "")))
        description = ""
        hierarchy_level = 1
    
    # Generate composition (tokens)
    if content:
        composition = content.split() if domain == "english" else list(content.replace(" ", "␣"))
    else:
        composition = []
    
    # Generate unique ID
    unique_id = hashlib.md5(f"{domain}_{curriculum_type}_{index}".encode()).hexdigest()[:8]
    
    return {
        "lesson_id": f"{domain[:2]}_{curriculum_type[:3]}_{index:04d}_{unique_id}",
        "content": content[:500] if content else "",
        "type": "pattern",
        "hierarchy_level": hierarchy_level,
        "domain": domain,
        "composition": composition[:50] if composition else [],
        "metadata": {
            "source": config.get("dataset_name", "unknown"),
            "curriculum_type": curriculum_type,
            "description": description[:200] if description else "",
            "difficulty": min(hierarchy_level, 4)
        },
        "created_at": datetime.now().isoformat()
    }


def run_all_tests():
    """Run all dataset tests."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║            RPA DATASET CONNECTION TESTER                      ║
║            Testing Hugging Face Dataset Access                ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    # Load config
    print("\n📋 Loading dataset configuration...")
    config = load_config()
    datasets = config.get("datasets", {})
    print(f"   Found {len(datasets)} configured datasets")
    
    # Test HF import
    if not test_huggingface_import():
        print("\n❌ Cannot proceed without datasets library")
        return
    
    # Test each dataset
    results = {}
    
    print("\n" + "="*60)
    print("  2. TESTING DATASET CONNECTIONS")
    print("="*60)
    
    # Sort by priority
    sorted_datasets = sorted(datasets.items(), key=lambda x: x[1].get("priority", 99))
    
    for dataset_name, dataset_config in sorted_datasets:
        result = test_dataset_access(dataset_name, dataset_config)
        if result:
            results[dataset_name] = result
            show_sample_curriculum(result)
        print()
    
    # Summary
    print("\n" + "="*60)
    print("  3. CONNECTION SUMMARY")
    print("="*60)
    
    success = len(results)
    total = len(datasets)
    
    print(f"\n  Connected: {success}/{total} datasets")
    print("\n  Status by dataset:")
    
    for dataset_name, dataset_config in datasets.items():
        if dataset_name in results:
            items = results[dataset_name]["total_items"]
            print(f"    ✅ {dataset_name}: {items} items available")
        else:
            print(f"    ❌ {dataset_name}: Connection failed")
    
    # Estimated curriculum potential
    print("\n" + "="*60)
    print("  4. ESTIMATED CURRICULUM POTENTIAL")
    print("="*60)
    
    total_items = 0
    for dataset_name, result in results.items():
        if isinstance(result["total_items"], int):
            sample_rate = datasets[dataset_name].get("sample_rate", 1.0)
            estimated = int(result["total_items"] * sample_rate)
            total_items += estimated
            print(f"    {dataset_name}: ~{estimated:,} curriculum items")
    
    print(f"\n  📊 Total curriculum items available: ~{total_items:,}")
    print(f"  📊 Estimated training time: {total_items // 100} batches")
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
