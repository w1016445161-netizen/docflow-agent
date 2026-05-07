# DocFlow Agent

DocFlow Agent 是一个基于 **FastAPI + Vue 3 + OpenAI-compatible LLM API** 构建的 AI 文档处理智能体项目。

项目面向学习资料、课程论文、实验报告、项目文档等场景，支持文档上传解析、结构化摘要生成、流式摘要输出、文档问答、参考片段展示、学习笔记生成、行动项提取、Markdown 报告导出、扫描型 PDF OCR 识别等功能。

当前版本：**v0.3.2**

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
展示结构化结果
↓
支持复制、问答、导出报告
```

当前项目已实现从“普通聊天 Demo”到“文档智能体”的基础升级。前端已经支持单文档的上传、摘要、问答、参考片段展示、学习笔记生成和 Markdown 报告导出；后端同时保留多文档对比、Excel 分析、图表生成、本地记忆等基础能力。

v0.3.2 版本开始补充后端工程化能力，新增统一异常处理体系、结构化日志系统和 request_id 全链路追踪，为后续数据库持久化、RAG 检索、测试与部署打基础。

---

## 二、当前已实现功能

### 1. 文档上传与结构化摘要

用户可以上传 TXT / PDF 文档，系统会自动解析文档内容，并调用大模型生成结构化摘要。

摘要内容包括：

1. 文档主要内容
2. 关键信息提取
3. 结构化要点
4. 可能的后续问题

当前支持两种摘要模式：

| 模式 | 说明 |
|---|---|
| 快速摘要 | 输入较短上下文，生成速度更快，适合快速预览 |
| 深度摘要 | 输入更多文档内容，生成更完整的结构化摘要，适合论文、报告和较长文档 |

当前运行链路：

```text
上传 TXT / PDF 文档
↓
backend/main.py 接收 /api/documents/summarize/stream 请求
↓
backend/document_parser.py 解析文档文本
↓
如果是扫描型 PDF 且普通文本提取过少，自动调用 OCR fallback
↓
backend/llm_client.py::summarize_text_stream() 构造摘要 prompt
↓
调用阿里云百炼 qwen 模型
↓
前端边生成边显示结构化摘要
```

---

### 2. 流式摘要输出

项目新增流式摘要能力。后端通过：

```text
POST /api/documents/summarize/stream
```

返回 `application/x-ndjson` 流式事件，前端使用 `response.body.getReader()` 逐段读取模型输出，实现“边生成边显示”的摘要体验。

流式事件包括：

| 事件类型 | 说明 |
|---|---|
| `status` | 当前处理状态，例如正在解析文档、正在生成摘要 |
| `meta` | 文件名、文件类型、字符数、是否截断、预览文本、doc_id 等元数据 |
| `delta` | 模型新增生成的文本片段 |
| `done` | 摘要生成完成 |
| `error` | 错误信息 |

旧版非流式接口 `POST /api/documents/summarize` 仍然保留。

---

### 3. 扫描型 PDF OCR 支持

项目支持扫描型 PDF 的自动识别。

当 PDF 无法直接提取文字，或普通文本提取结果少于 `OCR_MIN_TEXT_LENGTH` 时，系统会自动回退到 Tesseract OCR，对扫描型 PDF 页面进行文字识别，然后继续进入摘要和问答流程。

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

### 4. 基于文档内容的问答

用户上传文档并生成摘要后，可以继续围绕当前文档进行提问。

问答链路：

```text
用户提问
↓
后端根据 doc_id 读取文档索引
↓
backend/retriever.py 检索相关文档片段
↓
backend/llm_client.py::ask_llm() 构造问答 prompt
↓
调用阿里云百炼 qwen 模型
↓
返回基于文档内容的回答和相关参考片段
```

前端支持：

- 展示模型回答
- 展示相关原文片段
- 保存当前页面问答历史
- 复制回答内容

---

### 5. 学习笔记与行动项生成

前端提供两个快捷分析按钮：

| 功能 | 说明 |
|---|---|
| 生成学习笔记 | 基于当前文档生成适合学生复习的学习笔记，包括核心概念、重点知识、易混点和复习建议 |
| 生成行动项 | 从当前文档中提取任务、待办事项、后续问题或改进建议 |

这两个功能复用已有 `/ask` 文档问答接口，不额外引入新的后端接口。

---

### 6. 复制与 Markdown 报告导出

前端支持：

- 复制摘要
- 复制回答
- 导出 Markdown 分析报告

导出的 Markdown 报告包含：

- 文件名
- 文件类型
- 字符数
- 摘要模式
- 是否截断
- 结构化摘要
- 问答历史
- 每个问答的参考片段
- 生成时间

该功能在前端本地完成，不需要额外后端接口。

---

### 7. Excel 分析与图表生成

上传 Excel 文件后，后端可以分析表格结构、统计数值字段，并生成柱状图 / 折线图。

相关模块：

```text
backend/table_analyzer.py
backend/chart_generator.py
```

当前该能力主要在后端接口层实现，前端页面仍以 TXT / PDF 文档摘要和问答为主。

---

### 8. 本地记忆与报告保存

项目包含简单的本地记忆系统和 Markdown 报告保存能力：

| 模块 | 说明 |
|---|---|
| `backend/memory.py` | 保存用户偏好和历史记录 |
| `backend/report.py` | 保存问答报告为 Markdown 文件 |

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
| 日志系统 | Python logging + JSON formatter | 结构化日志记录 |
| 异常处理 | FastAPI exception_handler | 统一处理业务异常、HTTP 异常和未捕获异常 |
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
| ReadableStream | 实现流式摘要显示 |

当前前端主要使用 `DocumentPanel.vue` 展示文档上传、结构化摘要、文档问答、参考片段、复制和导出功能。`ChatPanel.vue` 为历史遗留或后续扩展组件，当前未作为主页面入口。

---

## 四、工程架构

### 1. 统一异常处理体系

项目建立了一套以 `AppException` 为基类的业务异常继承体系，并通过全局单一的 `exception_handler` 将所有异常转换为统一的 `ApiResponse` 响应。

#### 设计目标

1. 所有业务异常返回结构一致，前端可精确区分错误类型。
2. 新增异常类型无需修改核心处理逻辑，符合开闭原则。
3. 未捕获异常不会被直接抛出给客户端，始终返回安全的错误信息。
4. 错误响应中携带 `request_id`，便于根据一次请求定位对应日志。

#### 异常继承树（简化）

```text
AppException (基类，code 分区)
├── 1001 FileTypeNotSupportedError
├── 1002 FileParseError
├── 1003 DocumentNotFoundError
├── 2001 OCRException
└── 3001 LLMException
```

#### 错误码分区规则

| 区间 | 模块 | 示例 |
|---|---|---|
| 1000-1999 | 文档处理 | 文件类型不支持、解析失败、文档未找到 |
| 2000-2999 | OCR 识别 | OCR 环境不可用、识别超时 |
| 3000-3999 | LLM 调用 | 模型请求失败、上下文过长 |
| 5000+ | 系统兜底 | 未捕获异常、内部错误 |

#### 全局异常处理流程

```text
用户请求
  ↓
