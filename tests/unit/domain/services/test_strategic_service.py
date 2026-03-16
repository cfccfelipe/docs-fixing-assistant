from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from domain.services.strategic_service import (
    StrategicResourceOrchestrator,
)


@pytest.fixture
def mock_fs():
    """Mock del sistema de archivos."""
    return MagicMock()


@pytest.fixture
def mock_agents():
    """Diccionario con todos los agentes mockeados, incluyendo el nuevo NamingAgent."""
    return {
        "tag": AsyncMock(),
        "content": AsyncMock(),
        "diagram": AsyncMock(),
        "matrix": AsyncMock(),
        "case_study": AsyncMock(),
        "flashcards": AsyncMock(),
        "naming": AsyncMock(),
    }


@pytest.fixture
def orchestrator(mock_fs, mock_agents):
    """Instancia del orquestador con todas sus dependencias inyectadas."""
    return StrategicResourceOrchestrator(
        fs=mock_fs,
        tag_agent=mock_agents["tag"],
        content_agent=mock_agents["content"],
        diagram_agent=mock_agents["diagram"],
        matrix_agent=mock_agents["matrix"],
        case_study_agent=mock_agents["case_study"],
        flashcards_agent=mock_agents["flashcards"],
        naming_agent=mock_agents["naming"],
    )


@pytest.mark.asyncio
async def test_execute_success(orchestrator, mock_fs, mock_agents, tmp_path):
    """
    Verifica la ejecución exitosa del pipeline completo.
    Valida la integración del NamingAgent y la persistencia en el directorio correcto.
    """
    root_dir = tmp_path / "resource_folder"
    xml_dir = root_dir / "xml"
    xml_dir.mkdir(parents=True)
    xml_file = xml_dir / "consolidated.xml"
    xml_file.write_text("<root>data</root>")

    xml_path_str = str(xml_file)

    ai_name = "Cloud_Architecture_Design_Strategic"
    expected_final_path = root_dir / f"{ai_name}.md"

    mock_fs.read_file.return_value = "<root>data</root>"
    mock_agents["naming"].run.return_value = ai_name
    mock_agents["tag"].run.return_value = "---yaml---"
    mock_agents["content"].run.return_value = "Body Content"
    mock_agents["diagram"].run.return_value = "Mermaid"
    mock_agents["matrix"].run.return_value = "Matrix"
    mock_agents["case_study"].run.return_value = "Case Study"
    mock_agents["flashcards"].run.return_value = "Flashcards"

    result_path = await orchestrator.execute(xml_path_str)

    assert result_path == str(expected_final_path)

    mock_agents["naming"].run.assert_called_once_with("<root>data</root>")
    for key, agent in mock_agents.items():
        agent.run.assert_called_once_with("<root>data</root>")

    # Verificar que se escribió el archivo principal entre las múltiples llamadas
    mock_fs.write_file.assert_any_call(str(expected_final_path), ANY)

    # Recuperar la llamada al archivo principal
    calls = mock_fs.write_file.call_args_list
    main_call = [c for c in calls if c.args[0] == str(expected_final_path)][0]
    dest_path, content = main_call.args

    assert dest_path == str(expected_final_path)
    assert f"# {ai_name.replace('_', ' ')}" in content
    assert "---yaml---" in content
    assert "## 🃏 Knowledge Retention" in content


@pytest.mark.asyncio
async def test_execute_file_not_found(orchestrator):
    """Verifica que se lance FileNotFoundError si el XML de origen no existe."""
    with pytest.raises(FileNotFoundError):
        await orchestrator.execute("invalid/path/xml/consolidated.xml")


@pytest.mark.asyncio
async def test_execute_logic_with_ai_title(
    orchestrator, mock_fs, mock_agents, tmp_path
):
    """Verifica que el H1 del documento use el nombre dictado por la IA."""
    root_dir = tmp_path / "any_folder"
    xml_dir = root_dir / "xml"
    xml_dir.mkdir(parents=True)
    xml_file = xml_dir / "consolidated.xml"
    xml_file.write_text("...")

    mock_fs.read_file.return_value = "..."

    for agent in mock_agents.values():
        agent.run.return_value = "ok"

    mock_agents["naming"].run.return_value = "Custom_AI_Title_Strategic"

    await orchestrator.execute(str(xml_file))

    # Buscar la llamada al archivo principal
    calls = mock_fs.write_file.call_args_list
    main_call = [c for c in calls if "Custom_AI_Title_Strategic.md" in c.args[0]][0]
    content = main_call.args[1]

    assert "# Custom AI Title Strategic" in content
