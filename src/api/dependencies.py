import logging

from api.routes.fixing import FixingRouter
from api.routes.health import HealthRouter

# ... (Tus imports existentes) ...
from api.routes.pipeline import FullPipelineRouter  # Importamos el nuevo router
from api.routes.reordering import ReorderingRouter
from api.routes.strategic import StrategicResourceRouter
from domain.agents.atomicity_agent import AtomicityAgent
from domain.agents.case_study_agent import CaseStudyAgent
from domain.agents.content_agent import ContentAgent
from domain.agents.diagram_agent import DiagramAgent
from domain.agents.flashcards_agent import FlashcardsAgent
from domain.agents.matrix_agent import MatrixAgent
from domain.agents.naming_agent import NamingAgent
from domain.agents.reordering_agent import ReorderingAgent
from domain.agents.tag_agent import TagAgent
from domain.services.fixing_service import FixingService
from domain.services.reordering_service import ReorderingService
from domain.services.strategic_service import StrategicResourceOrchestrator
from infrastructure.adapters.config.ollama import OllamaConfig
from infrastructure.adapters.llm_provider.ollama_adapter import OllamaAdapter
from infrastructure.adapters.storage.atomic_storage import AtomicSourceStorageTool
from infrastructure.adapters.storage.local_file_system import LocalFileSystemAdapter

# --- 1. CONFIGURACIÓN DE INFRAESTRUCTURA BASE ---
logger = logging.getLogger(__name__)

# Configuración de Ollama (8GB VRAM optimized: 7b)
llm_config = OllamaConfig()
llm_adapter = OllamaAdapter(config=llm_config)
fs_adapter = LocalFileSystemAdapter()

# --- 2. INSTANCIACIÓN DE SERVICIOS (Lógica de Dominio) ---

# Instanciamos los servicios por separado para poder inyectarlos en el Pipeline Maestro
fixing_service = FixingService(
    llm_provider=llm_adapter,
    atomic_storage=AtomicSourceStorageTool(),
    file_system=fs_adapter,
    cleaning_agent=AtomicityAgent(llm_adapter),
)

reordering_service = ReorderingService(
    llm_provider=llm_adapter,
    reordering_agent=ReorderingAgent(llm_adapter),
    fs=fs_adapter,
)

strategic_orchestrator = StrategicResourceOrchestrator(
    fs=fs_adapter,
    tag_agent=TagAgent(llm_adapter),
    content_agent=ContentAgent(llm_adapter),
    diagram_agent=DiagramAgent(llm_adapter),
    matrix_agent=MatrixAgent(llm_adapter),
    case_study_agent=CaseStudyAgent(llm_adapter),
    flashcards_agent=FlashcardsAgent(llm_adapter),
    naming_agent=NamingAgent(llm_adapter),
)

# --- 3. INICIALIZACIÓN DE MÓDULOS (ROUTERS) ---

health_module = HealthRouter(llm_service=llm_adapter)
fixing_module = FixingRouter(fixing_service)
reordering_module = ReorderingRouter(reordering_service)
strategic_module = StrategicResourceRouter(strategic_orchestrator)


full_pipeline_module = FullPipelineRouter(
    fixing_service=fixing_service,
    reordering_service=reordering_service,
    strategic_orchestrator=strategic_orchestrator,
)
