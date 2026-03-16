from pathlib import Path

import pytest

from domain.agents.case_study_agent import CaseStudyAgent
from domain.agents.content_agent import ContentAgent
from domain.agents.diagram_agent import DiagramAgent
from domain.agents.flashcards_agent import FlashcardsAgent
from domain.agents.matrix_agent import MatrixAgent
from domain.agents.naming_agent import NamingAgent
from domain.agents.tag_agent import TagAgent
from infrastructure.adapters.storage.local_file_system import LocalFileSystemAdapter

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
async def llm_adapter():
    """Adaptador real de Ollama para pruebas de integración."""
    from infrastructure.adapters.config.ollama import OllamaConfig
    from infrastructure.adapters.llm_provider.ollama_adapter import OllamaAdapter

    config = OllamaConfig(model_name="llama3.1:latest")
    return OllamaAdapter(config=config)


@pytest.fixture
def fs_adapter(tmp_path):
    return LocalFileSystemAdapter(base_dir=str(tmp_path))


@pytest.fixture
def xml_content(fs_adapter):
    xml_path = Path("tests/requirements/xml/consolidated.xml")
    if not xml_path.exists():
        pytest.skip("❌ No se encontró el XML consolidado")
    return fs_adapter.read_file(str(xml_path))


# --- SUITE DE TESTS POR AGENTE ---


async def test_tag_agent_integration(llm_adapter, xml_content):
    agent = TagAgent(llm_adapter)
    result = await agent.run(xml_content)
    assert isinstance(result, str)
    assert len(result) > 0
    # Opcional: validar que tenga al menos "---" o "importance"
    assert "---" in result or "importance" in result.lower()


async def test_content_agent_integration(llm_adapter, xml_content):
    agent = ContentAgent(llm_adapter)
    result = await agent.run(xml_content)
    assert isinstance(result, str)
    assert len(result) > 50  # contenido mínimo
    # Opcional: validar que tenga título
    assert "# " in result or "title" in result.lower()


async def test_diagram_agent_integration(llm_adapter, xml_content):
    agent = DiagramAgent(llm_adapter)
    result = await agent.run(xml_content)
    assert isinstance(result, str)
    assert len(result) > 0
    # Opcional: validar que tenga alguna pista de diagrama
    assert "mermaid" in result.lower() or "graph" in result.lower()


async def test_matrix_agent_integration(llm_adapter, xml_content):
    agent = MatrixAgent(llm_adapter)
    result = await agent.run(xml_content)
    assert isinstance(result, str)
    assert len(result) > 0
    # Opcional: validar que tenga separadores de tabla
    assert "|" in result or "---" in result


async def test_case_study_agent_integration(llm_adapter, xml_content):
    agent = CaseStudyAgent(llm_adapter)
    result = await agent.run(xml_content)
    assert isinstance(result, str)
    assert len(result) > 50  # texto narrativo mínimo
    # Opcional: validar que no sea código
    assert "```" not in result


async def test_flashcards_agent_integration(llm_adapter, xml_content):
    agent = FlashcardsAgent(llm_adapter)
    result = await agent.run(xml_content)
    assert isinstance(result, str)
    assert len(result) > 0
    # Opcional: validar que tenga separador de pregunta/respuesta
    assert "::" in result or "respuesta" in result.lower()


async def test_naming_agent_integration(llm_adapter, xml_content):
    agent = NamingAgent(llm_adapter)
    result = await agent.run(xml_content)
    assert isinstance(result, str)
    assert len(result) > 5
    # Opcional: validar que no tenga espacios
    assert " " not in result
