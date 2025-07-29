from typing import Literal

from langgraph.graph import MessagesState
from typing_extensions import TypedDict

from src.app_config import app_config

OPTIONS = app_config.TEAM_MEMBERS + ["FINISH"]


class Router(TypedDict):
    next: Literal[*OPTIONS]
    action: str
    information: str

class Supervisor(TypedDict):
    approval: Literal["approved", "rejected"]
    response: str

class State(MessagesState):
    next: str
    full_plan: str
