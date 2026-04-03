import os
import pytest
import httpx
from domain.models.llm_provider_model import OllamaConfig
from domain.models.state_model import AgentState
from domain.orchestrator.agent_registry import setup_orchestrator
from domain.models.tool_model import ToolCall  # Corrected import for ToolCall
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter
from infrastructure.storage.local_file_system_adapter import LocalFileSystemAdapter

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "llama3.1:latest"

def is_ollama_running():
    try:
        return httpx.get(OLLAMA_HOST, timeout=2.0).status_code == 200
    except Exception:
        return False

@pytest.fixture
def orchestrator_setup(tmp_path):
    llm = OllamaAdapter(OllamaConfig(host=OLLAMA_HOST, model_id=MODEL_NAME))
    fs = LocalFileSystemAdapter(base_path=str(tmp_path))
    supervisor, registry = setup_orchestrator(llm, fs)
    return supervisor, registry, tmp_path

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama offline")
async def test_full_task_loop_atomicity(orchestrator_setup):
    """
    Verifica el ciclo completo:
    1. Planner crea el plan.
    2. Supervisor delega a atomicity_agent.
    3. AtomicityAgent usa herramientas para leer y escribir.
    4. Supervisor marca tarea como completada.
    """
    supervisor, registry, tmp_path = orchestrator_setup
    
    # 1. Preparar archivo fuente
    (tmp_path / "input.md").write_text("""
## High Availability
- Use multiple zones.
- Set up load balancer.
""")
    
    state = AgentState(
        folder_path=".",
        user_prompt="Process my docs",
        content="" # Vacío para forzar planning
    )
    
    # --- CICLO 1: PLANNING ---
    update = await supervisor(state)
    state.update(update)
    assert state.next_agent == "planner_agent"
    
    planner = registry.get_node("planner_agent")
    planner_update = await planner(state)
    state.update(planner_update)
    
    assert "input.md" in state.content
    assert "atomicity_agent" in state.content
    
    # --- CICLO 2: ATOMICITY ---
    # Supervisor procesa el nuevo plan y elige la primera tarea
    route_update = await supervisor(state)
    state.update(route_update)
    
    assert state.next_agent == "atomicity_agent"
    assert "input.md" in state.next_task
    
    agent = registry.get_node("atomicity_agent")
    agent_update = await agent(state)
    state.update(agent_update)
    
    # Verificar que el agente usó herramientas
    assert "Tool write_file output" in state.task_result
    assert (tmp_path / "xml" / "input.xml").exists()
    
    # --- CICLO 3: POST-PROCESSING ---
    # Supervisor debe ver que el último agente fue atomicity_agent y marcar la tarea [x]
    final_route = await supervisor(state)
    state.update(final_route)
    
    assert "- [x]" in state.content
    assert "input.md" in state.content
