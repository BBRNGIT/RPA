"""
RPA - Recursive Pattern Agent

A token-free AI learning system that builds knowledge hierarchically
from characters to complex patterns.
"""

__version__ = "0.1.0"

from rpa.core.graph import Node, Edge, PatternGraph
from rpa.memory.stm import ShortTermMemory
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory

__all__ = [
    "Node",
    "Edge", 
    "PatternGraph",
    "ShortTermMemory",
    "LongTermMemory",
    "EpisodicMemory",
]
