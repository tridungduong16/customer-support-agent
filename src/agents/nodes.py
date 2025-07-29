import os
from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.types import Command

from src.app_config import app_config
from src.agents.types import Router, State
from src.agents.members.billing_agent import BillingAgent
from src.agents.members.general_info_agent import GeneralInfoAgent
from src.agents.members.technical_agent import TechnicalAgent
from src.agents.members.supervisor_agent import SupervisorAgent
from src.prompt_lib import ROUTER_PROMPT
from langchain_core.messages import AIMessage


class CustomerSupportAgentCoordinator:
    def __init__(self):
        os.environ["OPENAI_API_KEY"] = app_config.OPENAI_API_KEY
        self.model_name = app_config.OPENAI_MODEL_NAME
        self.model = ChatOpenAI(model=self.model_name)
        self.RESPONSE_FORMAT = ChatPromptTemplate.from_template(
            "Response from {agent_name} with information {information}\n\nPlease execute the next step.*"
        )
        self.TEAM_MEMBERS = app_config.TEAM_MEMBERS
        self.router_agent = ChatOpenAI(
            model=self.model_name, temperature=0.1, top_p=0.1
        ).with_structured_output(Router)

    async def async_init(self):
        self.general_info_agent = GeneralInfoAgent().agent
        self.technical_agent = TechnicalAgent().agent
        self.billing_agent = BillingAgent().agent
        self.supervisor_agent = SupervisorAgent().agent

    def _invoke_agent(
        self, agent, state: State, agent_name: str
    ) -> Command[Literal["router"]]:
        user_msg = state["messages"][-1].content
        result = agent.invoke({"messages": [{"role": "user", "content": user_msg}]})
        response = self.RESPONSE_FORMAT.format(
            agent_name=agent_name,
            information=result["messages"][-1].content,
        )
        return Command(
            update={"messages": [HumanMessage(content=response, name=agent_name)]},
            goto="router",
        )

    def general_info_node(self, state: State) -> Command[Literal["router"]]:
        return self._invoke_agent(self.general_info_agent, state, "general_info_agent")

    def technical_node(self, state: State) -> Command[Literal["router"]]:
        return self._invoke_agent(self.technical_agent, state, "technical_agent")

    def billing_node(self, state: State) -> Command[Literal["router"]]:
        import pdb

        pdb.set_trace()
        return self._invoke_agent(self.billing_agent, state, "billing_agent")

    def router_node(
        self, state: State
    ) -> Command[Literal[*app_config.TEAM_MEMBERS, "__end__"]]:
        messages = [("system", ROUTER_PROMPT)]
        messages.append(("human", state["messages"][0].content))
        for msg in state["messages"]:
            if msg.name in self.TEAM_MEMBERS:
                messages.append(("human", msg.content))
        response = self.router_agent.invoke(messages)
        next_step = response["next"]
        if next_step == "FINISH":
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
        action = response["action"]
        information = response["information"]
        supervisor_message = f"Conduct the following action: {action} with this information: {information}"
        return Command(
            goto=next_step,
            update={
                "messages": [
                    HumanMessage(content=supervisor_message, name="supervisor")
                ],
                "next": next_step,
            },
        )

    def supervisor_node(
        self, state: State
    ) -> Command[Literal["final_response", "router"]]:
        agent_msg = state["messages"][-1].content
        supervisor_review = self.supervisor_agent.invoke(
            {"messages": [{"role": "user", "content": agent_msg}]}
        )
        approval_decision = supervisor_review["messages"][-1].content.strip().lower()
        if "approved" in approval_decision:
            return Command(
                update={"messages": [AIMessage(content=agent_msg, name="supervisor")]},
                goto="final_response",
            )
        else:
            return Command(
                update={
                    "messages": [
                        AIMessage(
                            content="Supervisor rejected the response. Please re-route.",
                            name="supervisor",
                        )
                    ]
                },
                goto="router",
            )

    def final_response_node(self, state: State) -> Command[Literal["__end__"]]:
        final_msg = state["messages"][-1].content
        return Command(
            update={"messages": [AIMessage(content=final_msg, name="final_response")]},
            goto="__end__",
        )
