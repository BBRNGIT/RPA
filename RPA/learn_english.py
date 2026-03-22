#!/usr/bin/env python3
"""
RPA English Learning Job - Run English language learning sessions.

Usage:
    python learn_english.py --mode vocabulary --items 20
    python learn_english.py --mode grammar --items 10
    python learn_english.py --mode reading --passages 3
    python learn_english.py --mode writing --prompts 2
    python learn_english.py --mode full --duration 30
"""

import argparse
import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime
import random

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent))

from rpa.domains.english import (
    EnglishDomain,
    VocabularyTrainer,
    GrammarEngine,
    ReadingComprehension,
    WritingAssessor,
    ProficiencyLevel,
)
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory


def print_header():
    """Print the header."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              RPA ENGLISH LEARNING JOB                          ║
║         Vocabulary • Grammar • Reading • Writing               ║
╚═══════════════════════════════════════════════════════════════╝
""")


def run_vocabulary_session(trainer, num_items=20, verbose=True):
    """Run a vocabulary learning session."""
    print("\n📚 VOCABULARY LEARNING SESSION")
    print("=" * 60)

    # Get new and due items
    new_items = trainer.get_new_vocabulary(limit=num_items // 2)
    due_items = trainer.get_due_reviews(limit=num_items // 2)

    all_items = new_items + due_items
    random.shuffle(all_items)

    if not all_items:
        print("   No items to review! Adding new vocabulary...")
        # Show available vocabulary
        all_items = list(trainer._vocabulary.values())[:num_items]

    print(f"   Items to learn/review: {len(all_items)}")
    print(f"   ─────────────────────────────────────────────────────")

    stats = {
        "total": 0,
        "correct": 0,
        "incorrect": 0,
        "time_spent": 0,
    }

    for i, item in enumerate(all_items):
        stats["total"] += 1
        start_time = time.time()

        # Generate flashcard
        flashcard = trainer.generate_flashcard(item)

        if verbose:
            print(f"\n   [{i+1}/{len(all_items)}] Word: {item.word.upper()}")
            print(f"   Part of speech: {item.part_of_speech}")
            print(f"   Current proficiency: {item.proficiency.value}")

            # Show definition after "thinking"
            time.sleep(0.5)
            print(f"   ─────────────────────────────────────")
            print(f"   Definition: {item.definition}")

            if item.examples:
                print(f"   Example: {item.examples[0]}")

        # Simulate review (auto-grade based on existing knowledge)
        # In a real scenario, user would respond
        quality = random.choices(
            [5, 4, 3, 2, 1, 0],
            weights=[0.3, 0.3, 0.2, 0.1, 0.05, 0.05]  # Bias towards correct
        )[0]

        time_spent = time.time() - start_time
        stats["time_spent"] += time_spent

        # Process review
        result = trainer.review(item.word_id, quality, time_spent=time_spent)

        if result.correct:
            stats["correct"] += 1
            status = "✅ Correct"
        else:
            stats["incorrect"] += 1
            status = "❌ Incorrect"

        if verbose:
            print(f"   Result: {status}")
            print(f"   New proficiency: {item.proficiency.value}")
            print(f"   Next review: {item.next_review.strftime('%Y-%m-%d %H:%M') if item.next_review else 'N/A'}")

    # Summary
    accuracy = stats["correct"] / max(stats["total"], 1) * 100
    print(f"\n   ═════════════════════════════════════════")
    print(f"   📊 VOCABULARY SESSION SUMMARY")
    print(f"   ═════════════════════════════════════════")
    print(f"   Total items:   {stats['total']}")
    print(f"   Correct:       {stats['correct']} ({accuracy:.1f}%)")
    print(f"   Time spent:    {stats['time_spent']:.1f}s")

    # Show proficiency distribution
    proficiency_dist = trainer.get_statistics()["by_proficiency"]
    print(f"\n   Proficiency Distribution:")
    for level, count in proficiency_dist.items():
        if count > 0:
            bar = "█" * min(count, 20)
            print(f"      {level:12}: {bar} ({count})")

    return stats


def run_grammar_session(engine, num_exercises=10, verbose=True):
    """Run a grammar practice session."""
    print("\n📖 GRAMMAR PRACTICE SESSION")
    print("=" * 60)

    # Get rules by difficulty
    all_rules = list(engine._rules.values())
    random.shuffle(all_rules)

    exercises_to_do = min(num_exercises, len(all_rules))

    print(f"   Exercises to complete: {exercises_to_do}")
    print(f"   ─────────────────────────────────────────────────────")

    stats = {
        "total": 0,
        "correct": 0,
        "incorrect": 0,
        "by_category": {},
    }

    for i in range(exercises_to_do):
        rule = all_rules[i]
        stats["total"] += 1

        if verbose:
            print(f"\n   [{i+1}/{exercises_to_do}] Rule: {rule.name}")
            print(f"   Category: {rule.category.value}")
            print(f"   Difficulty: {'⭐' * rule.difficulty}")

        # Generate exercise
        exercise_type = random.choice(["multiple_choice", "error_correction", "fill_blank"])
        exercise = engine.generate_exercise(rule, exercise_type)

        if verbose:
            print(f"\n   Question ({exercise_type}):")
            print(f"   {exercise['question']}")

            if exercise_type == "multiple_choice":
                for j, opt in enumerate(exercise["options"]):
                    print(f"      {j+1}. {opt}")

        # Simulate answer (auto-grade with bias towards correct)
        if exercise_type == "multiple_choice":
            # 70% chance of correct answer
            if random.random() < 0.7:
                answer = exercise["correct_index"]
            else:
                wrong_options = [i for i in range(len(exercise["options"])) if i != exercise["correct_index"]]
                answer = random.choice(wrong_options) if wrong_options else 0

            is_correct = answer == exercise["correct_index"]

        else:
            # For other types, simulate 70% correct rate
            is_correct = random.random() < 0.7
            answer = exercise.get("answer", exercise.get("correct_answer", ""))

        if is_correct:
            stats["correct"] += 1
            status = "✅ Correct"
        else:
            stats["incorrect"] += 1
            status = "❌ Incorrect"

        if verbose:
            print(f"\n   Your answer: {answer if exercise_type == 'multiple_choice' else 'Submitted'}")
            print(f"   Result: {status}")
            print(f"   Explanation: {exercise.get('explanation', 'N/A')[:100]}...")

        # Track by category
        cat = rule.category.value
        if cat not in stats["by_category"]:
            stats["by_category"][cat] = {"correct": 0, "total": 0}
        stats["by_category"][cat]["total"] += 1
        if is_correct:
            stats["by_category"][cat]["correct"] += 1

    # Summary
    accuracy = stats["correct"] / max(stats["total"], 1) * 100
    print(f"\n   ═════════════════════════════════════════")
    print(f"   📊 GRAMMAR SESSION SUMMARY")
    print(f"   ═════════════════════════════════════════")
    print(f"   Total exercises: {stats['total']}")
    print(f"   Correct:         {stats['correct']} ({accuracy:.1f}%)")

    print(f"\n   Performance by Category:")
    for cat, cat_stats in stats["by_category"].items():
        cat_acc = cat_stats["correct"] / max(cat_stats["total"], 1) * 100
        print(f"      {cat:25}: {cat_acc:.0f}%")

    return stats


def run_reading_session(reading, num_passages=3, verbose=True):
    """Run a reading comprehension session."""
    print("\n📰 READING COMPREHENSION SESSION")
    print("=" * 60)

    # Get passages
    all_passages = list(reading._passages.values())
    random.shuffle(all_passages)
    passages_to_do = all_passages[:num_passages]

    print(f"   Passages to read: {len(passages_to_do)}")
    print(f"   ─────────────────────────────────────────────────────")

    stats = {
        "total_questions": 0,
        "correct": 0,
        "passages_completed": 0,
        "total_time": 0,
    }

    for i, passage in enumerate(passages_to_do):
        if verbose:
            print(f"\n   [{'Passage ' + str(i+1)}] {passage.title}")
            print(f"   Difficulty: {'⭐' * passage.difficulty}")
            print(f"   Word count: {passage.word_count}")
            print(f"   ─────────────────────────────────────────")
            print(f"   {passage.text}")
            print(f"   ─────────────────────────────────────────")

        start_time = time.time()

        # Answer questions
        answers = []
        for j, question in enumerate(passage.questions):
            stats["total_questions"] += 1

            if verbose:
                print(f"\n   Question {j+1}: {question['question']}")
                for k, opt in enumerate(question["options"]):
                    print(f"      {k+1}. {opt}")

            # Simulate answer (70% correct rate)
            if random.random() < 0.7:
                answer = question["correct"]
            else:
                wrong_options = [x for x in range(len(question["options"])) if x != question["correct"]]
                answer = random.choice(wrong_options) if wrong_options else 0

            answers.append(answer)

            if answer == question["correct"]:
                stats["correct"] += 1
                if verbose:
                    print(f"      ✅ Correct!")
            else:
                if verbose:
                    print(f"      ❌ Incorrect. Correct answer: {question['options'][question['correct']]}")

        time_spent = time.time() - start_time
        stats["total_time"] += time_spent
        stats["passages_completed"] += 1

        # Submit assessment
        result = reading.assess(passage.passage_id, answers, time_spent)

        if verbose:
            print(f"\n   Passage Score: {result.score * 100:.0f}%")
            print(f"   Time: {time_spent:.1f}s")

    # Summary
    accuracy = stats["correct"] / max(stats["total_questions"], 1) * 100
    print(f"\n   ═════════════════════════════════════════")
    print(f"   📊 READING SESSION SUMMARY")
    print(f"   ═════════════════════════════════════════")
    print(f"   Passages completed: {stats['passages_completed']}")
    print(f"   Questions answered: {stats['total_questions']}")
    print(f"   Correct:            {stats['correct']} ({accuracy:.1f}%)")
    print(f"   Total time:         {stats['total_time']:.1f}s")

    return stats


def run_writing_session(assessor, num_prompts=2, verbose=True):
    """Run a writing practice session."""
    print("\n✍️  WRITING PRACTICE SESSION")
    print("=" * 60)

    # Get prompts
    all_prompts = list(assessor._prompts.values())
    random.shuffle(all_prompts)
    prompts_to_do = all_prompts[:num_prompts]

    print(f"   Prompts to complete: {len(prompts_to_do)}")
    print(f"   ─────────────────────────────────────────────────────")

    # Sample responses (in real scenario, user would write)
    sample_responses = [
        "I enjoy playing soccer on weekends. It is a great way to stay active and have fun with my friends. We usually play at the local park on Saturday mornings. Soccer helps me improve my teamwork skills and keeps me fit. I have been playing for three years now.",
        "Last summer, I visited Tokyo, Japan. It was an amazing experience. The city is full of modern buildings and traditional temples. I tried many delicious foods like sushi and ramen. The people were very friendly and helpful. I hope to visit again soon.",
        "Social media has both positive and negative effects. On the positive side, it helps people stay connected and share information. However, it can also lead to addiction and spread misinformation. I believe the key is to use it in moderation and verify information before sharing.",
        "The door slowly opened, revealing something unexpected. Behind it was a small, glowing creature. It had big eyes and tiny wings. At first, I was scared, but then it smiled at me. 'Hello,' it said softly. 'I have been waiting for you.' This was the beginning of an incredible adventure.",
    ]

    stats = {
        "total_submissions": 0,
        "total_words": 0,
        "scores": [],
        "criterion_scores": {},
    }

    for i, prompt in enumerate(prompts_to_do):
        if verbose:
            print(f"\n   [Prompt {i+1}] {prompt.prompt}")
            print(f"   Topic: {prompt.topic}")
            print(f"   Word limit: {prompt.word_limit[0]}-{prompt.word_limit[1]}")
            print(f"   Time limit: {prompt.time_limit_minutes} minutes")

        # Use sample response
        response = sample_responses[i % len(sample_responses)]

        if verbose:
            print(f"\n   Your response:")
            print(f"   ─────────────────────────────────────")
            print(f"   {response}")
            print(f"   ─────────────────────────────────────")

        # Assess
        result = assessor.assess(prompt.prompt_id, response)

        stats["total_submissions"] += 1
        stats["total_words"] += result.word_count
        stats["scores"].append(result.overall_score)

        if verbose:
            print(f"\n   Assessment Results:")
            print(f"      Word count: {result.word_count}")
            print(f"      Overall score: {result.overall_score * 100:.0f}%")
            print(f"\n      Scores by criterion:")
            for criterion, score in result.scores.items():
                print(f"         {criterion:15}: {score * 100:.0f}%")
                if criterion not in stats["criterion_scores"]:
                    stats["criterion_scores"][criterion] = []
                stats["criterion_scores"][criterion].append(score)

            print(f"\n      Feedback: {result.feedback}")

            if result.suggestions:
                print(f"\n      Suggestions:")
                for sug in result.suggestions:
                    print(f"         • {sug}")

            if result.grammar_errors:
                print(f"\n      Grammar errors found: {len(result.grammar_errors)}")

    # Summary
    avg_score = sum(stats["scores"]) / max(len(stats["scores"]), 1)
    print(f"\n   ═════════════════════════════════════════")
    print(f"   📊 WRITING SESSION SUMMARY")
    print(f"   ═════════════════════════════════════════")
    print(f"   Submissions:    {stats['total_submissions']}")
    print(f"   Total words:    {stats['total_words']}")
    print(f"   Average score:  {avg_score * 100:.0f}%")

    print(f"\n   Average by Criterion:")
    for criterion, scores in stats["criterion_scores"].items():
        avg = sum(scores) / len(scores)
        bar = "█" * int(avg * 10)
        print(f"      {criterion:15}: {bar} {avg * 100:.0f}%")

    return stats


def run_full_session(domain, duration_minutes=30, verbose=True):
    """Run a full mixed learning session."""
    print("\n🎓 FULL LEARNING SESSION")
    print("=" * 60)
    print(f"   Duration: {duration_minutes} minutes")
    print(f"   Mode: Mixed (Vocabulary, Grammar, Reading, Writing)")

    start_time = time.time()
    target_duration = duration_minutes * 60  # Convert to seconds

    all_stats = {
        "vocabulary": None,
        "grammar": None,
        "reading": None,
        "writing": None,
    }

    # Calculate time allocation
    vocab_time = target_duration * 0.25
    grammar_time = target_duration * 0.25
    reading_time = target_duration * 0.30
    writing_time = target_duration * 0.20

    # Vocabulary
    if time.time() - start_time < target_duration:
        print(f"\n{'─' * 60}")
        print("   📚 PHASE 1: VOCABULARY")
        print(f"{'─' * 60}")
        num_vocab = max(5, int(vocab_time / 10))  # ~10s per item
        all_stats["vocabulary"] = run_vocabulary_session(
            domain.vocabulary, num_items=num_vocab, verbose=verbose
        )

    # Grammar
    if time.time() - start_time < target_duration:
        print(f"\n{'─' * 60}")
        print("   📖 PHASE 2: GRAMMAR")
        print(f"{'─' * 60}")
        num_grammar = max(3, int(grammar_time / 15))  # ~15s per exercise
        all_stats["grammar"] = run_grammar_session(
            domain.grammar, num_exercises=num_grammar, verbose=verbose
        )

    # Reading
    if time.time() - start_time < target_duration:
        print(f"\n{'─' * 60}")
        print("   📰 PHASE 3: READING")
        print(f"{'─' * 60}")
        num_reading = max(1, int(reading_time / 60))  # ~60s per passage
        all_stats["reading"] = run_reading_session(
            domain.reading, num_passages=num_reading, verbose=verbose
        )

    # Writing
    if time.time() - start_time < target_duration:
        print(f"\n{'─' * 60}")
        print("   ✍️  PHASE 4: WRITING")
        print(f"{'─' * 60}")
        num_writing = max(1, int(writing_time / 90))  # ~90s per prompt
        all_stats["writing"] = run_writing_session(
            domain.writing, num_prompts=num_writing, verbose=verbose
        )

    # Final Summary
    elapsed = time.time() - start_time
    print(f"\n{'═' * 60}")
    print("   🏆 FULL SESSION COMPLETE")
    print(f"{'═' * 60}")
    print(f"   Total time: {elapsed / 60:.1f} minutes")

    # Aggregate statistics
    print(f"\n   📈 Overall Statistics:")

    if all_stats["vocabulary"]:
        vocab_acc = all_stats["vocabulary"]["correct"] / max(all_stats["vocabulary"]["total"], 1) * 100
        print(f"      Vocabulary: {vocab_acc:.0f}% accuracy")

    if all_stats["grammar"]:
        gram_acc = all_stats["grammar"]["correct"] / max(all_stats["grammar"]["total"], 1) * 100
        print(f"      Grammar:    {gram_acc:.0f}% accuracy")

    if all_stats["reading"]:
        read_acc = all_stats["reading"]["correct"] / max(all_stats["reading"]["total_questions"], 1) * 100
        print(f"      Reading:    {read_acc:.0f}% accuracy")

    if all_stats["writing"]:
        write_avg = sum(all_stats["writing"]["scores"]) / max(len(all_stats["writing"]["scores"]), 1) * 100
        print(f"      Writing:    {write_avg:.0f}% average score")

    # Get domain statistics
    domain_stats = domain.get_overall_statistics()
    print(f"\n   📚 Cumulative Progress:")
    print(f"      Vocabulary words: {domain_stats['vocabulary']['total_words']}")
    print(f"      Grammar rules:    {domain_stats['grammar']['total_rules']}")
    print(f"      Reading passages: {domain_stats['reading']['total_passages']}")
    print(f"      Writing prompts:  {domain_stats['writing']['total_prompts']}")

    return all_stats


def main():
    parser = argparse.ArgumentParser(description="RPA English Learning Job")
    parser.add_argument("--mode", type=str, default="full",
                       choices=["vocabulary", "grammar", "reading", "writing", "full"],
                       help="Learning mode")
    parser.add_argument("--items", type=int, default=10,
                       help="Number of items (vocabulary/grammar)")
    parser.add_argument("--passages", type=int, default=3,
                       help="Number of reading passages")
    parser.add_argument("--prompts", type=int, default=2,
                       help="Number of writing prompts")
    parser.add_argument("--duration", type=int, default=15,
                       help="Session duration in minutes (for full mode)")
    parser.add_argument("--verbose", "-v", action="store_true", default=True,
                       help="Show detailed output")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Minimal output")

    args = parser.parse_args()

    if args.quiet:
        args.verbose = False

    print_header()

    start_time = datetime.now()

    # Initialize domain
    domain = EnglishDomain()

    # Run appropriate session
    if args.mode == "vocabulary":
        stats = run_vocabulary_session(domain.vocabulary, args.items, args.verbose)
    elif args.mode == "grammar":
        stats = run_grammar_session(domain.grammar, args.items, args.verbose)
    elif args.mode == "reading":
        stats = run_reading_session(domain.reading, args.passages, args.verbose)
    elif args.mode == "writing":
        stats = run_writing_session(domain.writing, args.prompts, args.verbose)
    elif args.mode == "full":
        stats = run_full_session(domain, args.duration, args.verbose)
    else:
        print("Unknown mode. Use: vocabulary, grammar, reading, writing, or full")
        return

    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\n{'═' * 60}")
    print(f"  ✅ LEARNING JOB COMPLETE")
    print(f"{'═' * 60}")
    print(f"  Mode:       {args.mode}")
    print(f"  Time:       {elapsed:.1f}s")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()
