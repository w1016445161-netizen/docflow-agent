# DocFlow Agent

DocFlow Agent 是一个基于 **FastAPI + Vue 3 + OpenAI-compatible LLM API** 构建的 AI 文档处理智能体项目。

项目面向学习资料、课程论文、实验报告、项目文档等场景，支持文档上传解析、结构化摘要生成、文档问答、多文档对比、Excel 分析与扫描型 PDF OCR 识别等功能。

当前版本：**v0.3.0**

---

## 一、项目简介

DocFlow Agent 的核心目标是将常见文档处理流程自动化：

```text
上传文档
↓
解析文本内容
↓
必要时进行 OCR 识别
↓
调用大模型生成摘要或回答问题
↓
返回结构化结果
```

当前项目已实现从“普通聊天 Demo”到“文档智能体”的基础升级，能够完成：

- TXT / PDF 文档结构化摘要
- 扫描型 PDF OCR fallback
- 文档上传、切分与索引
- 基于文档内容的问答
- 多文档对比
- Excel 表格分析与图表生成
- 本地用户记忆与问答报告保存

---

## 二、当前已实现功能

### 1. 文档上传与结构化摘要

用户上传 TXT 或 PDF 文档后，后端会自动解析文本内容，并调用大模型生成结构化摘要。

摘要结果包括：

1. 文档主要内容
2. 关键信息提取
3. 结构化要点
4. 可能的后续问题

当前运行链路：

```text
上传 TXT / PDF 文档
↓
backend/main.py 接收 /api/documents/summarize 请求
↓
backend/document_parser.py 解析文档文本
↓
如果是扫描型 PDF 且普通文本提取过少，自动调用 OCR fallback
↓
backend/llm_client.py::summarize_text() 构造摘要 prompt
↓
调用阿里云百炼 qwen 模型
↓
返回结构化摘要
```

---

### 2. 扫描型 PDF OCR 支持

项目支持扫描型 PDF 的自动识别。

当 PDF 不能直接提取文本，或普通文本提取结果少于 `OCR_MIN_TEXT_LENGTH` 时，系统会自动回退到 Tesseract OCR，对 PDF 页面进行文字识别，再进入摘要或问答流程。

OCR 处理链路：

```text
上传 PDF
↓
pypdf 尝试提取文本
↓
如果提取文本过少
↓
backend/ocr_parser.py 调用 Tesseract OCR
↓
识别页面图片中的文字
↓
返回给 document_parser.py
↓
进入 LLM 摘要 / 问答流程
```

OCR 需要本机安装 Tesseract-OCR，并在环境变量中配置路径。

---

### 3. 文档问答

用户通过 `/upload` 上传文档后，可以使用返回的 `doc_id` 对文档内容进行提问。

问答链路：

```text
用户提问
↓
backend/retriever.py 检索相关文档片段
↓
backend/llm_client.py::ask_llm() 构造 QA prompt
↓
调用阿里云百炼 qwen 模型
↓
返回基于文档内容的回答
```

---

### 4. 多文档对比

支持同时选择多个已上传文档，构造多文档上下文，并调用大模型分析它们的共同点、差异点和核心内容。

---

### 5. Excel 分析与图表生成

上传 Excel 文件后，系统可以：

- 读取表格数据
- 分析字段结构
- 统计数值列
- 生成数据预览
- 自动生成柱状图 / 折线图

相关模块：

```text
backend/table_analyzer.py
backend/chart_generator.py
```

---

### 6. 本地记忆与报告保存

项目包含简单的本地记忆系统和 Markdown 报告保存能力：

- `backend/memory.py`：保存用户偏好和历史记录
- `backend/report.py`：保存问答报告为 Markdown 文件

---

## 三、技术栈

### 后端

| 模块 | 技术 / 文件 | 说明 |
|---|---|---|
| Web 框架 | FastAPI | 后端 API 服务 |
| ASGI 服务 | Uvicorn | 本地开发服务 |
| LLM SDK | openai | 使用 OpenAI-compatible API 调用模型 |
| 模型服务 | 阿里云百炼 DashScope | 当前示例使用 qwen 模型 |
| PDF 解析 | pypdf | 提取普通 PDF 文本 |
| 扫描 PDF OCR | Tesseract + pytesseract + PyMuPDF + Pillow | OCR fallback |
| Word 解析 | python-docx | 解析 `.docx` |
| Excel 解析 | pandas + openpyxl | 表格读取与统计 |
| 图表生成 | matplotlib | 生成柱状图 / 折线图 |
| 环境变量 | python-dotenv | 读取 `.env` 配置 |

---

### 前端

| 技术 | 说明 |
|---|---|
| Vue 3 | 前端框架 |
| Vite | 前端构建工具 |
| JavaScript | 前端开发语言 |
| markdown-it | 渲染模型返回的 Markdown |
| Fetch API | 调用后端接口 |

当前前端主要使用 `DocumentPanel.vue` 展示文档上传与摘要结果。`ChatPanel.vue` 为后续文档问答界面预留。

