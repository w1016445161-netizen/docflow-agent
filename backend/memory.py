import json
from pathlib import Path

MEMORY_PATH = Path("storage/memory.json")


def load_memory() -> dict:
    """
    读取用户记忆。
    """
    if not MEMORY_PATH.exists():
        return {"user_profile": {}, "project_preferences": {}, "history": []}

    return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))


def save_memory(memory: dict) -> None:
    """
    保存用户记忆。
    """
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(
        json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update_memory(key: str, value: str) -> dict:
    """
    更新用户记忆。
    """
    memory = load_memory()

    memory["user_profile"][key] = value

    save_memory(memory)

    return memory


def add_history(event_type: str, content: str) -> dict:
    """
    添加历史事件。
    """
    memory = load_memory()

    memory["history"].append({"event_type": event_type, "content": content})

    save_memory(memory)

    return memory


def memory_to_text() -> str:
    """
    把记忆转成提示词文本。
    """
    memory = load_memory()

    lines = []
    lines.append("【用户记忆】")

    if memory["user_profile"]:
        lines.append("用户信息：")
        for key, value in memory["user_profile"].items():
            lines.append(f"- {key}: {value}")

    if memory["project_preferences"]:
        lines.append("项目偏好：")
        for key, value in memory["project_preferences"].items():
            lines.append(f"- {key}: {value}")

    if memory["history"]:
        lines.append("历史记录：")
        for item in memory["history"][-5:]:
            lines.append(f"- {item['event_type']}: {item['content']}")

    return "\n".join(lines)
