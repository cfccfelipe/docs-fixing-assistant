from dataclasses import dataclass, field
from typing import Any, TypedDict

from domain.models.enums import StopReason
from domain.models.llm_provider_model import ToolCall


@dataclass
class StateMetadata:
    """Consolidated metadata for performance tracking and observability."""

    # Tokens & Usage
    input_tokens: int = 0
    output_tokens: int = 0
    token_usage: int = 0

    # Latencies (ms)
    total_duration_ms: float = 0.0
    load_duration_ms: float = 0.0
    prompt_eval_duration_ms: float = 0.0
    eval_duration_ms: float = 0.0

    # Tracing & Context
    model_name: str | None = None
    last_agent_key: str | None = None
    trace_id: str | None = None


@dataclass
class AgentState:
    """The unique source of truth for the Orchestrator workflow."""

    # Context & User Input (Obligatorios)
    folder_path: str
    user_prompt: str

    # State Data
    content: str = ""
    current_file: str | None = None
    task_result: str = ""  # Output of the current specialist task

    # Orchestration & Flow Control
    iteration: int = 0
    next_task: str | None = None
    next_agent: str | None = None
    stop_reason: StopReason = StopReason.CALL

    # Tool Execution Bridge (FIX: Usamos objetos ToolCall en lugar de IDs planos)
    tool_calls: list[ToolCall] = field(default_factory=list)

    # Final Outputs
    error_message: str | None = None
    final_response: str | None = None

    # Observability
    metadata: StateMetadata = field(default_factory=StateMetadata)

    def update(self, delta: "StateUpdate") -> None:
        """Surgically applies a StateUpdate to the current state."""
        for key, value in delta.items():
            if hasattr(self, key):
                setattr(self, key, value)


class StateUpdate(TypedDict, total=False):
    """Partial state delta returned by any Node."""

    folder_path: str  # Mantenemos consistencia en el path
    content: str
    current_file: str | None
    task_result: str
    iteration: int
    next_task: str | None
    next_agent: str | None
    stop_reason: StopReason
    tool_calls: list[ToolCall]
    error_message: str | None
    final_response: str | None
    metadata: StateMetadata


@dataclass(frozen=True)
class AgentConfig:
    """
    Configuration DTO for specific agents.
    Encapsulates prompts, LLM settings, and output formats.
    """

    agent_id: str
    system_prompt: str
    llm_provider: Any  # El provider inyectado (Ollama, OpenAI, etc.)

    temperature: float = 0.0
    max_tokens: int = 2500
    stop_sequences: list[str] = field(default_factory=lambda: ["}\n", "}"])

    # Formato de salida esperado (json o txt)
    output_format: str = "json"
