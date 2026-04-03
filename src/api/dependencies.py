import logging

from api.routes.health import HealthRouter
from api.routes.orchestration import OrchestrationRouter
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter
from infrastructure.storage.local_file_system_adapter import LocalFileSystemAdapter
from api.config import settings

# --- 1. CONFIGURACIÓN DE INFRAESTRUCTURA BASE ---
logger = logging.getLogger(__name__)

# Configuración de Ollama (8GB VRAM optimized: 7b)
llm_config = settings.ollama
llm_adapter = OllamaAdapter(config=llm_config)
fs_adapter = LocalFileSystemAdapter()

# --- 3. INICIALIZACIÓN DE MÓDULOS (ROUTERS) ---
health_module = HealthRouter(llm_service=llm_adapter)
orchestration_module = OrchestrationRouter()
