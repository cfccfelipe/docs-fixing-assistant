import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from domain.models.state_model import AgentState
from domain.orchestrator.agent_registry import setup_orchestrator
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter
from domain.models.llm_provider_model import OllamaConfig
from infrastructure.storage.local_file_system_adapter import LocalFileSystemAdapter
from infrastructure.graph.builder import create_workflow
import os

router = APIRouter()
logger = logging.getLogger(__name__)

class OrchestrationRequest(BaseModel):
    folder_path: str
    user_prompt: str

@router.post("/run")
async def run_orchestration(request: OrchestrationRequest):
    if not os.path.exists(request.folder_path):
        raise HTTPException(status_code=404, detail="Folder path not found")

    # 1. Setup
    llm = OllamaAdapter(OllamaConfig(host="http://localhost:11434", model_id="llama3.1:latest"))
    fs = LocalFileSystemAdapter(base_path=request.folder_path)
    supervisor, registry = setup_orchestrator(llm, fs)
    
    # 2. Compile LangGraph workflow
    graph = create_workflow(registry)
    
    # 3. Initialize State
    state = AgentState(
        folder_path=request.folder_path,
        user_prompt=request.user_prompt
    )
    
    # 4. Invoke graph
    try:
        final_state = await graph.ainvoke(state)
        return {
            "status": "completed",
            "final_response": final_state.final_response,
            "metadata": final_state.metadata
        }
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
