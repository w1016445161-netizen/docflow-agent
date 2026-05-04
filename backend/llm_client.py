import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

_ROOT_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = _ROOT_DIR / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


def _get_client_and_model():
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if not provider:
        raise ValueError(
            "缺少 LLM_PROVIDER，请在项目根目录 .env 中设置 LLM_PROVIDER=aliyun"
        )

    base_url = os.getenv("LLM_BASE_URL", "").strip()
    if not base_url:
        raise ValueError(
            "缺少 LLM_BASE_URL，请在项目根目录 .env 中设置 LLM_BASE_URL"
        )

    model = os.getenv("LLM_MODEL", "").strip()
    if not model:
        raise ValueError(
            "缺少 LLM_MODEL，请在项目根目录 .env 中设置 LLM_MODEL"
        )

    api_key = ""
    if provider == "aliyun":
        api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "LLM_PROVIDER=aliyun 但缺少 DASHSCOPE_API_KEY，请在项目根目录 .env 中设置"
            )
    else:
        raise ValueError(f"不支持的 LLM_PROVIDER：{provider}")

    return OpenAI(api_key=api_key, base_url=base_url), model


def build_prompt(question: str, contexts: list[dict]) -> str:
    context_text = "\n\n".join(
        [
            f"[片段 {item['chunk_id']}]\n{item['text']}"
            for item in contexts
        ]
    )

    prompt = f"""
你是 DocFlow-Agent，一个严谨的文档处理智能体。

请你严格根据下面提供的文档片段回答问题。
如果文档片段中没有答案，请明确说"根据当前文档内容无法确定"。

【文档片段】
{context_text}

【用户问题】
{question}

【回答要求】
1. 先直接回答问题
2. 再列出依据
3. 不要编造文档中没有的信息
"""
    return prompt.strip()


def ask_llm(question: str, contexts: list[dict]) -> str:
    client, model = _get_client_and_model()
    prompt = build_prompt(question, contexts)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨的文档问答助手，只能基于用户提供的文档内容回答。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


def summarize_text(filename: str, text: str, max_tokens: int = 800) -> str:
    client, model = _get_client_and_model()

    prompt = f"""请对文档「{filename}」生成结构化摘要。
所有内容必须严格基于以下文档，不要引入文档中未出现的信息。

请按照以下格式输出：

## 一、文档主要内容

用 3 到 5 句话概括文档核心内容。

## 二、关键信息提取

提取文档中的重要人物、时间、地点、概念、数据、结论或任务。

## 三、结构化要点

用有序列表总结文档中的主要段落或逻辑结构。

## 四、可能的后续问题

提出 3 个与本文内容直接相关的后续问题，不要发散到文档未涉及的领域。

以下是文档内容：

{text}"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨的文档摘要助手。严格基于文档内容生成摘要，不添加文档中不存在的信息。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content


def summarize_text_stream(filename: str, text: str, max_tokens: int = 800):
    client, model = _get_client_and_model()

    prompt = f"""请对文档「{filename}」生成结构化摘要。
所有内容必须严格基于以下文档，不要引入文档中未出现的信息。

请按照以下格式输出：

## 一、文档主要内容

用 3 到 5 句话概括文档核心内容。

## 二、关键信息提取

提取文档中的重要人物、时间、地点、概念、数据、结论或任务。

## 三、结构化要点

用有序列表总结文档中的主要段落或逻辑结构。

## 四、可能的后续问题

提出 3 个与本文内容直接相关的后续问题，不要发散到文档未涉及的领域。

以下是文档内容：

{text}"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨的文档摘要助手。严格基于文档内容生成摘要，不添加文档中不存在的信息。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=max_tokens,
        stream=True
    )

    for chunk in response:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta
