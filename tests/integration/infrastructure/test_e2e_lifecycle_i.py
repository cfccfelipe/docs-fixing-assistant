import pytest
import shutil
import logging
from pathlib import Path
from domain.models.state_model import AgentState
from domain.orchestrator.agent_registry import setup_orchestrator
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter
from domain.models.llm_provider_model import OllamaConfig
from infrastructure.storage.local_file_system_adapter import LocalFileSystemAdapter
from infrastructure.graph.builder import create_workflow

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_sequential_orchestrator_validation():
    # Use workspace folder inside the project root for persistent verification
    project_root = Path("tests/integration/workspace").resolve()
    if project_root.exists():
        shutil.rmtree(project_root)
    project_root.mkdir(parents=True)
    
    # Copy example data
    examples_dir = Path("tests/integration/examples")
    if examples_dir.exists():
        for file in examples_dir.rglob("*.md"):
            shutil.copy2(file, project_root / file.name)
                
    # LLM & FileSystem
    llm = OllamaAdapter(OllamaConfig(host="http://localhost:11434", model_id="llama3.1:latest"))
    fs = LocalFileSystemAdapter(base_path=str(project_root))
    
    # Initialize Registry & Graph
    supervisor, registry = setup_orchestrator(llm, fs)
    graph = create_workflow(registry)
    
    # Initialize State
    state = AgentState(
        folder_path=str(project_root),
        user_prompt="Organize documentation files sequentially."
    )
    
    # Execute workflow
    await graph.ainvoke(state)
    
    # Verification
    fixed_files = project_root / "fixed_files"
    assert fixed_files.exists(), "fixed_files directory not created!"
    
    # Assert PLAN.md has progress (tasks marked as done)
    plan_file = project_root / "PLAN.md"
    assert plan_file.exists(), "PLAN.md not created!"
    assert "[x]" in plan_file.read_text(), "No tasks were marked as completed!"
    
    # Check if artifacts exist within the new structure
    assert (fixed_files / "xml").exists(), "XML artifact directory missing!"
    assert (fixed_files / "summaries").exists(), "Summaries artifact directory missing!"
