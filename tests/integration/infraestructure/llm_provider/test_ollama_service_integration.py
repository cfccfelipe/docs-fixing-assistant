import time
from pathlib import Path

import pytest
import requests

from domain.agents.atomicity_agent import AtomicityAgent
from domain.agents.reordering_agent import ReorderingAgent
from domain.services.fixing_service import FixingService
from domain.services.reordering_service import ReorderingService
from infrastructure.adapters.config.ollama import OllamaConfig
from infrastructure.adapters.llm_provider.ollama_adapter import OllamaAdapter
from infrastructure.adapters.storage.atomic_storage import AtomicSourceStorageTool
from infrastructure.adapters.storage.local_file_system import LocalFileSystemAdapter

# Marcamos todo el módulo para ejecución asíncrona
pytestmark = pytest.mark.asyncio


class TestOllamaIntegration:
    @pytest.fixture(scope="module")
    def ollama_available(self):
        """Verifica disponibilidad y calienta el modelo local para evitar latencias."""
        base_url = "http://localhost:11434"
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=3)
            if response.status_code != 200:
                pytest.skip("Ollama respondió con error de estado.")

            # Warm-up: Carga el modelo en VRAM
            requests.post(
                f"{base_url}/api/generate",
                json={"model": "llama3.1:latest", "keep_alive": "5m"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("No se pudo conectar con Ollama en localhost:11434")

    @pytest.fixture
    def fs_adapter(self, tmp_path):
        """Adaptador de sistema de archivos real con base_dir seguro."""
        return LocalFileSystemAdapter(base_dir=str(tmp_path))

    @pytest.fixture
    def llm_adapter(self):
        """Adaptador de Ollama real."""
        config = OllamaConfig(model_name="llama3.1:latest")
        return OllamaAdapter(config=config)

    @pytest.mark.integration
    async def test_fixing_service_with_real_llm(
        self, ollama_available, llm_adapter, fs_adapter, tmp_path
    ):
        """Test E2E: Verifica la transformación y el cumplimiento del contrato limpio."""
        service = FixingService(
            llm_provider=llm_adapter,
            atomic_storage=AtomicSourceStorageTool(),
            file_system=fs_adapter,
            cleaning_agent=AtomicityAgent(llm_adapter),
        )

        file_name = "auth_specs"
        raw_md = "# Auth\nEl sistema debe usar OAuth2 con tokens JWT."

        start_time = time.time()
        xml_path_str = await service.run_full_pipeline(
            raw_content=raw_md, file_name=file_name, base_path=str(tmp_path)
        )
        duration = time.time() - start_time

        xml_path = Path(xml_path_str)
        assert xml_path.exists()
        content = xml_path.read_text()

        assert "<ORIGINAL_FILE_NAME>auth_specs</ORIGINAL_FILE_NAME>" in content
        assert "<PARENT_DIRECTORY>" in content
        assert "<VERSION>" not in content
        assert "<atomic_structure>" in content
        assert any(word in content for word in ["JWT", "OAuth2", "tokens"])

        print(f"\n[OLLAMA FIXING DURATION]: {duration:.2f}s")

    @pytest.mark.integration
    async def test_reordering_service_integrity_and_streaming(
        self, ollama_available, llm_adapter, fs_adapter, tmp_path
    ):
        """Verifica la consolidación de múltiples fuentes XML usando el flujo de streaming."""
        service = ReorderingService(
            llm_provider=llm_adapter,
            reordering_agent=ReorderingAgent(llm_adapter),
            fs=fs_adapter,
            max_chunk_size=500,  # Chunks pequeños para forzar múltiples llamadas
        )

        source_dir = tmp_path / "integrity_check"
        source_dir.mkdir()

        # 1. Arrange: Creamos archivos con contenido específico
        files_data = {
            "auth.xml": "KEYWORD_AUTH_LOGIC",
            "db.xml": "KEYWORD_DB_CONN",
        }
        for name, content in files_data.items():
            (source_dir / name).write_text(
                f"<root><segment id='1'>{content}</segment></root>"
            )

        # 2. Act
        output_path = await service.run_folder_pipeline(str(source_dir))

        # 3. Assert
        final_xml = Path(output_path).read_text()
        assert Path(output_path).exists()
        assert "consolidated.xml" in output_path

        for keyword in files_data.values():
            assert keyword in final_xml

        assert "<PARENT_DIRECTORY>integrity_check</PARENT_DIRECTORY>" in final_xml
        assert "auth.xml" in final_xml
        assert "db.xml" in final_xml
        assert "<VERSION>" not in final_xml

        print("\n[OLLAMA REORDERING SUCCESSFUL]")
