# src/infrastructure/orchestrator/langgraph_builder.py

from langgraph.graph import END, START, StateGraph

from domain.models.state import AgentState
from domain.orchestrator.nodes.agents_factory import WorkerNodeFactory
from domain.orchestrator.nodes.supervisor_node import SupervisorNode
from domain.orchestrator.registry import VALID_ROUTING_KEYS
from domain.ports.file_system import FileSystemPort
from domain.ports.graph_builder_port import GraphBuilderPort

# Adaptador de infraestructura (ejemplo local)
from infrastructure.adapters.storage.local_file_system import LocalFileSystemAdapter


class LangGraphBuilder(GraphBuilderPort):
    """
    Infrastructure implementation of GraphBuilderPort using LangGraph.
    """

    def __init__(self, fs: FileSystemPort | None = None) -> None:

        self.fs = LocalFileSystemAdapter()

    def build_fixing_graph(self, llm_provider):
        builder = StateGraph(AgentState)

        # Supervisor no necesita FS directamente
        builder.add_node("supervisor", SupervisorNode(llm_provider))

        # Factory ahora recibe también el FS
        worker_factory = WorkerNodeFactory(llm_provider, fs=self.fs)
        for agent_id in VALID_ROUTING_KEYS:
            builder.add_node(agent_id, worker_factory.create(agent_id))

        builder.add_edge(START, "supervisor")

        builder.add_conditional_edges(
            "supervisor",
            lambda state: state["active_agents"],
            {**{agent_id: agent_id for agent_id in VALID_ROUTING_KEYS}, "__end__": END},
        )

        for agent_id in VALID_ROUTING_KEYS:
            builder.add_edge(agent_id, "supervisor")

        return builder.compile()