API 层执行业务逻辑
  ↓ 发生异常
global_exception_handler(Exception) 捕获
  ↓ isinstance 判断
  │
  ├── AppException
  │     ↓
  │   根据 code 和 message 构造 ApiResponse
  │
  ├── HTTPException
  │     ↓
  │   转换为 ApiResponse
  │
  └── 其他未捕获异常
        ↓
      记录完整 traceback
        ↓
      返回通用错误码 5000
  ↓
返回统一响应 { code, message, data, request_id }
```

#### 核心实现原则

1. **单一入口**：整个应用只注册一个 `@app.exception_handler(Exception)`，避免异常处理逻辑分散。
2. **深度判断**：通过 `isinstance(exc, AppException)` 识别业务异常，HTTP 异常和系统异常走统一兜底。
3. **可扩展**：新增业务异常只需继承 `AppException` 并分配新的错误码，无需改动 handler。
4. **安全输出**：未捕获异常只向客户端返回通用错误信息，详细 traceback 仅写入日志。

---

### 2. 结构化日志系统

项目新增结构化日志系统，采用 JSON 行格式记录关键事件，便于后续接入日志检索和问题排查工具。

#### 设计目标

1. 日志机器可读，可直接接入 ELK / Loki 等日志收集系统。
2. 支持按操作类型、文档 ID、用户 ID、错误类型等维度快速检索。
3. 每条日志自动关联 `request_id`，实现全链路追踪。
4. 通过统一 `log_event()` 函数减少散乱的 `print()` 和非结构化日志。

#### 日志字段规范

每条日志固定包含以下字段，缺省值填充为 `null`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `timestamp` | string | ISO 8601 时间戳 |
| `level` | string | INFO / WARNING / ERROR |
| `module` | string | 产生日志的模块名称 |
| `operation` | string | 操作类型：upload / parse / ocr / llm / query 等 |
| `request_id` | string | 本次请求的唯一标识，贯穿整个调用链 |
| `duration_ms` | number / null | 操作耗时，单位毫秒 |
| `user_id` | string / null | 用户 ID，当前预留 |
| `file_id` | string / null | 关联的文件 ID |
| `error_detail` | string / null | 错误详细信息 |

#### 关键路径日志覆盖

| 操作 | 记录点 |
|---|---|
| 文档上传 | 开始 / 完成 / 失败 |
| PDF 解析 | 解析方式选择（text 或 OCR）、起止、耗时 |
| OCR 识别 | 触发原因、页数、DPI、语言、耗时 |
| LLM 调用 | 请求开始 / 响应完成 / 失败，prompt 预览长度，耗时 |
| 文档问答 | 请求 doc_id、问题长度、检索片段数、回答耗时 |

#### 实现方式

1. 使用 Python 标准库 `logging` 的 `extra` 参数传递结构化字段。
2. 封装 `log_event()` 工具函数，统一字段填充逻辑。
3. 日志同时写入 `logs/app.log` 和控制台。
4. 使用 JSON Lines 格式，一行对应一次事件，便于检索和分析。

---

### 3. 请求全链路追踪（request_id）

为保证一次请求在日志、异常响应中能被完整串联，系统在所有入口自动注入 `request_id`，并使其在业务逻辑中透明传递。

#### 透传机制

```text
中间件 request_context_middleware
  ↓
