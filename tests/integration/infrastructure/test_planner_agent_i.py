import os
import pytest
import httpx
from domain.models.llm_provider_model import OllamaConfig
from domain.models.state_model import AgentState
from domain.orchestrator.agent_registry import setup_orchestrator
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
async def test_planner_agent_workflow(orchestrator_setup):
    """
    Verifica que el planner_agent explore la carpeta y genere un plan con tareas [ ].
    """
    supervisor, registry, tmp_path = orchestrator_setup
    
    # 1. Crear archivos de prueba
    (tmp_path / "doc1.md").write_text("# Doc 1 content")
    (tmp_path / "doc2.md").write_text("# Doc 2 content")
    
    # 2. Estado inicial (vacío para forzar planner)
    state = AgentState(
        folder_path=".",
        user_prompt="Organize this folder",
        content=""
    )
    
    # 3. Supervisor debe rutear al planner
    update = await supervisor(state)
    assert update.get("next_agent") == "planner_agent"
    
    # 4. Ejecutar el planner_agent
    planner = registry.get_node("planner_agent")
    state.update(update)
    
    planner_update = await planner(state)
    
    # 5. Validaciones del plan
    content = planner_update.get("content", "")
    assert "TASK" in content.upper()
    assert "doc1.md" in content
    assert "doc2.md" in content
    assert "atomicity_agent" in content
