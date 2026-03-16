from fastapi import Request

from api.routes.base import BaseRouter
from domain.utils.exceptions import LLMConnectionException


class HealthRouter(BaseRouter):
    """
    Router for deep system diagnostics.
    Verifies internal state and external LLM provider availability.
    """

    def __init__(self, llm_service):
        """
        Injected with the LLM service to check connectivity.
        """
        super().__init__()
        self.llm_service = llm_service
        self._setup_routes()

    def _setup_routes(self) -> None:
        """
        Configures the routes for system health monitoring on the inherited router.
        """
        self.router.prefix = "/system"
        self.router.tags = ["System"]

        @self.router.get("/health")
        async def health_check(request: Request):
            """
            Performs a deep health check including the LLM provider status.
            """
            llm_status = self.llm_service.check_health()

            return {
                "status": "healthy" if llm_status else "degraded",
                "service": "docs-fixing-assistant",
                "dependencies": {"llm_provider": "up" if llm_status else "down"},
            }

        @self.router.get("/health/error-test")
        async def test_error_handling():
            """
            Verifies the JSON infrastructure by forcing a known DomainException.
            """
            raise LLMConnectionException(
                overrides={"provider": "Ollama", "layer": "Infrastructure"}
            )
