import os
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langchain_core.messages import SystemMessage

from src.agents.members.billing_agent import BillingAgent
from src.agents.members.general_info_agent import GeneralInfoAgent
from src.agents.members.supervisor_agent import SupervisorAgent
from src.agents.members.technical_agent import TechnicalAgent
from src.agents.types import Router, State, Supervisor
from src.app_config import app_config
from src.prompt_lib import ROUTER_PROMPT, SUPERVISOR_PROMPT


class CustomerSupportAgentCoordinator:
    def __init__(self):
        os.environ["OPENAI_API_KEY"] = app_config.OPENAI_API_KEY
        self.model_name = app_config.OPENAI_MODEL_NAME
        self.model = ChatOpenAI(model=self.model_name)
        self.RESPONSE_FORMAT = ChatPromptTemplate.from_template(
            """Response from {agent_name}:
            \n - {information}
            With above information please provide the final answer to the user.
            
            """
        )
        self.TEAM_MEMBERS = app_config.TEAM_MEMBERS
        self.router_agent = (
            ChatOpenAI(model=self.model_name, temperature=0.1, top_p=0.1)
            .bind(messages=[SystemMessage(content=ROUTER_PROMPT)])
            .with_structured_output(Router)
        )
        self.general_info_agent = GeneralInfoAgent().agent
        self.technical_agent = TechnicalAgent().agent
        self.billing_agent = BillingAgent().agent
        self.supervisor_agent = (
            ChatOpenAI(model=self.model_name, temperature=0.1, top_p=0.1)
            .bind(messages=[SystemMessage(content=SUPERVISOR_PROMPT)])
            .with_structured_output(Supervisor)
        )

    def _invoke_agent(
        self, agent, state: State, agent_name: str
    ) -> Command[Literal["supervisor_agent"]]:
        user_msg = state["messages"][-1].content
        result = agent.invoke({"messages": [{"role": "user", "content": user_msg}]})
        response = self.RESPONSE_FORMAT.format(
            agent_name=agent_name,
            information=result["messages"][-1].content,
        )
        return Command(
            update={"messages": [HumanMessage(content=response, name=agent_name)]},
            goto="supervisor_agent",
        )

    def general_info_node(self, state: State) -> Command[Literal["supervisor_agent"]]:
        return self._invoke_agent(self.general_info_agent, state, "general_info_agent")

    def technical_node(self, state: State) -> Command[Literal["supervisor_agent"]]:
        return self._invoke_agent(self.technical_agent, state, "technical_agent")

    def billing_node(self, state: State) -> Command[Literal["supervisor_agent"]]:
        response = self._invoke_agent(self.billing_agent, state, "billing_agent")
        print("Billing: ", response)
        return response

    def router_node(
        self, state: State
    ) -> Command[Literal[*app_config.TEAM_MEMBERS, "__end__"]]:
        messages = [("system", ROUTER_PROMPT)]
        for msg in state["messages"]:
            messages.append(("human", msg.content))
        response = self.router_agent.invoke(messages)
        next_step = response["next"]
        action = response["action"]
        information = response["information"]
        supervisor_message = f"Conduct the following action: {action} with this information: {information}"
        return Command(
            goto=next_step,
            update={
                "messages": [HumanMessage(content=supervisor_message, name="router")],
                "next": next_step,
            },
        )

    def _get_original_user_question(self, state: State) -> str:
        for msg in state["messages"]:
            if (
                isinstance(msg, HumanMessage)
                and msg.name != "router"
                and not hasattr(msg, "name")
                or msg.name is None
            ):
                return msg.content
        return state["messages"][-1].content if state["messages"] else ""

    def supervisor_node(
        self, state: State
    ) -> Command[Literal["final_response", "router"]]:
        agent_msg = state["messages"][-1].content
        original_question = self._get_original_user_question(state)
        messages = []
        messages.append(("human", original_question))
        messages.append(("ai", agent_msg))
        response = self.supervisor_agent.invoke(messages)
        print("--------------------------------")
        print(response)
        # import pdb; pdb.set_trace()
        if response["approval"] == "approved":
            return Command(
                update={
                    "messages": [
                        AIMessage(content=response["response"], name="supervisor")
                    ]
                },
                goto="final_response",
            )
        else:
            return Command(
                update={
                    "messages": [
                        AIMessage(
                            content="I'm sorry, I can't help with that. Please try again.",
                            name="supervisor",
                        )
                    ]
                },
                goto="final_response",
            )

    def final_response_node(self, state: State) -> Command[Literal["__end__"]]:
        final_msg = state["messages"][-1].content
        return Command(
            update={"messages": [AIMessage(content=final_msg, name="final_response")]},
            goto="__end__",
        )