生成 UUID → 写入 ContextVar
  ↓
业务逻辑任意深处调用 log_event()
  ↓
日志格式化器自动从 ContextVar 读取 request_id
  ↓
异常 handler 同样从 ContextVar 取出 request_id 写入 ApiResponse
```

#### 设计优势

1. 业务代码无需显式传递 `request_id` 参数，保持函数签名干净。
2. 即使发生未捕获异常，错误响应中仍包含 `request_id`，便于定位日志。
3. 同一次上传、解析、OCR、LLM 调用、问答流程可以通过同一个 `request_id` 串联。
4. 后续如果接入前端错误提示或日志平台，可以直接通过 `request_id` 查找完整调用链。

---

### 4. 后续工程化计划

当前 v0.3.2 主要完成异常处理、结构化日志和 request_id 追踪。后续工程化方向包括：

1. 补充 pytest 核心流程测试，覆盖异常分支。
2. 增加文档状态管理，记录 uploaded、parsing、summarizing、ready、failed 等状态。
3. 引入数据库持久化，设计文档表、问答记录表和处理日志表，替代当前文件索引方案。
4. 接入 Embedding 模型与向量存储，将关键词检索升级为语义检索。
5. 根据项目规模决定是否引入 Celery / Redis 处理长耗时异步任务。
6. 增加 Docker / docker-compose，简化本地部署与演示流程。

---

## 五、项目结构

```text
docflow_agent/
├── backend/
│   ├── main.py                  # FastAPI 主应用，当前后端主入口
│   ├── document_parser.py       # 文档解析，支持 TXT/PDF/DOCX/MD/Excel
│   ├── ocr_parser.py            # Tesseract OCR 识别扫描型 PDF
│   ├── llm_client.py            # LLM 调用，包含 ask_llm / summarize_text / summarize_text_stream
│   ├── chunker.py               # 长文本切分
│   ├── retriever.py             # 关键词检索
│   ├── memory.py                # 本地用户记忆
│   ├── report.py                # Markdown 报告保存
│   ├── table_analyzer.py        # Excel 表格分析
│   ├── chart_generator.py       # Excel 图表生成
│   ├── multi_doc.py             # 多文档上下文构建
│   ├── requirements.txt         # 后端依赖
│   │
│   ├── core/                    # 工程化基础模块
│   │   ├── __init__.py          # core 包初始化
│   │   ├── response.py          # ApiResponse 统一响应模型
│   │   ├── exceptions.py        # AppException 异常体系与错误码
│   │   └── logging.py           # 结构化日志、request_id 透传与 log_event
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
│   │   │   ├── document.js      # 文档摘要、流式摘要、问答等 API 封装
│   │   │   └── chat.js          # 历史遗留聊天 API 封装
│   │   ├── components/
│   │   │   ├── DocumentPanel.vue # 当前主页面组件
│   │   │   └── ChatPanel.vue     # 历史遗留 / 后续扩展组件
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.js
│
├── scripts/
│   ├── start_agent.ps1          # Windows 一键启动脚本
│   ├── stop_agent.ps1           # Windows 停止脚本
│   └── status_agent.ps1         # Windows 状态检查脚本
│
├── docs/
│   └── images/                  # README 效果截图
│
├── storage/                     # 本地运行数据，已加入 .gitignore
├── logs/                        # 本地日志目录，建议加入 .gitignore
├── .env.example                 # 环境变量示例
├── .gitignore
└── README.md
```

---

## 六、环境准备

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

## 七、环境变量配置

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

## 八、安装 Tesseract-OCR

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

## 九、启动项目

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

## 十、API 接口说明

### 1. 非流式文档摘要

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
| `summary_mode` | string | 摘要模式，可选 `fast` 或 `deep` |

当前支持格式：

```text
.txt
.pdf
```

返回示例：

```json
{
  "doc_id": "example-doc-id",
  "filename": "example.pdf",
  "file_type": "pdf",
  "char_count": 6774,
  "is_truncated": false,
  "preview": "提取出的前 500 字文本",
  "summary": "结构化摘要内容，Markdown 格式",
  "summary_mode": "deep",
  "model": "docflow-agent",
  "usage": null
}
```

说明：

- `char_count` 表示解析出的文本字符数
- `is_truncated` 表示是否超过当前摘要模式的输入限制
- `preview` 返回前 500 字文本预览
- `summary` 为模型生成的结构化摘要
- `doc_id` 可用于后续 `/ask` 文档问答
- `usage` 当前为 `null`，Token 使用量统计将在后续版本补充
- 扫描型 PDF 会在普通文本提取过少时自动尝试 OCR fallback

---

### 2. 流式文档摘要

```text
POST /api/documents/summarize/stream
```

请求类型：

```text
multipart/form-data
```

参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `file` | File | TXT 或 PDF 文件 |
| `summary_mode` | string | 摘要模式，可选 `fast` 或 `deep` |

返回类型：

```text
application/x-ndjson
```

事件示例：

```json
{"type":"status","message":"正在解析文档..."}
{"type":"meta","filename":"example.pdf","file_type":"pdf","char_count":6675,"is_truncated":false,"preview":"...","doc_id":"...","summary_mode":"deep"}
{"type":"status","message":"正在生成摘要..."}
{"type":"delta","text":"一、文档主要内容..."}
{"type":"done"}
```

说明：

- 该接口用于前端流式展示摘要
- `fast` 模式生成更快，适合快速预览
- `deep` 模式输入更多文档内容，摘要更完整
- 旧版非流式接口 `POST /api/documents/summarize` 仍然保留

---

### 3. 通用文档上传

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

### 4. 文档问答

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

- 需要先上传文档并获取 `doc_id`
- 系统会检索相关文档片段
- 然后调用大模型生成基于文档内容的回答
- 前端会展示回答和相关原文片段

---

### 5. 多文档对比

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

说明：

当前该能力主要在后端接口层实现，前端尚未提供完整多文档管理页面。

---

### 6. OCR 状态检查

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

### 7. 其他接口

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

### 8. 历史遗留接口说明

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

## 十一、效果展示

### 文档上传与结构化摘要

![文档摘要效果](docs/images/pdf-summary-result.png)

---

### 流式摘要输出

![流式摘要输出](docs/images/streaming-summary.png)

---

### 基于文档内容问答

![文档问答与参考片段](docs/images/document-qa.png)

---

## 十二、当前项目亮点

1. 实现文档上传、解析、摘要、问答的完整主链路
2. 支持普通 PDF 与扫描型 PDF 自动解析
3. 当 PDF 文本提取过少时自动回退到 Tesseract OCR
4. 支持快速摘要 / 深度摘要两种模式
5. 支持流式摘要输出，前端可以边生成边显示模型结果
6. 通过专用 `summarize_text()` / `summarize_text_stream()` prompt 生成结构化摘要，减少模型发散
7. 摘要接口返回 `doc_id`，支持摘要后继续围绕当前文档提问
8. 支持基于当前文档的问答，并展示相关原文片段
9. 支持问答历史、复制摘要、复制回答和 Markdown 报告导出
10. 支持一键生成学习笔记和行动项
11. 引入统一异常处理体系，按文件处理、OCR、LLM 调用等模块划分业务错误码
12. 引入 request_id 全链路追踪和 JSON 结构化日志，便于定位文档上传、解析、OCR、LLM 调用等关键流程
13. LLM 调用统一读取根目录 `.env` 配置，便于切换 OpenAI-compatible 服务商
14. 支持 Excel 表格分析和图表生成
15. 提供 PowerShell 脚本简化 Windows 本地启动与停止

---

## 十三、当前限制

1. 前端当前主要围绕单文档摘要与问答流程，暂未提供完整多文档管理页面
2. `/api/documents/summarize` 和 `/api/documents/summarize/stream` 当前主要支持 TXT / PDF
3. OCR 依赖本机 Tesseract 环境，不适合无配置直接部署
4. 文档检索目前主要基于关键词匹配，还没有接入 Embedding 模型和向量数据库
5. Token 使用量统计尚未完整展示到前端
6. Excel 分析与图表生成能力主要在后端，前端展示还可以继续完善
7. `routers/` 和 `services/` 目录属于历史遗留 / 实验性结构，当前主运行链路仍是 `backend/main.py + 扁平模块`
8. 当前暂未引入数据库，文档索引、chunk 和问答上下文仍主要依赖本地文件存储
9. 当前暂未实现用户系统、JWT 鉴权和多用户隔离
10. 当前日志主要用于本地调试，尚未接入远程日志平台

---

## 十四、后续计划

- 增加文档状态管理，记录 uploaded、parsing、summarizing、ready、failed 等处理状态
- 引入 SQLAlchemy，持久化文档元数据、处理状态和问答记录
- 接入 Embedding 模型与向量检索，增强 RAG 问答能力
- 增加基础 pytest 测试，覆盖文档上传、解析、摘要、问答等核心流程
- 增加 Token 使用量统计与前端展示
- 完善前端文档问答交互体验
- 增加多文档管理与多文档对比前端界面
- 优化 OCR 识别结果清洗与页面级来源展示
- 增强 Markdown 报告导出能力
- 支持 Docker / docker-compose 本地部署
- 支持局域网或云服务器部署

---

## 十五、版本记录

### v0.3.2

- 设计并实现统一异常处理体系，新增 `AppException` 业务异常基类及文件处理、OCR、LLM 调用等异常类型
- 引入统一 `ApiResponse` 错误响应模型，错误响应包含 `code`、`message`、`data`、`request_id`
- 新增全局单一 `exception_handler`，统一处理业务异常、HTTP 异常和未捕获异常
- 引入 JSON 结构化日志系统，支持按操作类型、错误类型、request_id 等字段检索
- 添加 `request_id` 全链路追踪中间件，通过 `ContextVar` 在日志与异常响应中自动透传
- 在文档上传、PDF 解析、OCR 识别、LLM 调用、文档问答等关键路径增加处理状态、耗时和错误日志
- 当前改动保持原有 API 主流程不变，主要增强后端可观测性与问题排查能力

---

### v0.3.1

- 新增流式摘要接口 `POST /api/documents/summarize/stream`
- 前端支持边生成边显示结构化摘要
- 新增快速摘要 / 深度摘要模式
- 文档摘要接口返回 `doc_id`，支持摘要后继续文档问答
- 前端支持基于当前文档提问
- 前端展示相关原文片段
- 新增问答历史
- 新增复制摘要、复制回答功能
- 新增 Markdown 报告导出
- 新增一键生成学习笔记和行动项功能

---

### v0.3.0

- 新增 `/api/documents/summarize` 文档摘要接口
- 新增 `summarize_text()` 专用摘要 prompt
- 统一 LLM 配置读取逻辑
- 支持阿里云百炼 OpenAI-compatible API
- 支持扫描型 PDF OCR fallback
- 修复从项目根目录启动 `backend.main:app` 的导入问题
- 保留 `/upload`、`/ask`、`/compare` 等已有接口

---

## 十六、安全说明

项目中的 `.env` 文件包含 API Key 等敏感信息，已加入 `.gitignore`。

请不要提交以下文件或目录：

```text
.env
backend/.env
.claude/
storage/
.runtime/
logs/
```

如果 API Key 曾经被公开展示，建议立即在服务商控制台删除或轮换该 Key。

---

## License

This project is for learning and personal portfolio demonstration.