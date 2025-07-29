from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from src.prompt_lib import SUPERVISOR_PROMPT

class SupervisorAgent:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            top_p=0.1,
        )
        self.agent = create_react_agent(
            model=self.model,
            tools=[],
            name="supervisor_agent",
            prompt=SUPERVISOR_PROMPT,
        )
