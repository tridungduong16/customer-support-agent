import asyncio
import json
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from markdown import markdown
from src.agents.builder import build_graph


async def process_question_stream(inputs, agent):
    async for s in agent.astream(inputs, stream_mode="values"):
        message = s["messages"][-1]
        yield {"content": message.content, "agent_name": getattr(message, "name", None)}


async def main():
    graph = await build_graph()
    while True:
        user_question = f"""
        I was overcharged on my last bill.
        """
        inputs = {
            "messages": [{"role": "user", "content": user_question}],
        }
        messages = []
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
        break


if __name__ == "__main__":
    asyncio.run(main())
