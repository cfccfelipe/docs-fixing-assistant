from langgraph.graph import StateGraph, END
from domain.models.state_model import AgentState
from domain.orchestrator.agent_registry import AgentRegistry
from domain.models.enums import StopReason
import logging

logger = logging.getLogger(__name__)

def create_workflow(registry: AgentRegistry):
    workflow = StateGraph(AgentState)

    # Wrap nodes with error handling and state persistence
    async def run_node(state: AgentState, node_id: str):
        logger.info(f"🔄 Executing Node: {node_id} for file: {state.current_file}")
        node = registry.get_node(node_id)
        result = await node(state)
        # Result is a StateUpdate, merge into state
        state.update(result)
        return state

    # Register Nodes
    async def planner_node(state):
        return await run_node(state, "planner_agent")
    
    async def supervisor_node(state):
        return await run_node(state, "supervisor")

    workflow.add_node("planner_agent", planner_node)
    workflow.add_node("supervisor", supervisor_node)
    
    for agent_id in registry._nodes:
        if agent_id not in ["supervisor", "planner_agent"]:
            async def specialist_node(state, nid=agent_id):
                return await run_node(state, nid)
            workflow.add_node(agent_id, specialist_node)

    # Edges
    workflow.set_entry_point("planner_agent")
    workflow.add_edge("planner_agent", "supervisor")

    def route_supervisor(state: AgentState):
        if state.stop_reason == StopReason.END:
            return END
        if state.next_agent and registry.has_node(state.next_agent):
            return state.next_agent
        return END

    # Incluimos planner_agent en el mapeo para permitir re-planificación si es necesario
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {agent_id: agent_id for agent_id in registry._nodes if agent_id != "supervisor"} | {END: END}
    )

    for agent_id in registry._nodes:
        if agent_id not in ["supervisor", "planner_agent"]:
            workflow.add_edge(agent_id, "supervisor")

    return workflow.compile()
