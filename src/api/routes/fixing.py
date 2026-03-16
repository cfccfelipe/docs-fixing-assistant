import asyncio
from pathlib import Path

from fastapi import Form, HTTPException, Request

from api.routes.base import BaseRouter


class FixingRouter(BaseRouter):
    def __init__(self, fixing_service):
        super().__init__()
        self.fixing_service = fixing_service
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.router.prefix = "/fix"
        self.router.tags = ["Document Fixing"]

        @self.router.post("/file")
        async def fix_file(request: Request, file_path: str = Form(...)):
            """
            Processes a single Markdown file asynchronously.
            Supports cancellation if client disconnects.
            """
            md_file = Path(file_path)
            if not md_file.exists():
                raise HTTPException(status_code=404, detail="File not found")

            task = asyncio.create_task(
                self.fixing_service.run_full_pipeline(file_path=file_path)
            )

            try:
                result_path = await task
                return {"status": "success", "fixed_file": result_path}
            except asyncio.CancelledError:
                task.cancel()
                raise HTTPException(
                    status_code=499, detail="Request cancelled by client"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/folder")
        async def fix_folder(request: Request, folder_path: str = Form(...)):
            """
            Processes all Markdown files in a folder asynchronously.
            Supports cancellation if client disconnects.
            """
            task = asyncio.create_task(
                self.fixing_service.run_folder_pipeline(folder_path=folder_path)
            )

            try:
                results = await task
                return {"status": "success", "fixed_files": results}
            except asyncio.CancelledError:
                task.cancel()
                raise HTTPException(
                    status_code=499, detail="Request cancelled by client"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
