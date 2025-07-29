from langgraph.graph import END, START, StateGraph

from src.agents.nodes import (
    CustomerSupportAgentCoordinator,
)  # Your coordinator class
from src.agents.types import State


async def build_graph():
    coordinator = CustomerSupportAgentCoordinator()
    await coordinator.async_init()
    builder = StateGraph(State)
    builder.add_edge(START, "router")
    builder.add_node("router", coordinator.router_node)
    builder.add_node("general_info_agent", coordinator.general_info_node)
    builder.add_node("technical_agent", coordinator.technical_node)
    builder.add_node("billing_agent", coordinator.billing_node)
    builder.add_node("supervisor_agent", coordinator.supervisor_node)
    builder.add_node("final_response", coordinator.final_response_node)
    return builder.compile()
