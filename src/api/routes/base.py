from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from domain.constants.errors import COMMON_RESPONSES


class BaseRouter:
    """
    Base class for API routers to share common configuration.
    Ensures a consistent interface for FastAPI's include_router.
    """

    def __init__(self, templates_dir: str = "templates"):
        """
        Initializes common components like Jinja2 templates and the APIRouter instance.
        """
        self.templates = Jinja2Templates(directory=templates_dir)
        self.common_responses = COMMON_RESPONSES

        self.router: APIRouter = APIRouter()
