"""
RPA Regression Test Suite (SI-007)

This module provides baseline regression tests to ensure core functionality
remains intact across all changes. The tests are organized by functional area:

1. Training Pipeline - Tests for learn_pipeline.py and training infrastructure
2. Memory Persistence - Tests for LTM, STM, and episodic memory
3. Curriculum Loading - Tests for curriculum registry and track loading
4. Exam System - Tests for exam engine and assessment

All tests are designed to catch regressions and ensure backward compatibility.
Run with: pytest tests/regression/ -v
"""
