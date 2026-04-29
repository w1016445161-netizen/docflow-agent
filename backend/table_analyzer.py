from pathlib import Path
import pandas as pd


def load_excel(file_path: str) -> dict:
    """
    读取 Excel 文件，返回所有 sheet 的 DataFrame。
    """
    path = Path(file_path)

    if path.suffix.lower() not in [".xlsx", ".xls"]:
        raise ValueError("只支持 .xlsx 或 .xls 表格文件")

    sheets = pd.read_excel(file_path, sheet_name=None)

    return sheets


def summarize_dataframe(df: pd.DataFrame, sheet_name: str) -> dict:
    """
    对单个工作表做基础分析。
    """
    rows, cols = df.shape

    columns = list(df.columns)

    missing_values = df.isna().sum().to_dict()

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    text_columns = df.select_dtypes(exclude="number").columns.tolist()

    numeric_summary = {}

    if numeric_columns:
        desc = df[numeric_columns].describe().round(3)
        numeric_summary = desc.to_dict()

    preview = df.head(10).fillna("").to_dict(orient="records")

    return {
        "sheet_name": sheet_name,
        "rows": rows,
        "columns_count": cols,
        "columns": columns,
        "numeric_columns": numeric_columns,
        "text_columns": text_columns,
        "missing_values": missing_values,
        "numeric_summary": numeric_summary,
        "preview": preview
    }


def analyze_excel(file_path: str) -> dict:
    """
    分析整个 Excel 文件。
    """
    sheets = load_excel(file_path)

    result = {
        "file_path": file_path,
        "sheet_count": len(sheets),
        "sheets": []
    }

    for sheet_name, df in sheets.items():
        summary = summarize_dataframe(df, sheet_name)
        result["sheets"].append(summary)

    return result


def excel_analysis_to_text(analysis: dict) -> str:
    """
    把 Excel 分析结果转成文本，方便交给文档问答系统和大模型。
    """
    lines = []

    lines.append("【Excel 表格分析结果】")
    lines.append(f"文件路径：{analysis['file_path']}")
    lines.append(f"工作表数量：{analysis['sheet_count']}")

    for sheet in analysis["sheets"]:
        lines.append("")
        lines.append(f"工作表名称：{sheet['sheet_name']}")
        lines.append(f"行数：{sheet['rows']}")
        lines.append(f"列数：{sheet['columns_count']}")
        lines.append(f"字段列表：{', '.join(map(str, sheet['columns']))}")

        if sheet["numeric_columns"]:
            lines.append(f"数值型字段：{', '.join(map(str, sheet['numeric_columns']))}")
        else:
            lines.append("数值型字段：无")

        if sheet["text_columns"]:
            lines.append(f"文本型字段：{', '.join(map(str, sheet['text_columns']))}")
        else:
            lines.append("文本型字段：无")

        lines.append("缺失值统计：")
        for col, count in sheet["missing_values"].items():
            lines.append(f"- {col}: {count}")

        lines.append("前 10 行预览：")
        for row in sheet["preview"]:
            lines.append(str(row))

    return "\n".join(lines)