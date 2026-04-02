from langgraph.graph import StateGraph

from domain.models.state_model import AgentState
from domain.orchestrator.agent_registry import AgentRegistry


def create_workflow(registry: AgentRegistry):
    # 1. Inicializamos el Grafo con tu Dataclass agnóstica
    # LangGraph usará AgentState como la "memoria compartida"
    workflow = StateGraph(AgentState)

    # 2. Definición de Wrappers (Los Puentes)
    # Estos métodos estandarizan la llamada a tus nodos de dominio

    async def call_supervisor(state: AgentState):
        """Nodo Decisor: Analiza el plan y delega."""
        node = registry.get_node("supervisor")
        return await node(state)

    # 3. Registro de Nodos en el Grafo
    # Aquí es donde LangGraph 'instala' las piezas del sistema
    workflow.add_node("supervisor", call_supervisor)

    # 4. Punto de Entrada Único
    # Todo flujo comienza siempre por el Supervisor (Arquitecto)
    workflow.set_entry_point("supervisor")

    # Por ahora, el grafo está 'compilado' con sus piezas,
    # pero sin los caminos definidos.
    return workflow
