import asyncio
import logging
import re
import time
from pathlib import Path

from domain.agents.case_study_agent import CaseStudyAgent
from domain.agents.content_agent import ContentAgent
from domain.agents.diagram_agent import DiagramAgent
from domain.agents.flashcards_agent import FlashcardsAgent
from domain.agents.matrix_agent import MatrixAgent
from domain.agents.naming_agent import NamingAgent
from domain.agents.tag_agent import TagAgent
from domain.ports.file_system import FileSystemPort

logger = logging.getLogger(__name__)


class StrategicResourceOrchestrator:
    """
    Orquestador para Obsidian.
    Mantiene el archivo principal en la raíz y organiza secundarios en '.md/'.
    """

    def __init__(
        self,
        fs: FileSystemPort,
        tag_agent: TagAgent,
        content_agent: ContentAgent,
        diagram_agent: DiagramAgent,
        matrix_agent: MatrixAgent,
        case_study_agent: CaseStudyAgent,
        flashcards_agent: FlashcardsAgent,
        naming_agent: NamingAgent,
        max_concurrency: int = 1,
    ):
        self.fs = fs
        self.tag_agent = tag_agent
        self.content_agent = content_agent
        self.diagram_agent = diagram_agent
        self.matrix_agent = matrix_agent
        self.case_study_agent = case_study_agent
        self.flashcards_agent = flashcards_agent
        self.naming_agent = naming_agent
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def execute(self, xml_path_str: str, force_refresh: bool = False) -> str:
        xml_path = Path(xml_path_str)
        if not xml_path.exists():
            raise FileNotFoundError(f"Source XML not found: {xml_path_str}")

        xml_content = self.fs.read_file(xml_path_str)

        async with self.semaphore:
            logger.info(f"🚀 Procesando: {xml_path.name}")

            # 1. Generar identidad del recurso
            ai_name = (
                await self.naming_agent.run(xml_content) or "Strategic_Resource_Note"
            )
            safe_name = self._sanitize_name(ai_name)

            # 2. Configurar rutas (Main vs Subfolder)
            parent_dir = xml_path.parent.parent.resolve()
            subfolder_dir = parent_dir / "resources"

            # Asegurar que la subcarpeta existe
            if not subfolder_dir.exists():
                subfolder_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Subcarpeta creada: {subfolder_dir}")

            # 3. Generar Archivo Principal
            yaml_metadata = await self.tag_agent.run(xml_content) or ""
            body = await self.content_agent.run(xml_content) or ""

            # Limpieza básica de intros del LLM
            body = re.sub(
                r"(?im)^(The provided XML|This document|### .*Overview).*$", "", body
            ).strip()

            main_file = parent_dir / f"{safe_name}.md"
            main_buffer = [
                yaml_metadata,
                f"# {ai_name.replace('_', ' ')}",
                f"\n{body}\n",
            ]
            self._sync_file(main_file, main_buffer)

            # 4. Procesar Agentes Secundarios en la subcarpeta
            secondary_tasks = [
                ("diagram", self.diagram_agent, f"{safe_name}_Diagram.md"),
                ("matrix", self.matrix_agent, f"{safe_name}_Matrix.md"),
                ("case_study", self.case_study_agent, f"{safe_name}_CaseStudy.md"),
                ("flashcards", self.flashcards_agent, f"{safe_name}_Flashcards.md"),
            ]

            for key, agent, filename in secondary_tasks:
                try:
                    logger.info(f"🧠 Agente secundario: {key}")
                    result = await agent.run(xml_content)
                    if result:
                        # Guardar en la subcarpeta .md/
                        target_path = subfolder_dir / filename
                        self._sync_file(target_path, [result])
                        logger.info(f"✅ Guardado en subcarpeta: {filename}")
                except Exception as e:
                    logger.error(f"❌ Error en {key}: {str(e)}")

        return str(main_file)

    def _sync_file(self, path: Path, buffer: list[str]) -> None:
        clean_buffer = [part for part in buffer if part.strip()]
        full_content = "\n".join(clean_buffer)
        self.fs.write_file(str(path), full_content or "")

    def _sanitize_name(self, name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_]", "", name or "").strip("_")
        return safe[:64] or f"Strategic_{int(time.time())}"
