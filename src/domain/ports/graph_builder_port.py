# src/domain/orchestrator/ports/graph_builder_port.py
from typing import Protocol, runtime_checkable


@runtime_checkable
class GraphBuilderPort(Protocol):
    """
    Abstraction for building and compiling agent orchestration graphs.
    Keeps domain independent of specific frameworks (LangGraph, Strands, etc.).
    """

    def build_fixing_graph(self, llm_provider) -> object:
        """
        Build and compile a graph that orchestrates Supervisor + Workers.
        Returns a compiled graph object (type left abstract).
        """
        pass
