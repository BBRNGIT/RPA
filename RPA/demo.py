#!/usr/bin/env python3
"""
RPA Interactive Demo - Try out your RPA system!
Run with: python /home/z/my-project/RPA/demo.py
"""

import sys
sys.path.insert(0, '/home/z/my-project/RPA')

from rpa.memory import ShortTermMemory, LongTermMemory, EpisodicMemory, EventType
from rpa.core import Node, NodeType
from rpa.agents import CodingAgent, LanguageAgent, AgentRegistry, Orchestrator
from rpa.safety import SystemHealthMonitor, CurriculumIngestionGate, CurriculumBatch
from rpa.inquiry import GapDetector


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def demo_memory():
    separator("1. MEMORY SYSTEM")

    # Initialize
    stm = ShortTermMemory()
    ltm = LongTermMemory()
    episodic = EpisodicMemory()

    # Create a session first
    session_id = stm.create_session(metadata={"demo": True})
    print(f"\n📚 Created session: {session_id}")

    # Teach some patterns
    print("\n📚 Teaching patterns to STM...")
    words = [
        ("apple", ["a", "p", "p", "l", "e"]),
        ("banana", ["b", "a", "n", "a", "n", "a"]),
        ("cat", ["c", "a", "t"]),
    ]

    for word, composition in words:
        # Use the factory method to create a pattern node
        node = Node.create_pattern(
            label=word,
            content=word,
            hierarchy_level=1,
            domain="english"
        )
        # Store composition in metadata
        node.metadata["composition"] = composition
        stm.add_pattern(node)
        print(f"  ✓ Created: {node.label} (ID: {node.node_id[:20]}...)")

    # Create event
    episodic.log_event(
        event_type=EventType.SESSION_STARTED,
        session_id=session_id,
        data={"description": "Learned 3 word patterns"},
        metadata={"words": [w[0] for w in words]}
    )

    print(f"\n📊 Memory Status:")
    print(f"  STM nodes: {len(stm)}")
    print(f"  LTM nodes: {len(ltm)}")
    print(f"  Episodic events: {len(episodic)}")


def demo_coding_agent():
    separator("2. CODING AGENT")

    coder = CodingAgent(language="python")

    # Generate code
    print("\n🔧 Generating code...")
    result = coder.generate_code("create a for loop from 0 to 5")
    print(f"  Prompt: 'create a for loop from 0 to 5'")
    print(f"  Generated:\n{result['code']}")

    # Execute code
    print("\n⚡ Executing code in sandbox...")
    code = "for i in range(5):\n    print(f'Number: {i}')"
    exec_result = coder.execute_code(code)
    print(f"  Code:\n{code}")
    print(f"  Output:\n{exec_result.output}")

    # Review code
    print("\n🔍 Reviewing code...")
    review = coder.review_code("x=1\ny=2\nz=x+y")
    print(f"  Score: {review.score}/100")
    print(f"  Issues: {len(review.issues)}")


def demo_language_agent():
    separator("3. LANGUAGE AGENT")

    linguist = LanguageAgent()

    # Parse sentence
    print("\n📝 Parsing sentence...")
    sentence = "The quick brown fox jumps over the lazy dog."
    parsed = linguist.parse_sentence(sentence)
    print(f"  Input: '{sentence}'")
    print(f"  Words: {parsed.words[:5]}...")
    print(f"  Word count: {len(parsed.words)}")

    # Generate sentence
    print("\n✍️ Generating sentence...")
    result = linguist.generate_sentence({
        "subject": "The AI",
        "verb": "learned",
        "object": "new patterns"
    })
    print(f"  Generated: '{result['sentence']}'")

    # Explain concept
    print("\n📖 Explaining concept...")
    concept = linguist.explain_concept("noun")
    print(f"  Concept: noun")
    print(f"  Definition: {concept['definition']}")
    print(f"  Examples: {concept['examples'][:3]}")


