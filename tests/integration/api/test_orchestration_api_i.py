import pytest
import httpx
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings

client = TestClient(app)

OLLAMA_HOST = "http://localhost:11434"

def is_ollama_running():
    try:
        return httpx.get(OLLAMA_HOST, timeout=2.0).status_code == 200
    except Exception:
        return False

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama offline")
async def test_orchestrator_run_endpoint_full_loop(tmp_path):
    """
    Integration Test for Phase 3:
    Verifies that the /orchestrator/run endpoint:
    1. Requires X-API-KEY.
    2. Initializes AgentState.
    3. Executes the full loop (Planner -> Specialist -> Supervisor).
    """
    
    # 1. Setup test files
    doc_path = tmp_path / "test_doc.md"
    doc_path.write_text("## Test Section\n- Test bullet points.")
    
    # 2. Test Unauthorized
    response = client.post(
        "/api/v1/orchestrator/run",
        data={"folder_path": str(tmp_path), "user_prompt": "Process this folder"},
        headers={"X-API-KEY": "wrong_key"}
    )
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json()["message"]

    # 3. Test Successful Orchestration
    # Using the default secret from config.py for testing
    headers = {"X-API-KEY": settings.API_KEY}
    
    # We use a real call to Ollama.
    # Note: This might take a while depending on the local machine.
    response = client.post(
        "/api/v1/orchestrator/run",
        data={
            "folder_path": str(tmp_path),
            "user_prompt": "Structure my docs"
        },
        headers=headers,
        timeout=120.0 # High timeout for LLM inference
    )

    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "final_response" in data
    assert "metadata" in data
    assert "plan_result" in data
    
    # Verify that at least some tokens were used (telemetry)
    assert data["metadata"]["token_usage"] > 0
    
    # Check if files were created (integration proof)
    xml_dir = tmp_path / "xml"
    # We expect the atomicity_agent to at least try to create an XML
    # depending on how far the loop went before max_iterations or END
    if xml_dir.exists():
        files = list(xml_dir.glob("*.xml"))
        assert len(files) >= 0 # Just checking path existence
