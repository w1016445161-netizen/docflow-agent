import os
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL")

        if not self.api_key:
            raise ValueError("没有读取到 DASHSCOPE_API_KEY，请检查 .env 文件。")

        if not self.base_url:
            raise ValueError("没有读取到 LLM_BASE_URL，请检查 .env 文件。")

        if not self.model:
            raise ValueError("没有读取到 LLM_MODEL，请检查 .env 文件。")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def chat(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        if system_prompt is None:
            system_prompt = "你是一个文档处理智能体，回答要准确、清晰、结构化。"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=temperature,
            extra_body={"enable_thinking": False},
        )

        content = response.choices[0].message.content

        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return {
            "model": self.model,
            "content": content,
            "usage": usage,
        }


llm_service = LLMService()
