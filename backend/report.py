from datetime import datetime
from pathlib import Path


def save_markdown_report(doc_id: str, question: str, answer: str) -> str:
    output_dir = Path("storage/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = output_dir / f"{doc_id}_report.md"

    content = f"""# DocFlow-Agent 文档问答报告

生成时间：{now}

## 用户问题

{question}

## 系统回答

{answer}
"""

    report_path.write_text(content, encoding="utf-8")

    return str(report_path)
