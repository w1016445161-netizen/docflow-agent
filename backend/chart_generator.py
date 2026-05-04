from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def setup_chinese_font():
    """
    设置 matplotlib 中文字体。
    Windows 优先使用 Microsoft YaHei 或 SimHei。
    """
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def safe_filename(text: str) -> str:
    """
    避免文件名里出现特殊字符。
    """
    text = str(text)
    for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        text = text.replace(ch, "_")
    return text


def add_value_labels(ax):
    """
    给柱状图顶部添加数值标签。
    """
    for bar in ax.patches:
        height = bar.get_height()
        ax.annotate(
            f"{height:.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )


def generate_bar_chart(
    df: pd.DataFrame,
    sheet_name: str,
    x_col: str,
    y_col: str,
    doc_id: str,
    output_dir: Path,
) -> str:
    """
    生成柱状图：文本列作为横轴，数值列作为纵轴。
    """
    chart_df = df[[x_col, y_col]].dropna().head(20)

    if chart_df.empty:
        return ""

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(chart_df[x_col].astype(str), chart_df[y_col])

    ax.set_title(f"{sheet_name}：{x_col} 与 {y_col} 对比", fontsize=16)
    ax.set_xlabel(str(x_col), fontsize=12)
    ax.set_ylabel(str(y_col), fontsize=12)

    ax.tick_params(axis="x", rotation=35)

    add_value_labels(ax)

    max_value = chart_df[y_col].max()
    ax.set_ylim(0, max_value * 1.15)

    plt.tight_layout()

    safe_sheet = safe_filename(sheet_name)
    safe_x = safe_filename(x_col)
    safe_y = safe_filename(y_col)

    chart_path = output_dir / f"{doc_id}_{safe_sheet}_{safe_x}_vs_{safe_y}.png"

    plt.savefig(chart_path, dpi=150)
    plt.close(fig)

    return str(chart_path)


def generate_line_chart(
    df: pd.DataFrame, sheet_name: str, y_col: str, doc_id: str, output_dir: Path
) -> str:
    """
    如果没有文本列，就用行号作为横轴生成折线图。
    """
    chart_df = df[[y_col]].dropna().head(20)

    if chart_df.empty:
        return ""

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(chart_df.index, chart_df[y_col], marker="o")

    ax.set_title(f"{sheet_name}：{y_col} 趋势图", fontsize=16)
    ax.set_xlabel("序号", fontsize=12)
    ax.set_ylabel(str(y_col), fontsize=12)

    for x, y in zip(chart_df.index, chart_df[y_col]):
        ax.annotate(
            f"{y:.0f}",
            xy=(x, y),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontsize=10,
        )

    plt.tight_layout()

    safe_sheet = safe_filename(sheet_name)
    safe_y = safe_filename(y_col)

    chart_path = output_dir / f"{doc_id}_{safe_sheet}_{safe_y}_line.png"

    plt.savefig(chart_path, dpi=150)
    plt.close(fig)

    return str(chart_path)


def generate_excel_charts(file_path: str, doc_id: str) -> list[str]:
    """
    根据 Excel 文件自动生成图表。

    当前策略：
    1. 每个 sheet 最多处理前 3 个数值列
    2. 如果有文本列，用第一个文本列作为横轴
    3. 如果没有文本列，就用行号作为横轴
    4. 每张图都显示中文标题、坐标轴和数值标签
    """
    setup_chinese_font()

    output_dir = Path("storage/outputs/charts")
    output_dir.mkdir(parents=True, exist_ok=True)

    sheets = pd.read_excel(file_path, sheet_name=None)

    chart_paths = []

    for sheet_name, df in sheets.items():
        if df.empty:
            continue

        numeric_columns = df.select_dtypes(include="number").columns.tolist()
        text_columns = df.select_dtypes(exclude="number").columns.tolist()

        if not numeric_columns:
            continue

        # 每个工作表最多生成 3 张图，避免图太多
        numeric_columns = numeric_columns[:3]

        if text_columns:
            x_col = text_columns[0]

            for y_col in numeric_columns:
                chart_path = generate_bar_chart(
                    df=df,
                    sheet_name=sheet_name,
                    x_col=x_col,
                    y_col=y_col,
                    doc_id=doc_id,
                    output_dir=output_dir,
                )

                if chart_path:
                    chart_paths.append(chart_path)

        else:
            for y_col in numeric_columns:
                chart_path = generate_line_chart(
                    df=df,
                    sheet_name=sheet_name,
                    y_col=y_col,
                    doc_id=doc_id,
                    output_dir=output_dir,
                )

                if chart_path:
                    chart_paths.append(chart_path)

    return chart_paths
