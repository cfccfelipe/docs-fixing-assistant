import asyncio
import logging

from fastapi import Form, HTTPException, Request

from api.routes.base import BaseRouter

logger = logging.getLogger(__name__)


class FullPipelineRouter(BaseRouter):
    def __init__(self, fixing_service, reordering_service, strategic_orchestrator):
        super().__init__()
        self.fixing_service = fixing_service
        self.reordering_service = reordering_service
        self.strategic_orchestrator = strategic_orchestrator
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.router.prefix = "/pipeline"
        self.router.tags = ["Full Mastery Pipeline"]

        @self.router.post("/run")
        async def run_full_pipeline(request: Request, folder_path: str = Form(...)):
            """
            Ejecuta el pipeline completo:
            1. Fix (Limpieza) -> 2. Reorder (Consolidación XML) -> 3. Strategic (Notas Obsidian)
            """
            logger.info(f"🚀 Iniciando Full Pipeline para carpeta: {folder_path}")

            # Tarea principal que envuelve toda la lógica secuencial
            task = asyncio.create_task(self._execute_logic(folder_path))

            # Monitor de desconexión
            async def monitor_disconnect():
                try:
                    while not await request.is_disconnected():
                        await asyncio.sleep(1)
                    logger.warning(
                        "🔌 Cliente desconectado. Cancelando Pipeline Maestro."
                    )
                    task.cancel()
                except asyncio.CancelledError:
                    pass

            disconnect_task = asyncio.create_task(monitor_disconnect())

            try:
                final_output = await task
                return {
                    "status": "success",
                    "pipeline_flow": ["fixed", "reordered", "strategic_generated"],
                    "final_resource": final_output,
                }

            except asyncio.CancelledError:
                raise HTTPException(
                    status_code=499, detail="Pipeline cancelled by client"
                )
            except Exception as e:
                logger.error(f"💥 Error en Pipeline Maestro: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500, detail=f"Pipeline failed: {str(e)}"
                )
            finally:
                if not disconnect_task.done():
                    disconnect_task.cancel()

    async def _execute_logic(self, folder_path: str) -> str:
        """Lógica secuencial de los tres servicios."""

        # FASE 1: FIXING
        logger.info("--- FASE 1: Fixing Folder ---")
        # Asumiendo que devuelve la lista de archivos corregidos
        await self.fixing_service.run_folder_pipeline(folder_path=folder_path)

        # FASE 2: REORDERING (Consolidación en un XML único)
        logger.info("--- FASE 2: Reordering/Consolidation ---")
        # El reordering suele generar un archivo consolidado (ej: consolidated.xml)
        consolidated_xml_path = await self.reordering_service.run_folder_pipeline(
            folder_path=folder_path
        )

        # FASE 3: STRATEGIC (Generación de notas Obsidian)
        logger.info("--- FASE 3: Strategic Generation ---")
        # Usamos el XML consolidado de la fase anterior
        final_note_path = await self.strategic_orchestrator.execute(
            xml_path_str=consolidated_xml_path
        )

        return final_note_path
