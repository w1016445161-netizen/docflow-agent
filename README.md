# DocFlow Agent

DocFlow Agent 是一个基于 **FastAPI + Vue 3 + 阿里云百炼 qwen 模型** 构建的 AI 文档处理智能体项目。项目面向学习资料、课程论文、实验报告和项目文档等场景，支持文档上传解析、结构化摘要生成、文档问答、多文档对比等功能。

---

## 当前已实现功能

### 1. 文档上传与结构化摘要

用户上传 TXT / PDF 文档，后端自动解析文本内容，调用大模型生成结构化摘要。摘要包含：文档主要内容、关键信息提取、结构化要点、可能的后续问题。

已实现链路：

```text
上传 TXT / PDF 文档
↓
backend/document_parser.py 解析文本
↓
backend/llm_client.py :: summarize_text() 构造摘要 prompt
↓
调用阿里云百炼 qwen 模型
↓
返回结构化摘要
```

### 2. 文档问答

用户上传文档后，可以对文档内容进行提问。后端将文档切分成片段，通过关键词匹配检索相关片段，构造提示词后调用大模型生成回答。

```text
用户提问
↓
backend/retriever.py 检索相关片段
↓
backend/llm_client.py :: ask_llm() 构造 QA prompt
↓
调用阿里云百炼 qwen 模型
↓
返回回答
```

### 3. 多文档对比

同时对比多个文档，分析共同点和差异。

### 4. Excel 分析与图表生成

上传 Excel 文件后自动分析表格结构、统计数值字段，并生成柱状图 / 折线图。

### 5. OCR 扫描型 PDF 支持

上传扫描型 PDF 时，如果普通文本提取结果过少，自动回退到 OCR 识别。需要本地安装 Tesseract-OCR，并在 `.env` 中启用配置。

---

## 技术栈

### 后端

| 模块 | 职责 |
|---|---|
| `backend/main.py` | 后端主入口，路由注册 |
| `backend/document_parser.py` | TXT/PDF/DOCX/Excel 文档解析 |
| `backend/ocr_parser.py` | Tesseract OCR 识别 |
| `backend/llm_client.py` | LLM 调用封装（ask_llm / summarize_text） |
| `backend/chunker.py` | 长文本切分 |
| `backend/retriever.py` | 关键词匹配检索 |
| `backend/memory.py` | 用户记忆与历史记录 |
| `backend/report.py` | Markdown 报告保存 |
| `backend/table_analyzer.py` | Excel 表格分析 |
| `backend/chart_generator.py` | Excel 图表生成 |
| `backend/multi_doc.py` | 多文档上下文构建 |

### 前端

- Vue 3 + Vite
- JavaScript
- markdown-it（Markdown 渲染）
- Fetch API

### 模型服务

- 阿里云百炼（OpenAI-compatible API）
- qwen3.6-plus / qwen3.6-flash

---

## 后端启动方式

在项目根目录执行：

