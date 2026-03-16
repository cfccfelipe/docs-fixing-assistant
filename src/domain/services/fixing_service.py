import logging
import re
from pathlib import Path

import defusedxml.ElementTree as dET

from domain.ports.agent import AgentPort
from domain.ports.file_system import FileSystemPort
from domain.ports.llm_provider import LLMProviderPort
from domain.ports.tool import ITool
from domain.utils.exceptions import FileSystemException

logger = logging.getLogger(__name__)


class FixingService:
    """
    Service responsible for the XML-centric lifecycle of fixing documentation.
    Uses an unified FileSystemPort for I/O operations and supports async agent execution.
    """

    def __init__(
        self,
        llm_provider: LLMProviderPort,
        atomic_storage: ITool,
        file_system: FileSystemPort,
        cleaning_agent: AgentPort,
    ):
        self.llm_provider = llm_provider
        self.atomic_storage = atomic_storage
        self.fs = file_system
        self.atomicity_agent = cleaning_agent

    async def run_full_pipeline(
        self, raw_content: str, file_name: str, base_path: str
    ) -> str:
        """
        Runs the full transformation pipeline for a single file asynchronously.
        Maintains the strict 2-metadata contract.
        """
        logger.info(f"[START] Async pipeline for file: {file_name}")

        xml_dir = Path(base_path) / "xml"
        xml_dir.mkdir(parents=True, exist_ok=True)

        # Paso 1: Generación inicial mediante Atomic Storage
        # Se encarga de crear el sobre XML base con los metadatos iniciales
        logger.info("Step 1: Generating initial atomic XML structure...")
        xml_path: str = self.atomic_storage.execute(
            raw_content=raw_content,
            file_name=file_name,
            storage_path=str(xml_dir),
        )

        # Paso 2: Lectura de la estructura mediante el FileSystem unificado
        xml_structure: str = self.fs.read_file(path=xml_path)

        # Paso 3: Coordinación asíncrona con el Agente de IA
        agents_output = await self._get_strategic_outputs(xml_structure)

        if "atomicity" in agents_output:
            raw_agent_text = agents_output["atomicity"]
            clean_xml = self._sanitize_agent_output(raw_agent_text)
            agents_output["atomicity"] = clean_xml

            try:
                # Validación de seguridad para asegurar que el LLM no rompió el XML
                dET.fromstring(clean_xml)
            except Exception as e:
                logger.error(f"Agent generated invalid XML for {file_name}: {e}")
                raise FileSystemException(
                    overrides={"message": f"IA regresó XML inválido: {e}"}
                )

        # Paso 4: Smart Merge (Inyección de la lógica limpia preservando el sobre)
        if "atomicity" in agents_output:
            logger.info(f"Step 4: Merging cleaned logic into {file_name}...")
            self.atomic_storage.execute(
                raw_content=agents_output["atomicity"],
                file_name=file_name,
                storage_path=str(xml_dir),
            )

        logger.info(f"[END] Pipeline finished for {file_name}")
        return xml_path

    async def run_folder_pipeline(self, folder_path: str) -> list[str]:
        """
        Processes all Markdown files in a folder asynchronously.
        """
        base_dir = Path(folder_path)
        # Usamos el FileSystem unificado para listar (o glob directo si es local)
        md_files = list(base_dir.glob("*.md"))

        if not md_files:
            logger.warning(f"No markdown files found in {folder_path}")
            return []

        results: list[str] = []
        for md_file in md_files:
            # Lectura asíncrona-friendly mediante la interfaz
            raw_content: str = self.fs.read_file(path=str(md_file))

            output_path = await self.run_full_pipeline(
                raw_content=raw_content,
                file_name=md_file.stem,
                base_path=str(base_dir),
            )
            results.append(output_path)

        return results

    def _sanitize_agent_output(self, text: str) -> str:
        """Extracts balanced XML block from LLM response."""
        text = re.sub(r"```xml\s*|```", "", text).strip()
        match = re.search(
            r"(<(?P<tag>[a-zA-Z0-9_:-]+).*?>.*</(?P=tag)>)", text, re.DOTALL
        )
        if match:
            return match.group(1).strip()
        return text.strip()

    async def _get_strategic_outputs(self, xml_content: str) -> dict[str, str]:
        """Calls the agent asynchronously without blocking the loop."""
        atomicity = await self.atomicity_agent.run(xml_content)
        return {"atomicity": atomicity}
