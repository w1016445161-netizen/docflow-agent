# DocFlow Agent

DocFlow Agent 是一个基于 **FastAPI + Vue 3 + 大模型 API** 构建的 AI 文档处理智能体项目。项目面向学习资料、课程论文、实验报告和项目文档等场景，支持用户上传 TXT / PDF 文档，系统自动解析文档内容，并调用大模型生成结构化摘要。

当前版本已经完成从“聊天智能体”到“文档智能体”的第一阶段升级：支持真实大模型 API 调用、文档上传、文本解析、结构化摘要生成，以及 Token 使用情况展示。

---

## 项目亮点

- 支持 TXT / PDF 文档上传
- 后端自动解析文档文本内容
- 支持可提取文字层的 PDF 文件
- 调用阿里云百炼 OpenAI-compatible API
- 使用 qwen3.6-flash 模型生成结构化摘要
- 前端展示文件名、文件类型、字符数和摘要内容
- 前端展示输入 Token、输出 Token 和总 Token
- 支持 Markdown 格式渲染模型输出
- 前后端分离架构，便于后续扩展 RAG、文档问答和报告生成能力

---

## 当前已实现功能

### 1. 大模型聊天接口

项目已经接入真实大模型 API，后端通过统一的 `LLMService` 封装模型调用逻辑。

用户可以在前端输入问题，后端调用大模型接口并返回回答内容和 Token 使用情况。

已实现链路：

```text
Vue 前端
↓
FastAPI 后端 /api/chat
↓
LLMService
↓
阿里云百炼 qwen3.6-flash
↓
返回模型回复与 Token 使用情况
```

---

### 2. 文档上传与摘要生成

用户可以上传 TXT 或 PDF 文件，后端自动识别文件类型并提取文本内容，然后构造文档摘要 Prompt，调用大模型生成结构化摘要。

已实现链路：

```text
上传 TXT / PDF 文档
↓
后端解析文档文本
↓
构造结构化摘要 Prompt
↓
调用大模型生成摘要
↓
前端展示摘要结果和 Token 消耗
```

当前摘要结果包含：

- 文档主要内容
- 关键信息提取
- 结构化要点
- 可能的后续问题
- 模型名称
- 输入 Token、输出 Token、总 Token

---

### 3. 前端结果展示

前端基于 Vue 3 实现，支持：

- 文档上传
- 文件信息展示
- 结构化摘要展示
- Markdown 渲染
- Token 使用情况展示
- 错误提示展示

---

## 技术栈

### 后端

- Python
- FastAPI
- Uvicorn
- pypdf
- python-multipart
- python-dotenv
- OpenAI Python SDK
- 阿里云百炼 OpenAI-compatible API

### 前端

- Vue 3
- Vite
- JavaScript
- markdown-it
- Fetch API

### 模型服务

- 阿里云百炼
- qwen3.6-flash
- OpenAI-compatible API 调用方式

---

## 项目目录结构

```text
docflow-agent/
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── chat.py
│   │   └── document.py
│   └── services/
│       ├── llm_service.py
│       └── document_service.py
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── chat.js
│   │   │   └── document.js
│   │   ├── components/
│   │   │   ├── ChatPanel.vue
│   │   │   └── DocumentPanel.vue
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.js
│
├── README.md
└── .gitignore
```

---

## 后端启动方式

进入项目根目录：

```powershell
cd D:\projects\docflow_agent
```

创建并激活虚拟环境后，安装依赖：

```powershell
pip install fastapi uvicorn openai python-dotenv python-multipart pypdf
```

在项目根目录创建 `.env` 文件：

```env
LLM_PROVIDER=aliyun
DASHSCOPE_API_KEY=你的阿里云百炼API_KEY
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.6-flash
```

启动后端：

```powershell
python -m uvicorn backend.main:app --reload
```

后端接口文档地址：

```text
http://127.0.0.1:8000/docs
```

健康检查接口：

```text
http://127.0.0.1:8000/api/health
```

---

## 前端启动方式

进入前端目录：

```powershell
cd D:\projects\docflow_agent\frontend
```

安装依赖：

```powershell
npm install
```

创建前端环境变量文件 `.env.development`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

启动前端：

```powershell
npm run dev
```

前端访问地址：

```text
http://localhost:5173
```

---

## API 接口说明

### 1. 聊天接口

```text
POST /api/chat
```

请求示例：

```json
{
  "message": "请用三句话介绍这个文档智能体项目。"
}
```

返回示例：

```json
{
  "model": "qwen3.6-flash",
  "content": "模型回复内容",
  "usage": {
    "prompt_tokens": 41,
    "completion_tokens": 90,
    "total_tokens": 131
  }
}
```

---

### 2. 文档摘要接口

```text
POST /api/documents/summarize
```

请求类型：

```text
multipart/form-data
```

参数：

```text
file: 上传的 TXT 或 PDF 文件
```

返回示例：

```json
{
  "filename": "example.pdf",
  "file_type": "pdf",
  "char_count": 6763,
  "is_truncated": false,
  "preview": "提取出的前 500 字文本",
  "summary": "结构化摘要内容",
  "model": "qwen3.6-flash",
  "usage": {
    "prompt_tokens": 4672,
    "completion_tokens": 1017,
    "total_tokens": 5689
  }
}
```

---

## 当前版本限制

当前版本支持：

- TXT 文档
- 可提取文字层的 PDF 文档

暂不支持：

- 扫描版 PDF
- 图片型 PDF
- 手写文档
- 多文件批量处理
- 长文档向量检索问答

如果上传扫描版 PDF，系统可能提示：

```text
没有从文档中提取到有效文本。如果是扫描版 PDF，需要后续接入 OCR。
```

后续可以接入 PaddleOCR、Tesseract 或云 OCR 服务，扩展扫描版 PDF 识别能力。

---

## 后续计划

### v0.3 文档问答能力

- 上传文档后保存文档文本
- 用户基于当前文档继续提问
- 后端基于文档内容生成回答
- 实现“上传文档 + 连续问答”的基础 Agent 体验

### v0.4 RAG 检索增强

- 文档切分
- 向量化存储
- 相似片段检索
- 基于检索结果回答问题
- 支持长文档问答

### v0.5 报告生成

- 根据文档内容生成 Markdown 报告
- 支持摘要、问答记录和结构化结论导出
- 支持实验报告、课程笔记和项目说明文档生成

### v0.6 部署与演示

- 支持局域网访问
- 支持云服务器部署
- 增加项目演示截图
- 完善在线访问说明

---

## 安全说明

项目中的 API Key 只应保存在后端 `.env` 文件中，不应写入前端代码，也不应提交到 GitHub。

`.gitignore` 中应包含：

```gitignore
.env
.env.*
frontend/.env.development
```

---

## 项目状态

当前版本：

```text
DocFlow Agent v0.2
```

已完成：

```text
真实大模型 API 接入
TXT / PDF 文档上传
文档文本解析
结构化摘要生成
Token 使用情况展示
Markdown 渲染
```

下一阶段目标：

```text
基于已上传文档的智能问答
```

---

## 项目适用场景

- 课程论文摘要
- 实验报告整理
- 学习笔记总结
- PDF 资料快速理解
- 项目文档问答
- 简历项目展示
- AI Agent 学习实践