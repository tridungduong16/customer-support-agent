import base64
import mimetypes
import os

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.app_config import app_config


class ImageProcessingAgent:
    def __init__(self):
        os.environ["OPENAI_API_KEY"] = app_config.OPENAI_API_KEY or "none"
        self.llm = None

    def load_model(self):
        self.llm = ChatOpenAI(
            model=app_config.OPENAI_MODEL_NAME,
            temperature=0,
            api_key=app_config.OPENAI_API_KEY,
        )

    def local_file_to_data_url(self, file_path: str) -> str:
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    def describe_image(self, image_url: str) -> str:
        if self.llm is None:
            self.load_model()
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Please provide a brief description of the image.",
                },
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        )
        response = self.llm.invoke([message])
        ans = response.content
        return ans
