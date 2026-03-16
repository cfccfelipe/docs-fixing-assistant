from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.services.reordering_service import ReorderingService

# Habilitar soporte asíncrono para pytest
pytestmark = pytest.mark.asyncio


class TestReorderingService:
    @pytest.fixture
    def mock_deps(self):
        """Prepara los mocks siguiendo la arquitectura asíncrona y de streaming."""
        return {
            "llm_provider": MagicMock(),
            "reordering_agent": MagicMock(),
            "fs": MagicMock(),  # FileSystemPort unificado
        }

    @pytest.fixture
    def service(self, mock_deps):
        """Instancia el servicio con dependencias mockeadas y configuración de test."""
        return ReorderingService(
            llm_provider=mock_deps["llm_provider"],
            reordering_agent=mock_deps["reordering_agent"],
            fs=mock_deps["fs"],
            max_chunk_size=100,
            overlap_size=10,
            max_concurrency=2,
        )

    async def test_run_folder_pipeline_success(self, service, mock_deps, tmp_path):
        """
        Verifica que el pipeline:
        1. Delega el listado de archivos al puerto fs (independencia de infraestructura).
        2. Procesa chunks asíncronamente mediante el agente.
        3. Ensambla la salida mediante un generador de streaming.
        """
        # --- Arrange ---
        folder = tmp_path / "data"
        folder.mkdir()

        # Creamos referencias de Path (no es necesario que existan en disco
        # porque mockearemos list_files y read_file, lo que hace el test puramente unitario)
        xml_files = [Path("file1.xml"), Path("file2.xml")]

        # Configuramos el mock para que devuelva nuestra lista controlada
        mock_deps["fs"].list_files.return_value = xml_files
        mock_deps["fs"].read_file.side_effect = [
            "<root>content1</root>",
            "<root>content2</root>",
        ]

        # El agente debe ser un AsyncMock para soportar 'await'
        mock_deps["reordering_agent"].run = AsyncMock(
            return_value="<topic>refined_data</topic>"
        )

        # Configuramos el retorno del path de salida
        expected_output_path = str(folder / "consolidated.xml")
        mock_deps["fs"].write_file.return_value = expected_output_path

        # --- Act ---
        result_path = await service.run_folder_pipeline(str(folder))

        # --- Assert ---
        # 1. Verificamos que NO se usó pathlib directamente para listar, sino el puerto
        mock_deps["fs"].list_files.assert_called_once_with(str(folder), extension="xml")

        # 2. Verificamos la lectura de los archivos listados
        assert mock_deps["fs"].read_file.call_count == 2

        # 3. Verificamos la llamada asíncrona al agente
        assert mock_deps["reordering_agent"].run.called

        # 4. Verificamos la escritura eficiente (Streaming)
        args, _ = mock_deps["fs"].write_file.call_args
        assert args[0] == expected_output_path
        # Verificamos que el contenido enviado sea un objeto iterable (el generador XML)
        assert hasattr(args[1], "__iter__")

        assert result_path == expected_output_path

    async def test_run_folder_pipeline_empty_folder(self, service, mock_deps, tmp_path):
        """Verifica que el servicio lance ValueError si el puerto devuelve una lista vacía."""
        mock_deps["fs"].list_files.return_value = []

        with pytest.raises(ValueError, match="No valid XML files found"):
            await service.run_folder_pipeline(str(tmp_path))

    async def test_normalize_chunk_output(self, service):
        """Prueba unitaria de la lógica de limpieza de tags del LLM."""
        raw_output = "<atomic_structure>\n  <topic>Test</topic>\n</atomic_structure>"
        normalized = service._normalize_chunk_output(raw_output)

        assert "<atomic_structure>" not in normalized
        assert "</atomic_structure>" not in normalized
        assert "<topic>Test</topic>" in normalized
