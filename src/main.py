import time
import uvicorn
from fastapi import FastAPI
from src.schema import ChatRequest, UserQuestion, UserThread, ChatRequest
from src.agents.run import AgentManager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to ["http://localhost:3000"] etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
call_agent = AgentManager()


@app.get("/")
async def root():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    return {"message": "AI Agent platform is running v1!", "datetime": current_time}


@app.post("/chat")
async def chat(requets: ChatRequest):
    start_time = time.time()
    user_thread = UserThread(user_id="111", thread_id="111")
    user_question = UserQuestion(user_thread=user_thread, question=requets.question)
    res = call_agent.process_question_stream(user_question, call_agent.graph)
    end_time = time.time()
    time_taken = end_time - start_time
    return {"message": res, "time_taken": time_taken}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7888, reload=True)
