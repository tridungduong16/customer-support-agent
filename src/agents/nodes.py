import json
import os
from typing import Any, Dict, List, Literal, Optional
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from src.app_config import app_config
from src.agents.types import Router, State
from src.agents.members.billing_agent import BillingAgent
from src.agents.members.general_info_agent import GeneralInfoAgent
from src.agents.members.technical_agent import TechnicalAgent
from src.agents.members.supervisor_agent import SupervisorAgent

class CustomerSupportAgentCoordinator:
    def __init__(self, mcp_config_path=None):
        os.environ["OPENAI_API_KEY"] = app_config.OPENAI_API_KEY
        self.model_name = app_config.MODEL_NAME
        self.model = ChatOpenAI(model=self.model_name)
        self.RESPONSE_FORMAT = ChatPromptTemplate.from_template(
            "Response from {agent_name} with information {information}\n\nPlease execute the next step.*"
        )
        self.TEAM_MEMBERS = app_config.TEAM_MEMBERS
        self.supervisor_agent = ChatOpenAI(
            model=self.model_name, temperature=0.1, top_p=0.1
        ).with_structured_output(Router)

    async def async_init(self):
        self.general_info_agent = GeneralInfoAgent(self.model).agent
        self.technical_agent = TechnicalAgent(self.model).agent
        self.billing_agent = BillingAgent(self.model).agent
        self.supervisor_agent = SupervisorAgent(self.model).agent

    def _invoke_agent(
        self, agent, state: State, agent_name: str, color: str
    ) -> Command[Literal["router"]]:
        messages = {
            "messages": [{"role": "user", "content": state["messages"][-1].content}]
        }
        result = agent.invoke(messages)
        response = self.RESPONSE_FORMAT.format(
            agent_name=agent_name, information=result["messages"][-1].content
        )
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=response,
                        name=agent_name,
                    )
                ]
            },
            goto="router",
        )

    def general_info_node(self, state: State) -> Command[Literal["router"]]:
        return self._invoke_agent(self.general_info_agent, state, "general_info_agent", "blue")

    def technical_node(self, state: State) -> Command[Literal["router"]]:
        return self._invoke_agent(
            self.itinerary_agent, state, "itinerary_agent", "green"
        )

    def knowledge_node(self, state: State) -> Command[Literal["router"]]:
        return self._invoke_agent(
            self.knowledge_agent, state, "knowledge_agent", "yellow"
        )

    def supervisor_node(self, state: State) -> Command[Literal["supervisor"]]:
        return self._invoke_agent(self.supervisor_agent, state, "supervisor_agent", "magenta")

    def router_node(self, state: State) -> Command[
        Literal[
            *app_config.TEAM_MEMBERS,
            "__end__",
        ]
    ]:
        print("Supervisor evaluating next action")
        messages = [("system", ROUTER_PROMPT)]
        messages.append(("human", state["messages"][0].content))
        for msg in state["messages"]:
            if msg.name in self.TEAM_MEMBERS:
                messages.append(("human", msg.content))
        response = self.router_agent.invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            final_content = response["final_output"]
            return Command(
                goto="__end__",
                update={
                    "messages": [
                        HumanMessage(content=final_content, name="supervisor")
                    ],
                    "next": "__end__",
                },
            )
        else:
            goto = response["next"]
            action = response["action"]
            information = response["information"]
            supervisor_message = (
                "Conduct the following action: "
                + action
                + "with this information: "
                + information
            )
            return Command(
                goto=goto,
                update={
                    "messages": [
                        HumanMessage(content=supervisor_message, name="supervisor")
                    ],
                    "next": goto,
                },
            )
