from typing import Protocol, runtime_checkable

from domain.models.state_model import AgentState, StateUpdate


@runtime_checkable
class NodePort(Protocol):
    """
    Structural protocol for Graph Nodes.
    Defines the contract for any component (Worker, Supervisor, Tool)
    that processes AgentState and returns a partial state delta.
    """

    name: str
    model: str

    async def __call__(self, state: AgentState) -> StateUpdate:
        """
        Execute the node logic.

        Args:
            state: The current global AgentState dataclass.

        Returns:
            StateUpdate: A TypedDict delta to be merged into the global state.
        """
        ...
