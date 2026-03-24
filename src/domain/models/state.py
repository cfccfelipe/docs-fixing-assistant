from dataclasses import dataclass, field
from enum import Enum


class StopReason(Enum):
    """
    Standardized exit codes for Orchestrator nodes.
    Using str mixin for JSON serializability.
    """

    CALL = "CALL"  # Delegate to another agent
    ERROR = "ERROR"  # Interrupt flow due to failure
    END = "END"  # Graceful workflow completion


@dataclass
class StateMetadata:
    """Consolidated metadata for tracking and observability."""

    token_usage: int = 0
    last_agent_key: str | None = None
    trace_id: str | None = None
    model_name: str | None = None


@dataclass
class AgentState:
    """The unique source of truth for the LangGraph workflow."""

    # Context
    folder_path: str
    user_prompt: str
    content: str = ""
    current_file: str | None = None

    # Orchestration
    iteration: int = 0
    next_task: str | None = None
    next_agent: str | None = None
    stop_reason: StopReason | None = None  # CALL, ERROR, END

    # Error Handling
    error_message: str | None = None

    metadata: StateMetadata = field(default_factory=StateMetadata)
