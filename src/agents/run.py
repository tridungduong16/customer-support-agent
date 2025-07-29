import asyncio
import json
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from markdown import markdown
from rich.console import Console
from rich.panel import Panel
from weasyprint import HTML
from src.agents.travel_agent.builder import build_graph

console = Console()

def save_markdown_as_pdf(markdown_text: str, output_path: str = "output.pdf") -> None:
    html = markdown(markdown_text, extensions=["extra", "smarty"])
    HTML(string=html).write_pdf(output_path)
    print(f"✅ PDF saved to {output_path}")


async def process_question_stream(inputs, agent):
    async for s in agent.astream(inputs, stream_mode="values"):
        message = s["messages"][-1]
        yield {"content": message.content, "agent_name": getattr(message, "name", None)}


async def main():
    graph = await build_graph()
    while True:
        user_question = f"""
        Estimate buget for travel from Ho Chi Minh City to Sydney from June 10, 2025 to June 15, 2025.
        AND visa requirement for Vietnamese people to travel to Australia.
        No need other information.

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
            messages.append(result)
        break

if __name__ == "__main__":
    asyncio.run(main())
