import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


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
如果文档片段中没有答案，请明确说“根据当前文档内容无法确定”。

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


def mock_answer(question: str, contexts: list[dict]) -> str:
    """
    没有 API Key 时使用，用于测试完整流程。
    """
    if not contexts:
        return "没有检索到相关文档片段，暂时无法回答。"

    context_preview = "\n\n".join(
        [
            f"片段 {item['chunk_id']}，相关度分数 {item.get('score', 0)}：\n{item['text'][:260]}..."
            for item in contexts
        ]
    )

    return f"""【Mock 模式回答】

你问的问题是：

{question}

系统已经检索到以下相关片段：

{context_preview}

说明：
当前 LLM_MODE=mock，所以这里还没有真正调用大模型。
这一步主要用于验证：上传、解析、切分、检索、返回结果、保存报告这些流程是否能跑通。

等你后面配置真实 API Key，并把 .env 里的 LLM_MODE 改成 openai 后，系统就会生成正式回答。
"""


def ask_llm(question: str, contexts: list[dict]) -> str:
    mode = os.getenv("LLM_MODE", "mock")

    if mode == "mock":
        return mock_answer(question, contexts)

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
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
