import pytest

# Orquestación
from domain.orchestrator.tool_registry import ToolRegistry

# Infraestructura y Tools
from infrastructure.storage.local_file_system_adapter import LocalFileSystemAdapter
from infrastructure.tools.delete_file_tool import DeleteFileTool
from infrastructure.tools.list_files_tool import ListFilesTool
from infrastructure.tools.read_file_tool import ReadFileTool
from infrastructure.tools.write_file_tool import WriteFileTool


@pytest.fixture
def setup_orchestration(tmp_path):
    """
    Ensamblaje real de la infraestructura para el test de integración.
    """
    # 1. El Obrero (Adapter)
    adapter = LocalFileSystemAdapter(base_path=tmp_path)

    # 2. Las Herramientas (Wrappers)
    tools = [
        ReadFileTool(adapter),
        WriteFileTool(adapter),
        ListFilesTool(adapter),
        DeleteFileTool(adapter),
    ]

    # 3. El Cerebro (Registry)
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)

    return registry, tmp_path


def test_full_filesystem_workflow(setup_orchestration):
    """
    Simula una secuencia de comandos que un CoderNode enviaría al Registry.
    """
    registry, base_path = setup_orchestration
    file_name = "integration_test.py"
    content = "print('Hello Integration')"

    # 1. PASO: Escribir un archivo
    # El Registry recibe el nombre de la tool y los kwargs (como lo haría el LLM)
    write_result = registry.execute("write_file", path=file_name, content=content)
    assert file_name in write_result
    assert (base_path / file_name).exists()

    # 2. PASO: Listar archivos para verificar que aparece
    list_result = registry.execute("list_files", folder_path=".")
    assert file_name in list_result

    # 3. PASO: Leer el contenido y verificar integridad
    read_result = registry.execute("read_file", path=file_name)
    assert read_result == content

    # 4. PASO: Borrar el archivo
    delete_result = registry.execute("delete_file", path=file_name)
    assert "deleted successfully" in delete_result.lower()
    assert not (base_path / file_name).exists()


def test_security_integration_via_registry(setup_orchestration):
    """
    Verifica que la seguridad del Mixin se mantenga a través de toda la cadena.
    """
    registry, _ = setup_orchestration

    # Intentar un Path Traversal a través del Registry
    with pytest.raises(PermissionError):
        registry.execute("read_file", path="../../../../etc/passwd")
