import os
import shutil
import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from src.app_config import app_config
from src.agents.builder import build_graph
from src.agents.nodes import CustomerSupportAgentCoordinator
from src.schema import UserThread, UserQuestion, ChatRequest

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
    user_thread = UserThread(
        user_id="1", thread_id="1", agent_name="calculator"
    )
    user_question = UserQuestion(
        user_thread=user_thread, question=requets.question
    )
    start_time = time.time()
    async for result in process_question_stream(inputs, graph):
        with open("result.txt", "a") as f:
            if not result["agent_name"]:
                result["agent_name"] = ""
            str_result = (
                "Agent: "
                + str(result["agent_name"])
                + "\n"
                + result["content"]
                + "\n\n"
            )
            f.write(str_result)
            f.write("\n\n")
        print(result["content"])
        messages.append(result)

    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken: {time_taken} seconds")
    return {"message": res, "time_taken": time_taken}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7888, reload=True)