---

## 四、项目结构

```text
docflow_agent/
├── backend/
│   ├── main.py                  # FastAPI 主应用，当前后端主入口
│   ├── document_parser.py       # 文档解析，支持 TXT/PDF/DOCX/MD/Excel
│   ├── ocr_parser.py            # Tesseract OCR 识别扫描型 PDF
│   ├── llm_client.py            # LLM 调用封装，包含 ask_llm / summarize_text
│   ├── chunker.py               # 长文本切分
│   ├── retriever.py             # 关键词检索
│   ├── memory.py                # 本地用户记忆
│   ├── report.py                # Markdown 报告保存
│   ├── table_analyzer.py        # Excel 表格分析
│   ├── chart_generator.py       # Excel 图表生成
│   ├── multi_doc.py             # 多文档上下文构建
│   ├── requirements.txt         # 后端依赖
│   │
│   ├── routers/                 # 历史遗留 / 实验性目录，当前未注册到 main.py
│   │   ├── chat.py              # /api/chat，当前未启用
│   │   └── document.py          # 旧版文档摘要路由，当前未启用
│   │
│   └── services/                # 历史遗留 / 实验性目录，当前主链路未使用
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
│   ├── start_agent.ps1          # Windows 一键启动脚本
│   ├── stop_agent.ps1           # Windows 停止脚本
│   └── status_agent.ps1         # Windows 状态检查脚本
│
├── storage/                     # 本地运行数据，已加入 .gitignore
├── .env.example                 # 环境变量示例
├── .gitignore
└── README.md
```

---

## 五、环境准备

### 1. 克隆项目

```bash
git clone https://github.com/w1016445161-netizen/docflow-agent.git
cd docflow-agent
```

---

### 2. 创建 Python 虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

### 3. 安装后端依赖

```powershell
pip install -r backend/requirements.txt
```

如果缺少 OCR 相关依赖，可手动安装：

```powershell
pip install pymupdf pytesseract pillow
```

---

### 4. 安装前端依赖

```powershell
cd frontend
npm install
```

---

## 六、环境变量配置

在项目根目录创建 `.env` 文件。

请不要把真实 `.env` 提交到 GitHub。

示例：

```env
# LLM Configuration
LLM_PROVIDER=aliyun
DASHSCOPE_API_KEY=your_dashscope_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.6-flash

# OCR Configuration
OCR_ENABLED=true
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_LANG=chi_sim+eng
OCR_DPI=200
OCR_MAX_PAGES=20
OCR_MIN_TEXT_LENGTH=80
```

字段说明：

| 变量 | 说明 |
|---|---|
| `LLM_PROVIDER` | 当前模型服务商，示例为 `aliyun` |
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key |
| `LLM_BASE_URL` | OpenAI-compatible API 地址 |
| `LLM_MODEL` | 使用的模型名称 |
| `OCR_ENABLED` | 是否启用 OCR fallback |
| `TESSERACT_CMD` | Tesseract 可执行文件路径 |
| `OCR_LANG` | OCR 语言包，例如 `chi_sim+eng` |
| `OCR_DPI` | PDF 转图片时的分辨率 |
| `OCR_MAX_PAGES` | OCR 最多处理页数 |
| `OCR_MIN_TEXT_LENGTH` | 普通 PDF 提取文本少于该值时启用 OCR |

---

## 七、安装 Tesseract-OCR

如果需要识别扫描型 PDF，需要先安装 Tesseract-OCR。

### Windows

推荐安装路径：

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

安装后确认语言包中包含：

```text
chi_sim
eng
```

可以通过后端接口检查：

```text
GET /ocr/status
```

---

## 八、启动项目

### 方式一：使用脚本启动

在项目根目录执行：

```powershell
.\scripts\start_agent.ps1
```

停止服务：

```powershell
.\scripts\stop_agent.ps1
```

查看状态：

```powershell
.\scripts\status_agent.ps1
```

---

### 方式二：手动启动后端

在项目根目录执行：

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

后端 API 文档地址：

```text
http://127.0.0.1:8000/docs
```

---

### 方式三：手动启动前端

```powershell
cd frontend
npm run dev
```

前端访问地址：

```text
http://localhost:5173
```

---

## 九、API 接口说明

### 1. 文档上传摘要

```text
POST /api/documents/summarize
```

请求类型：

```text
multipart/form-data
```

参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `file` | File | TXT 或 PDF 文件 |

当前支持格式：

```text
.txt
.pdf
```

返回示例：

```json
{
  "filename": "example.pdf",
  "file_type": "pdf",
  "char_count": 6774,
  "is_truncated": false,
  "preview": "提取出的前 500 字文本",
  "summary": "结构化摘要内容，Markdown 格式",
  "model": "docflow-agent",
  "usage": null
}
```

说明：

- `char_count` 表示解析出的文本字符数
- `is_truncated` 表示是否超过 12000 字符输入限制
- `preview` 返回前 500 字文本预览
- `summary` 为模型生成的结构化摘要
- `usage` 当前为 `null`，Token 使用量统计将在后续版本补充
- 扫描型 PDF 会在普通文本提取过少时自动尝试 OCR fallback

