from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.agents.travel_agent.tools.accomodation import AccomodationTool
from src.agents.travel_agent.tools.flights import FlightTool


class BillingAgent:
    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.agent = create_react_agent(
            model=self.model,
            tools=[],
            name="budget_agent",
        )
