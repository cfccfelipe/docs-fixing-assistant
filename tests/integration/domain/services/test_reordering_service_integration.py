from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.services.reordering_service import ReorderingService
from infrastructure.adapters.storage.local_file_system import LocalFileSystemAdapter

# Habilitar soporte para tests asíncronos
pytestmark = pytest.mark.asyncio


class TestReorderingIntegration:
    @pytest.fixture
    def setup_files(self, tmp_path):
        """Crea una estructura de carpetas real para el test de integración."""
        folder = tmp_path / "source_docs"
        folder.mkdir(parents=True, exist_ok=True)

        # Simulamos archivos XML pequeños para el test
        (folder / "part1.xml").write_text(
            "<atomic_structure><topic id='1'>Contenido A</topic></atomic_structure>"
        )
        (folder / "part2.xml").write_text(
            "<atomic_structure><topic id='2'>Contenido B</topic></atomic_structure>"
        )
        return folder

    async def test_reordering_pipeline_integration(self, setup_files, tmp_path):
        """
        Verifica la orquestación del ReorderingService:
        Streaming Input -> Parallel Async Processing -> Streaming Output.
        """
        # 🚨 CAMBIO 1: El agente ahora es asíncrono
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(
            return_value="<topic id='test'>Refined Content</topic>"
        )

        # 🚨 CAMBIO 2: Usamos el adaptador de FileSystem unificado
        # Inicializamos con base_dir=tmp_path para evitar errores de path traversal
        fs_adapter = LocalFileSystemAdapter(base_dir=str(tmp_path))

        # Instancia del servicio con la firma nueva
        service = ReorderingService(
            llm_provider=MagicMock(),
            reordering_agent=mock_agent,
            fs=fs_adapter,
            max_chunk_size=1000,
            max_concurrency=2,  # Testeamos que el semáforo no bloquee
        )

        # 🚨 CAMBIO 3: Ejecución asíncrona (await)
        output_path_str = await service.run_folder_pipeline(str(setup_files))

        # Assertions de archivo
        output_path = Path(output_path_str)
        assert output_path.exists()
        assert output_path.name == "consolidated.xml"

        # 🚨 CAMBIO 4: Validar el contenido generado por el Streaming Writer
        content = output_path.read_text()
        assert "<root>" in content
        assert "<metadata>" in content
        assert "ORIGINAL_FILE_NAME" in content
        assert "Refined Content" in content  # El contenido del mock del agente

        # Verificar que la orquestación llamó al agente
        assert mock_agent.run.called
