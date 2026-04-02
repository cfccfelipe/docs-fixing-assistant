import httpx
import pytest

from domain.models.enums import StopReason
from domain.models.llm_provider_model import OllamaConfig
from domain.models.state_model import AgentConfig, AgentState, StateMetadata
from domain.orchestrator.nodes.supervisor_node import SupervisorNode
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "llama3.1:latest"


def is_ollama_running():
    """Check if the local Ollama service is reachable."""
    try:
        return httpx.get(OLLAMA_HOST, timeout=2.0).status_code == 200
    except Exception:
        return False


@pytest.fixture
def supervisor_node():
    llm = OllamaAdapter(OllamaConfig(host=OLLAMA_HOST, model_id=MODEL_NAME))
    from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_SUPERVISOR

    config = AgentConfig(
        agent_id="supervisor",
        system_prompt=SYSTEM_PROMPT_SUPERVISOR,
        llm_provider=llm,
        temperature=0.0,
    )
    return SupervisorNode(config=config, max_iterations=5)


# --- CATEGORY 1: ROBUSTNESS (JSON & PARSING) ---


@pytest.mark.asyncio
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama offline")
async def test_supervisor_format_integrity(supervisor_node):
    """
    CRITICAL: Verify that BaseNode + ResponseParser clean malformed JSON.
    If this fails, the issue is in BaseNode regex cleaning.
    """
    state = AgentState(
        folder_path="./test_dir",
        user_prompt="Give me the initial plan",
        content="",
        metadata=StateMetadata(),
    )

    update = await supervisor_node(state)

    error = update.get("error_message")
    assert error is None, f"Format/JSON failure. Detail: {error}"
    assert isinstance(update, dict), "The response must be a valid dictionary"


# --- CATEGORY 2: ROUTING LOGIC (DECISION MAKING) ---


@pytest.mark.asyncio
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama offline")
async def test_route_to_planner_when_empty(supervisor_node):
    """Verify initial transition: Empty content -> Planner."""
    state = AgentState(
        folder_path="./test_dir",
        user_prompt="Organize my files",
        content="",
        metadata=StateMetadata(),
    )

    update = await supervisor_node(state)

    assert update.get("next_agent") == "planner_agent"
    assert update.get("stop_reason") == StopReason.CALL


@pytest.mark.asyncio
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama offline")
async def test_route_to_coder_when_tasks_pending(supervisor_node):
    """Verify technical delegation: Pending tasks [ ] -> Coder."""
    state = AgentState(
        folder_path="./test_dir",
        user_prompt="Execute the plan",
        content="- [x] Step 1\n- [ ] Create file config.py",
        metadata=StateMetadata(),
    )

    update = await supervisor_node(state)

    assert update.get("next_agent") == "coder_agent"
    assert "config.py" in update.get("next_task").lower()


@pytest.mark.asyncio
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama offline")
async def test_route_to_end_when_all_done(supervisor_node):
    """Verify loop closure: All [x] -> End."""
    state = AgentState(
        folder_path="./test_dir",
        user_prompt="Are we done?",
        content="- [x] Final task completed",
        metadata=StateMetadata(),
    )

    update = await supervisor_node(state)

    assert update.get("stop_reason") == StopReason.END
    assert update.get("final_response") is not None
    assert update.get("next_agent") is None


# --- CATEGORY 3: TELEMETRY (METADATA) ---


@pytest.mark.asyncio
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama offline")
async def test_supervisor_metadata_accumulation(supervisor_node):
    """Verify that token/time metrics accumulate correctly."""
    state = AgentState(
        folder_path="./test_dir",
        user_prompt="Hello",
        content="",
        metadata=StateMetadata(token_usage=100),  # Previous usage
    )

    update = await supervisor_node(state)
    metadata = update.get("metadata")

    assert metadata is not None
    assert metadata.token_usage > 100, "Token usage should accumulate"
    assert metadata.last_agent_key == "supervisor"
