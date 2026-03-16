import asyncio
import logging

from fastapi import Form, HTTPException, Request

from api.routes.base import BaseRouter


class ReorderingRouter(BaseRouter):
    def __init__(self, reordering_service):
        super().__init__()
        self.reordering_service = reordering_service
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.router.prefix = "/reorder"
        self.router.tags = ["Document Reordering"]

        @self.router.post("/folder")
        async def reorder_folder(request: Request, folder_path: str = Form(...)):
            """
            Consolida los archivos XML de una carpeta usando streaming y async.
            Soporta cancelación si el cliente corta la conexión.
            """
            # Creamos la tarea explícitamente para poder cancelarla si es necesario
            task = asyncio.create_task(
                self.reordering_service.run_folder_pipeline(folder_path=folder_path)
            )

            try:
                result_path = await task
                return {"status": "success", "consolidated_file": result_path}
            except asyncio.CancelledError:
                task.cancel()
                raise HTTPException(
                    status_code=499, detail="Request cancelled by client"
                )
            except Exception as e:
                logging.error(f"Error en reorder_folder: {str(e)}")
                raise HTTPException(
                    status_code=500, detail=f"Error procesando la carpeta: {str(e)}"
                )
