from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.services.fixing_service import FixingService

# Habilitar soporte asíncrono para pytest
pytestmark = pytest.mark.asyncio


class TestFixingService:
    @pytest.fixture
    def mock_deps(self):
        """Prepara los mocks de las dependencias siguiendo la nueva firma del servicio."""
        return {
            "llm_provider": MagicMock(),
            "atomic_storage": MagicMock(),
            "file_system": MagicMock(),  # Interfaz unificada FileSystemPort
            "cleaning_agent": MagicMock(),
        }

    @pytest.fixture
    def service(self, mock_deps):
        """Instancia el servicio con las dependencias mockeadas."""
        return FixingService(
            llm_provider=mock_deps["llm_provider"],
            atomic_storage=mock_deps["atomic_storage"],
            file_system=mock_deps["file_system"],
            cleaning_agent=mock_deps["cleaning_agent"],
        )

    async def test_run_full_pipeline_flow(self, service, mock_deps, tmp_path):
        """
        Verifica el flujo asíncrono de 4 pasos:
        1. Atomic Storage (Gen inicial)
        2. FS Read
        3. Agent Run (Async)
        4. Atomic Storage (Merge final)
        """
        # --- Arrange ---
        base_path = str(tmp_path)
        file_name = "test_doc"
        raw_content = "# Header\nContent"
        xml_path = str(tmp_path / "xml" / "test_doc.xml")

        # Configuración de respuestas
        mock_deps["atomic_storage"].execute.return_value = xml_path
        mock_deps[
            "file_system"
        ].read_file.return_value = "<root><metadata></metadata></root>"

        # El agente AHORA es asíncrono
        agent_xml_output = (
            "<atomic_structure><topic>Refined Content</topic></atomic_structure>"
        )
        mock_deps["cleaning_agent"].run = AsyncMock(return_value=agent_xml_output)

        # --- Act ---
        result = await service.run_full_pipeline(raw_content, file_name, base_path)

        # --- Assert ---

        # Paso 1: Generación inicial
        mock_deps["atomic_storage"].execute.assert_any_call(
            raw_content=raw_content,
            file_name=file_name,
            storage_path=str(Path(base_path) / "xml"),
        )

        # Paso 2: Lectura mediante el puerto unificado
        mock_deps["file_system"].read_file.assert_called_with(path=xml_path)

        # Paso 3: El agente recibe el XML (verificamos await implícito)
        mock_deps["cleaning_agent"].run.assert_called_with(
            "<root><metadata></metadata></root>"
        )

        # Paso 4: Merge final
        mock_deps["atomic_storage"].execute.assert_any_call(
            raw_content=agent_xml_output,
            file_name=file_name,
            storage_path=str(Path(base_path) / "xml"),
        )

        assert result == xml_path

    async def test_run_folder_pipeline(self, service, mock_deps, tmp_path):
        """Verifica que el procesamiento de carpetas sea asíncrono y use el FS unificado."""
        # --- Arrange ---
        (tmp_path / "one.md").write_text("content 1")
        (tmp_path / "two.md").write_text("content 2")

        # Mockeamos el método interno
        with patch.object(
            service, "run_full_pipeline", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = "path/to/xml"

            # --- Act ---
            results = await service.run_folder_pipeline(str(tmp_path))

            # --- Assert ---
            assert len(results) == 2
            assert mock_run.call_count == 2
            # El file_system lee los .md originales
            assert mock_deps["file_system"].read_file.call_count == 2

    async def test_get_strategic_outputs(self, service, mock_deps):
        """Prueba la coordinación asíncrona con el agente."""
        mock_deps["cleaning_agent"].run = AsyncMock(return_value="<root>cleaned</root>")

        output = await service._get_strategic_outputs("<xml/>")

        assert output == {"atomicity": "<root>cleaned</root>"}
        mock_deps["cleaning_agent"].run.assert_called_once_with("<xml/>")
