import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.app_config import app_config
from src.prompt_lib import GENERAL_INFO_PROMPT


class GeneralInfoAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            top_p=0.1,
        )
        self.agent = create_react_agent(
            model=self.llm,
            tools=[],
            name="general_info_agent",
            prompt=GENERAL_INFO_PROMPT,
        )
