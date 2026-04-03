import pytest
import httpx
import os
import shutil
import time
from domain.models.state_model import AgentState
from domain.orchestrator.agent_registry import setup_orchestrator
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter
from domain.models.llm_provider_model import OllamaConfig
from infrastructure.storage.local_file_system_adapter import LocalFileSystemAdapter

OLLAMA_HOST = "http://localhost:11434"

def is_ollama_running():
    try:
        return httpx.get(OLLAMA_HOST, timeout=2.0).status_code == 200
    except Exception:
        return False

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama offline")
async def test_classifier_agent_integration(tmp_path):
    # Setup
    llm = OllamaAdapter(OllamaConfig(host=OLLAMA_HOST, model_id="llama3.1:latest"))
    
    # Use a sub-directory for the adapter base_path to simulate a real project
    base_path = tmp_path / "project"
    base_path.mkdir()
    fs = LocalFileSystemAdapter(base_path=str(base_path))
    
    supervisor, registry = setup_orchestrator(llm, fs)
    
    # Create test file in project root
    test_file = base_path / "architecture_doc.md"
    test_file.write_text("This document describes the high-level system architecture.")
    
    # Arrange State
    state = AgentState(
        folder_path=str(base_path),
        user_prompt="Classify this document",
        content="- [ ] architecture_doc.md -> classifier_agent -> Categorize file",
        next_task="architecture_doc.md -> classifier_agent -> Categorize file"
    )
    
    # Act
    classifier = registry.get_node("classifier_agent")
    result = await classifier(state)
    print(f"Classifier result: {result}")
    
    # Assert
    # Check if the file was written to the expected path
    # If the LLM didn't use the correct path, we'll see it here.
    print(f"Final directory contents of project/: {list(base_path.iterdir())}")
    
    expected_path = base_path / "architecture" / "architecture_doc.md"
    assert expected_path.exists(), f"File not found at {expected_path}. Found: {list(base_path.iterdir())}"