---

### 2. 通用文档上传

```text
POST /upload
```

请求类型：

```text
multipart/form-data
```

参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `file` | File | 上传文档 |

支持格式：

```text
.txt
.pdf
.docx
.md
.xlsx
.xls
```

说明：

- 上传后会自动解析文档文本
- 文本会被切分为片段并建立本地索引
- Excel 文件会额外进行表格分析和图表生成
- 返回结果中包含 `doc_id`，可用于后续文档问答

---

### 3. 文档问答

```text
POST /ask
```

请求参数：

```json
{
  "doc_id": "文档ID",
  "question": "这份文档的主要内容是什么？"
}
```

说明：

- 需要先通过 `/upload` 上传文档并获取 `doc_id`
- 系统会检索相关文档片段
- 然后调用大模型生成基于文档内容的回答

---

### 4. 多文档对比

```text
POST /compare
```

请求参数：

```json
{
  "doc_ids": ["doc_id_1", "doc_id_2"],
  "question": "请比较这些文档的主要内容、共同点和差异点。"
}
```

---

### 5. OCR 状态检查

```text
GET /ocr/status
```

返回示例：

```json
{
  "available": true,
  "version": "5.3.0.20221214",
  "languages": ["chi_sim", "eng"],
  "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
}
```

说明：

- `available=true` 表示 OCR 环境可用
- `languages` 中应包含 `chi_sim` 和 `eng`
- 如果不可用，请检查 Tesseract 是否安装，以及 `.env` 中的 `TESSERACT_CMD` 是否正确

---

### 6. 其他接口

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

---

### 7. 历史遗留接口说明

```text
POST /api/chat
```

说明：

该接口定义在 `backend/routers/chat.py` 中，但当前没有在 `backend/main.py` 中注册，因此访问会返回 404。

当前可用的文档问答接口是：

```text
POST /ask
```

---

## 十、效果展示

### 文档上传与结构化摘要

后续可在此处添加截图：

```text
docs/images/pdf-summary-result.png
```

Markdown 示例：

```markdown
![文档摘要效果](docs/images/pdf-summary-result.png)
```

---

### OCR 扫描型 PDF 识别

后续可在此处添加截图：

```text
docs/images/ocr-summary-result.png
```

---

### Swagger API 文档

后续可在此处添加截图：

```text
docs/images/swagger-api-docs.png
```

---

## 十一、当前项目亮点

1. 实现文档上传、解析、摘要、问答的完整后端链路
2. 支持普通 PDF 与扫描型 PDF 的自动解析
3. 当 PDF 文本提取过少时自动回退到 Tesseract OCR
4. 通过专用 `summarize_text()` prompt 生成结构化摘要，减少模型发散
5. LLM 调用统一读取根目录 `.env` 配置，便于切换 OpenAI-compatible 服务商
6. 支持 Excel 表格分析和图表生成
7. 保留本地记忆和 Markdown 报告保存能力
8. 提供 PowerShell 脚本简化 Windows 本地启动与停止

---

## 十二、当前限制

1. `/api/documents/summarize` 当前仅支持 TXT / PDF
2. `usage` 当前为 `null`，尚未展示 Token 使用量
3. OCR 依赖本机 Tesseract 环境，不适合直接无配置部署
4. 文档检索目前主要基于关键词匹配，还没有接入向量数据库
5. 前端当前主要展示文档上传摘要功能，文档问答界面仍需进一步完善
6. `routers/` 和 `services/` 目录属于历史遗留 / 实验性结构，当前主运行链路仍是 `backend/main.py + 扁平模块`

---

## 十三、后续计划

- 接入 Embedding 模型与向量检索，增强 RAG 问答能力
- 增加 Token 使用量统计与前端展示
- 完善前端文档问答界面
- 支持多文档批量处理
- 优化 OCR 识别结果清洗与页面级来源展示
- 增强 Markdown 报告导出能力
- 增加 smoke test 脚本，自动检查核心接口
- 支持局域网或云服务器部署

---

## 十四、版本记录

### v0.3.0

- 新增 `/api/documents/summarize` 文档摘要接口
- 新增 `summarize_text()` 专用摘要 prompt
- 统一 LLM 配置读取逻辑
- 支持阿里云百炼 OpenAI-compatible API
- 支持扫描型 PDF OCR fallback
- 修复从项目根目录启动 `backend.main:app` 的导入问题
- 保留 `/upload`、`/ask`、`/compare` 等已有接口

---

## 十五、安全说明

项目中的 `.env` 文件包含 API Key 等敏感信息，已加入 `.gitignore`。

请不要提交以下文件或目录：

```text
.env
backend/.env
.claude/
storage/
.runtime/
```

如果 API Key 曾经被公开展示，建议立即在服务商控制台删除或轮换该 Key。

---

## License

This project is for learning and personal portfolio demonstration.