def demo_multi_agent():
    separator("4. MULTI-AGENT SYSTEM")

    # Create agents
    coder = CodingAgent()
    linguist = LanguageAgent()

    # Register them
    registry = AgentRegistry()
    registry.register_agent(coder)
    registry.register_agent(linguist)

    print(f"\n🤖 Registered {len(registry)} agents:")
    for agent in registry.list_agents():
        print(f"  - {agent.agent_id} ({agent.domain})")

    # Find agents by capability
    print("\n🔍 Finding agents with 'generate_code' capability:")
    coders = registry.find_agents_by_capability("generate_code")
    for agent in coders:
        print(f"  - {agent.agent_id}")

    # Orchestrator
    orchestrator = Orchestrator(registry=registry)
    task = orchestrator.create_task(
        description="Generate and review Python code",
        task_type="code"
    )

    print(f"\n📋 Created task: {task.task_id}")
    subtasks = orchestrator.decompose_task(task)
    print(f"  Decomposed into {len(subtasks)} subtasks:")
    for st in subtasks:
        print(f"    - {st.description}")


def demo_safety():
    separator("5. SAFETY SYSTEM")

    # Curriculum validation
    gate = CurriculumIngestionGate()

    batch = CurriculumBatch(
        batch_id="demo_batch",
        domain="english",
        hierarchy_level=1,
        items=[
            {"content": "hello", "label": "hello"},
            {"content": "world", "label": "world"},
        ]
    )

    print("\n🛡️ Validating curriculum batch...")
    result = gate.validate_batch(batch)
    print(f"  Valid: {result.is_valid}")
    print(f"  Items accepted: {result.items_accepted}")

    # Try malicious input
    print("\n🚫 Testing malicious input...")
    bad_batch = CurriculumBatch(
        batch_id="bad_batch",
        domain="english",
        hierarchy_level=1,
        items=[{"content": "<script>alert('xss')</script>"}]
    )
    bad_result = gate.validate_batch(bad_batch)
    print(f"  Valid: {bad_result.is_valid}")
    print(f"  Rejection reasons: {len(bad_result.rejection_reasons)}")


def demo_health_monitor():
    separator("6. HEALTH MONITORING")

    monitor = SystemHealthMonitor()

    # Record operations
    monitor.record_operation("teach", 50)
    monitor.record_operation("query", 200)
    monitor.record_error("validation_error", 5)

    print("\n📈 Recording operations...")
    print("  50 teach operations")
    print("  200 query operations")
    print("  5 validation errors")

    # Generate report
    report = monitor.generate_report(
        stm_count=50,
        ltm_count=500,
        episodic_count=100,
        pending_inquiries=10,
        consolidation_attempted=100,
        consolidation_success=85
    )

    print(f"\n🏥 Health Report:")
    print(f"  Overall Status: {report.overall_status.value.upper()}")
    print(f"  Uptime: {report.uptime_seconds:.1f}s")
    print(f"\n  Metrics:")
    for metric in report.metrics:
        status_emoji = "✅" if metric.status.value == "healthy" else "⚠️"
        print(f"    {status_emoji} {metric.name}: {metric.value} {metric.unit}")


def demo_gap_detection():
    separator("7. GAP DETECTION")

    # Create a PatternGraph directly for gap detection
    from rpa.core import PatternGraph
    graph = PatternGraph(domain="demo")
    detector = GapDetector()

    # Create some patterns
    print("\n🔎 Creating patterns for gap analysis...")
    for word in ["apple", "banana", "cat"]:
        node = Node.create_pattern(
            label=word,
            content=word,
            hierarchy_level=1
        )
        graph.add_node(node)
        print(f"  Created: {word}")

    # Detect gaps
    print("\n🔍 Detecting knowledge gaps...")
    gaps = detector.detect_orphaned_patterns(graph)
    print(f"  Orphaned patterns: {len(gaps)}")

    uncertain = detector.detect_flagged_uncertain_patterns(graph)
    print(f"  Uncertain patterns: {len(uncertain)}")
    
    all_gaps = detector.detect_all_gaps(graph)
    print(f"  Total gaps detected: {len(all_gaps)}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    RPA INTERACTIVE DEMO                        ║
║         Recursive Pattern Architecture System                  ║
╚═══════════════════════════════════════════════════════════════╝
""")

    try:
        demo_memory()
        demo_coding_agent()
        demo_language_agent()
        demo_multi_agent()
        demo_safety()
        demo_health_monitor()
        demo_gap_detection()

        print("\n" + "="*60)
        print("  ✅ DEMO COMPLETE!")
        print("="*60)
        print("""
Next steps:
  • Import modules: from rpa.agents import CodingAgent
  • Start REST API: python -c "from rpa.api import create_rest_server; ..."
  • Check tests: pytest tests/ -v
  • Read docs: cat README.md
""")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
