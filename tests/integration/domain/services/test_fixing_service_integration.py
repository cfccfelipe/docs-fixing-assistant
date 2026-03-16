from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import defusedxml.ElementTree as dET
import pytest

from domain.services.fixing_service import FixingService
from domain.utils.exceptions import FileSystemException
from infrastructure.adapters.storage.atomic_storage import AtomicSourceStorageTool
from infrastructure.adapters.storage.local_file_system import LocalFileSystemAdapter

# Marcamos todo el módulo para que soporte tests asíncronos
pytestmark = pytest.mark.asyncio


class TestFixingServiceIntegration:
    @pytest.fixture
    def service_setup(self, tmp_path):
        """Configura el servicio con infraestructura real y mocks de IA asíncronos."""
        base_dir = tmp_path / "integration_project"
        base_dir.mkdir(parents=True, exist_ok=True)

        # 🚨 CAMBIO 1: Usamos AsyncMock porque el AgentPort ahora es async
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(
            return_value="<atomic_structure><topic id='t1'>Ok</topic></atomic_structure>"
        )

        # 🚨 CAMBIO 2: Usamos el adaptador unificado de FileSystem
        fs_adapter = LocalFileSystemAdapter(base_dir=str(base_dir))

        service = FixingService(
            llm_provider=MagicMock(),  # El provider puede ser MagicMock si no se llama directamente
            atomic_storage=AtomicSourceStorageTool(),
            file_system=fs_adapter,
            cleaning_agent=mock_agent,
        )
        return service, base_dir, mock_agent

    async def test_run_full_pipeline_success(self, service_setup):
        """Verifica el flujo exitoso de creación y actualización (Async)."""
        service, base_dir, _ = service_setup

        xml_path_str = await service.run_full_pipeline("# Title", "doc", str(base_dir))

        xml_path = Path(xml_path_str)
        assert xml_path.exists()
        assert "doc" in xml_path.read_text()

    async def test_fixing_pipeline_agent_failure(self, service_setup):
        """Verifica que lance FileSystemException si el agente devuelve basura."""
        service, base_dir, mock_agent = service_setup

        # Ajustamos el AsyncMock para devolver basura
        mock_agent.run.return_value = "INVALID_NON_XML_STRING"

        with pytest.raises(FileSystemException):
            await service.run_full_pipeline("content", "fail_doc", str(base_dir))

    async def test_xml_structure_compliance(self, service_setup):
        """Valida el contrato del XML generado inspeccionando nodos clave."""
        service, base_dir, _ = service_setup

        xml_path_str = await service.run_full_pipeline(
            "# Test", "compliance", str(base_dir)
        )

        root = dET.fromstring(Path(xml_path_str).read_text())
        assert root.tag == "root"
        assert root.find("metadata/ORIGINAL_FILE_NAME").text == "compliance"

        # Verificamos que el merge ocurrió correctamente
        segment = root.find("segment[@id='1']")
        assert segment.find("atomic_structure/topic").attrib["id"] == "t1"

    async def test_run_folder_pipeline_integration(self, service_setup):
        """Verifica el procesamiento por lotes en una carpeta real."""
        service, base_dir, _ = service_setup
        (base_dir / "doc1.md").write_text("# Doc 1")
        (base_dir / "doc2.md").write_text("# Doc 2")

        results = await service.run_folder_pipeline(str(base_dir))

        assert len(results) == 2
        assert all(Path(p).exists() for p in results)