```powershell
cd D:\projects\docflow_agent
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

API 文档地址：http://127.0.0.1:8000/docs

---

## 环境变量配置

在项目根目录创建 `.env` 文件：

```env
LLM_PROVIDER=aliyun
DASHSCOPE_API_KEY=你的阿里云百炼API_KEY
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.6-plus
```

`backend/.env` 中包含 OCR 相关配置（可选）：

```env
OCR_ENABLED=true
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_LANG=chi_sim+eng
OCR_DPI=200
OCR_MAX_PAGES=20
OCR_MIN_TEXT_LENGTH=80
```

---

## 前端启动方式

```powershell
cd D:\projects\docflow_agent\frontend
npm install
npm run dev
```

前端访问地址：http://localhost:5173

---

## API 接口说明

### 1. 文档上传摘要

```text
POST /api/documents/summarize
```

请求类型：`multipart/form-data`
参数：`file`（TXT 或 PDF 文件）

返回示例（200）：

```json
{
  "filename": "example.pdf",
  "file_type": "pdf",
  "char_count": 6763,
  "is_truncated": false,
  "preview": "提取出的前 500 字文本",
  "summary": "结构化摘要内容（Markdown 格式）",
  "model": "docflow-agent",
  "usage": null
}
```

说明：
- 当前仅支持 `.txt` 和 `.pdf` 格式
- `is_truncated` 表示文档是否超过 12000 字符限制
- `usage` 当前为 `null`，token 消耗数据将在后续版本补充
- 摘要 prompt 使用 `summarize_text()`，严格基于文档内容生成

### 2. 文档问答

```text
POST /ask
```

请求参数（JSON）：

```json
{
  "doc_id": "文档ID",
  "question": "文档的主要内容是什么？"
}
```

说明：
- 需要先通过 `/upload` 上传文档获取 `doc_id`
- 系统自动检索文档中的相关片段后生成回答

### 3. 文档上传（通用）

```text
POST /upload
```

请求类型：`multipart/form-data`
参数：`file`

支持格式：`.txt`、`.pdf`、`.docx`、`.md`、`.xlsx`、`.xls`

上传后自动解析文档文本，切分为片段并建立索引。如果是 Excel 文件还会自动分析表格结构和生成图表。

### 4. 多文档对比

```text
POST /compare
```

请求参数（JSON）：

```json
{
  "doc_ids": ["doc_id_1", "doc_id_2"],
  "question": "请比较这些文档的主要内容、共同点和差异点。"
}
```

### 5. 其他接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 根路径 |
| GET | `/health` | 健康检查 |
| GET | `/api/health` | 健康检查 |
| GET | `/documents` | 已上传文档列表 |
| GET | `/documents/{doc_id}` | 单个文档信息 |
| POST | `/excel/analyze` | Excel 单独分析 |
| GET | `/memory` | 查看用户记忆 |
| POST | `/memory` | 更新用户记忆 |
| GET | `/ocr/status` | OCR 环境检查 |

### 6. 聊天接口（历史遗留，未启用）

```text
POST /api/chat
```

说明：该接口定义在 `backend/routers/chat.py` 中，但目前**未注册到主应用**，访问将返回 404。如需启用，需要在 `main.py` 中添加 `app.include_router()`。

---

## OCR 说明

项目通过 `Tesseract-OCR` 支持扫描型 PDF 的自动识别。

- 当普通 PDF 文本提取结果少于 80 字符时，自动启用 OCR fallback
- 需要本地安装 Tesseract-OCR（Windows / Linux / macOS）
- 在 `backend/.env` 中配置 `TESSERACT_CMD` 指向 Tesseract 可执行文件路径
- 可通过 `GET /ocr/status` 接口检查 OCR 环境是否就绪

---

## 项目结构

```text
docflow_agent/
├── backend/
│   ├── main.py                  # FastAPI 主应用，路由注册
│   ├── document_parser.py       # 文档解析（TXT/PDF/DOCX/Excel）
│   ├── ocr_parser.py            # Tesseract OCR 识别
│   ├── llm_client.py            # LLM 调用（ask_llm / summarize_text）
│   ├── chunker.py               # 长文本切分
│   ├── retriever.py             # 关键词检索
│   ├── memory.py                # 用户记忆
│   ├── report.py                # Markdown 报告保存
│   ├── table_analyzer.py        # Excel 表格分析
│   ├── chart_generator.py       # Excel 图表生成
│   ├── multi_doc.py             # 多文档对比上下文
│   ├── .env                     # OCR 配置
│   │
│   ├── routers/                 # ⚠️ 历史遗留，当前未注册
│   │   ├── chat.py              #     /api/chat（未注册）
│   │   └── document.py          #     /api/documents/summarize（未注册）
│   └── services/                # ⚠️ 历史遗留，当前未使用
│       ├── llm_service.py
│       └── document_service.py
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── document.js
│   │   │   └── chat.js
│   │   ├── components/
│   │   │   ├── DocumentPanel.vue
│   │   │   └── ChatPanel.vue
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.js
│
├── scripts/
│   ├── start_agent.ps1
│   ├── stop_agent.ps1
│   └── status_agent.ps1
│
├── .env                         # LLM 配置（LLM_PROVIDER / DASHSCOPE_API_KEY / LLM_BASE_URL / LLM_MODEL）
├── .gitignore
└── README.md
```

---

## 版本

```text
v0.3.0
```

---

## 后续计划

- 向量检索 RAG 增强，支持更长文档的精准问答
- Token 使用量统计和展示
- 文档批量处理
- Markdown 报告导出增强
- 局域网 / 云服务器部署支持
