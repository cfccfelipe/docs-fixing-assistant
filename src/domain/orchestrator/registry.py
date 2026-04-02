# src/domain/orchestrator/registry.py

from typing import Final

"""
Registry using 'Convention over Configuration'.
The routing tokens match the Agent IDs exactly.
"""

# IDs reales de los agentes en el sistema
VALID_ROUTING_KEYS: Final[list[str]] = [
    "supervisor",
    "planner_agent",
    "atomicity_agent",
    "reordering_agent",
    "tag_agent",
    "naming_agent",
    "content_agent",
    "matrix_agent",
    "flashcards_agent",
    "diagram_agent",
    "case_study_agent",
]

# El núcleo que garantiza la integridad del documento
MANDATORY_AGENT_IDS: Final[list[str]] = [
    "atomicity_agent",
    "tag_agent",
    "content_agent",
]
