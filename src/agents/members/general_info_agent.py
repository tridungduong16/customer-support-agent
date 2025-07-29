import os

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from rich.console import Console
from rich.panel import Panel
from tavily import TavilyClient

from src.app_config import app_config


class GeneralInfoAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            top_p=0.1,
        )
        self.agent = create_react_agent(
            model=self.llm,
            tools=[
                self.get_visa_requirements,
                self.get_dining_recommendations,
                self.list_travel_apps_needed,
                self.get_cultural_tips,
                self.get_language_tips,
            ],
            name="knowledge_agent",
        )

        self.tavily = TavilyClient(api_key=app_config.TAVILY_API_KEY)