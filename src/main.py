import os
import shutil
import time

import requests
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from src.agents.builder import build_graph
from src.agents.nodes import CustomerSupportAgentCoordinator
from src.app_config import app_config
from src.schema import ChatRequest, UserQuestion, UserThread


async def process_question_stream(inputs, agent):
    async for s in agent.astream(inputs, stream_mode="values"):
        message = s["messages"][-1]
        yield {"content": message.content, "agent_name": getattr(message, "name", None)}


coordinator = CustomerSupportAgentCoordinator()
app = FastAPI()
graph = build_graph()


class ChatRequest(BaseModel):
    question: str


@app.get("/")
async def root():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    return {"message": "AI Agent platform is running v1!", "datetime": current_time}


@app.post("/chat")
async def chat(requets: ChatRequest):
    user_thread = UserThread(user_id="1", thread_id="1", agent_name="calculator")
    user_question = UserQuestion(user_thread=user_thread, question=requets.question)
    start_time = time.time()
    message = f"""
    {requests.question}
    """
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": message}],
        }
    )
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken: {time_taken} seconds")
    return {"message": result["messages"][-1].content, "time_taken": time_taken}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7888, reload=True)
