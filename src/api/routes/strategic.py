import asyncio
import logging

from fastapi import Form, HTTPException, Request

from api.routes.base import BaseRouter
from domain.services.strategic_service import StrategicResourceOrchestrator
from domain.utils.exceptions import LLMConnectionException

logger = logging.getLogger(__name__)


class StrategicResourceRouter(BaseRouter):
    def __init__(self, orchestrator: StrategicResourceOrchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.router.prefix = "/strategic"
        self.router.tags = ["Strategic Resources"]

        @self.router.post("/generate")
        async def generate_resource(request: Request, xml_path: str = Form(...)):
            logger.info(f"📥 Solicitud recibida: {xml_path}")

            # Creamos la tarea de ejecución
            task = asyncio.create_task(self.orchestrator.execute(xml_path_str=xml_path))

            # Helper para monitorear desconexión de forma eficiente
            async def monitor_disconnect():
                try:
                    while True:
                        if await request.is_disconnected():
                            logger.warning(
                                f"🔌 Cliente desconectado. Cancelando tarea para: {xml_path}"
                            )
                            task.cancel()
                            break
                        await asyncio.sleep(
                            1
                        )  # Un intervalo de 1s es suficiente y consume menos CPU
                except asyncio.CancelledError:
                    pass

            disconnect_task = asyncio.create_task(monitor_disconnect())

            try:
                # Esperamos el resultado de la orquestación
                final_path = await task
                return {
                    "status": "success",
                    "message": "Recurso estratégico generado correctamente.",
                    "output_path": final_path,
                }

            except asyncio.CancelledError:
                # 499 es el estándar (Client Closed Request) usado por Nginx/Cloudflare
                raise HTTPException(
                    status_code=499, detail="Request cancelled by client"
                )
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except LLMConnectionException as e:
                raise HTTPException(
                    status_code=504, detail=f"LLM Timeout/Error: {str(e)}"
                )
            except Exception as e:
                logger.error(f"💥 Error crítico en pipeline: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500, detail="Internal server error in agent pipeline"
                )

            finally:
                # Limpieza crucial: detener el monitor de desconexión si la tarea principal terminó
                if not disconnect_task.done():
                    disconnect_task.cancel()
