import asyncio
import logging
from collections.abc import AsyncGenerator, Iterable
from pathlib import Path

from domain.agents.reordering_agent import ReorderingAgent
from domain.ports.file_system import FileSystemPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class ReorderingService:
    """
    Service that consolidates XML files using a fully asynchronous and
    memory-efficient streaming pipeline.
    """

    def __init__(
        self,
        llm_provider: LLMProviderPort,
        reordering_agent: ReorderingAgent,
        fs: FileSystemPort,
        max_chunk_size: int = 8000,
        overlap_size: int = 200,
        max_concurrency: int = 1,
    ):
        self.llm_provider = llm_provider
        self.reordering_agent = reordering_agent
        self.fs = fs
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def run_folder_pipeline(self, folder_path: str) -> str:
        """
        Runs the full async pipeline:
        Streaming Input -> Parallel Agent Processing -> Streaming Output.
        """
        logger.info(f"[START] Async streaming consolidation: {folder_path}")

        # 1. Obtener archivos usando la interfaz del FS (Independencia de infraestructura)
        # Esto soluciona el fallo en el test unitario.
        xml_files = self.fs.list_files(folder_path, extension="xml")

        if not xml_files:
            raise ValueError(f"No valid XML files found in {folder_path}")

        original_file_names_str = ", ".join([f.name for f in xml_files])

        # 2. Procesar chunks asíncronamente
        # Convertimos el generador a lista para poder usar asyncio.gather
        chunks = [chunk async for chunk in self._stream_chunks(xml_files)]

        tasks = []
        for i, chunk in enumerate(chunks, 1):
            tasks.append(self._process_chunk_with_semaphore(chunk, i))

        # Ejecución paralela respetando el semáforo de la GPU
        refined_parts = await asyncio.gather(*tasks)

        # 3. GENERADOR DE SALIDA (Streaming hacia el disco)
        def final_xml_stream() -> Iterable[str]:
            yield "<root>\n  <metadata>\n"
            yield f"    <ORIGINAL_FILE_NAME>{original_file_names_str}</ORIGINAL_FILE_NAME>\n"
            yield f"    <PARENT_DIRECTORY>{Path(folder_path).name}</PARENT_DIRECTORY>\n  </metadata>\n"
            yield "  <segment id='1'>\n    <atomic_structure>\n"

            for part in refined_parts:
                yield f"      {part}\n"

            yield "    </atomic_structure>\n  </segment>\n</root>"

        # 4. Escritura final delegada al FileSystem (soporta streaming mediante Iterables)
        output_path = Path(folder_path) / "consolidated.xml"
        return self.fs.write_file(str(output_path), final_xml_stream())

    async def _process_chunk_with_semaphore(self, chunk: str, index: int) -> str:
        """Limits concurrent calls to Ollama to protect VRAM."""
        async with self.semaphore:
            logger.info(f"Processing chunk {index} asynchronously...")
            output = await self.reordering_agent.run(chunk)
            return self._normalize_chunk_output(output)

    async def _stream_chunks(self, file_paths: list[Path]) -> AsyncGenerator[str, None]:
        """Reads files one-by-one and yields chunks using the FS port."""
        current_buffer = []
        current_size = 0
        overlap = ""

        for path in file_paths:
            content = self.fs.read_file(str(path))
            lines = content.splitlines()

            for line in lines:
                current_buffer.append(line)
                current_size += len(line)

                if current_size >= self.max_chunk_size:
                    chunk_to_yield = overlap + "\n".join(current_buffer)
                    yield chunk_to_yield
                    overlap = chunk_to_yield[-self.overlap_size :]
                    current_buffer = []
                    current_size = 0

        if current_buffer:
            yield overlap + "\n".join(current_buffer)

    def _normalize_chunk_output(self, chunk_output: str) -> str:
        """Removes LLM-specific tags to maintain a clean internal structure."""
        return (
            chunk_output.replace("<atomic_structure>", "")
            .replace("</atomic_structure>", "")
            .strip()
        )
