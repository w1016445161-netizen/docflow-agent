# DocFlow-Agent

DocFlow-Agent 是一个面向学习、实验报告、课程文档和项目资料整理场景的 AI 文档处理 Agent 原型项目。

项目目标是构建一个可以处理真实文档的智能体系统，使用户能够上传文档，并完成文档解析、文本切分、相关片段检索、文档问答和 Markdown 报告生成等任务。

当前项目处于 `v0.1 prototype` 开发阶段，重点是先完成一个最小可运行链路。

```text
文档上传
↓
文档解析
↓
文本切分
↓
相关片段检索
↓
LLM / Mock 模式回答
↓
Markdown 报告生成
```

---

## 1. 项目背景

在学习、课程实验、简历准备和日常办公中，经常需要处理大量非结构化文档，例如实验报告、课程资料、项目 README、论文笔记、学习资料和表格数据等。

传统方式需要人工阅读、提取重点、整理格式和生成报告，效率较低。DocFlow-Agent 希望通过大模型与工具模块结合，实现一个轻量级的文档处理智能体，帮助用户完成文档内容解析、重点信息提取、文档问答和报告生成。

---

## 2. 当前项目状态

当前版本是原型阶段，已经完成基础项目结构和后端核心模块设计。

已完成内容：

- FastAPI 后端基础接口
- Vue 前端项目骨架
- PDF / Word / TXT / Markdown 文档解析模块
- 文本切分模块
- 简易关键词检索模块
- LLM 调用模块
- Mock 模式测试流程
- Markdown 报告生成模块
- 表格分析模块雏形
- 图表生成模块雏形
- 多文档处理模块雏形
- 简单记忆模块雏形

后续将继续完善：

- 接入真实大模型 API
- 完成前端上传和问答交互页面
- 增加 RAG 向量检索
- 增加 Agent 工具调用日志
- 增加更完整的报告导出能力
- 增加项目截图、演示视频和部署说明

---

## 3. 技术栈

### 后端

- Python
- FastAPI
- Uvicorn
- pypdf
- python-docx
- pandas
- openpyxl
- matplotlib
- python-dotenv
- OpenAI-compatible API

### 前端

- Vue 3
- Vite
- JavaScript
- CSS

### 后续计划使用

- FAISS / Chroma
- Embedding 模型
- RAG 检索增强生成
- Agent Tool Calling
- SQLite 本地数据存储

---

## 4. 项目结构

```text
docflow-agent/
├─ backend/
│  ├─ main.py                 # FastAPI 后端入口
│  ├─ document_parser.py      # 文档解析模块
│  ├─ chunker.py              # 文本切分模块
│  ├─ retriever.py            # 简易检索模块
│  ├─ llm_client.py           # LLM / Mock 调用模块
│  ├─ report.py               # Markdown 报告生成模块
│  ├─ table_analyzer.py       # 表格分析模块
│  ├─ chart_generator.py      # 图表生成模块
│  ├─ multi_doc.py            # 多文档处理模块
│  ├─ memory.py               # 简单记忆模块
│  ├─ requirements.txt        # 后端依赖
│  └─ storage/                # 本地运行数据目录，不上传 GitHub
│     ├─ uploads/             # 上传文件目录
│     ├─ index/               # 文档索引目录
│     └─ outputs/             # 报告输出目录
│
├─ frontend/
│  ├─ src/
│  │  ├─ App.vue              # 前端主页面
│  │  └─ main.js              # 前端入口
│  ├─ package.json
│  └─ vite.config.js
│
├─ .gitignore
└─ README.md
```

---

## 5. 核心功能

### 5.1 文档解析

项目支持将不同格式的文档解析为纯文本，方便后续进行切分、检索和问答。

当前支持格式：

- `.pdf`
- `.docx`
- `.txt`
- `.md`

后续计划支持：

- `.xlsx`
- `.csv`
- `.pptx`

---

### 5.2 文本切分

长文档通常无法直接全部传入大模型，因此系统会先将文档切分成多个文本片段。

切分后的文本片段可以用于：

- 文档检索
- RAG 问答
- 上下文构造
- 摘要生成
- 报告生成

---

### 5.3 简易检索

当前版本使用关键词重合度进行基础检索。

基础流程如下：

```text
用户问题
↓
问题分词
↓
文档片段分词
↓
计算关键词重合度
↓
返回相关片段
```

该模块是 RAG 的原型版本。后续会升级为基于 Embedding 的向量检索。

---

### 5.4 LLM / Mock 模式

项目当前支持 Mock 模式，方便在没有真实 API Key 的情况下测试完整流程。

Mock 模式可以验证：

- 文档上传是否成功
- 文档解析是否成功
- 文本切分是否成功
- 检索是否返回相关片段
- 报告是否能够生成

后续可以通过 `.env` 文件切换到真实大模型 API。

---

### 5.5 Markdown 报告生成

系统可以将用户问题、模型回答和相关结果保存为 Markdown 报告，便于后续整理为学习笔记、实验报告或项目文档。

默认输出目录：

```text
backend/storage/outputs/
```

---

### 5.6 表格分析模块

项目中预留了表格分析模块，用于后续支持 Excel 数据分析场景。

计划能力包括：

- 读取 Excel 表格
- 统计行列信息
- 生成基础数据摘要
- 分析数值字段
- 根据表格内容生成分析报告

---

### 5.7 图表生成模块

项目中预留了图表生成模块，用于后续支持数据可视化。

计划能力包括：

- 根据表格数据生成柱状图
- 根据表格数据生成折线图
- 保存图表图片
- 将图表结果用于报告生成

---

### 5.8 多文档处理模块

项目中预留了多文档处理模块，用于后续实现多个文档之间的联合分析。

计划能力包括：

- 多文档上传
- 多文档内容合并
- 多文档对比
- 多文档问答
- 多文档总结报告生成

---

### 5.9 简单记忆模块

项目中包含简单记忆模块，用于保存用户偏好、任务记录或项目状态。

后续计划用于支持：

- 用户长期学习目标
- 当前处理项目
- 常用输出格式
- 历史问答记录
- 个性化 Agent 行为

---

## 6. 快速开始

### 6.1 克隆项目

```bash
git clone https://github.com/w1016445161-netizen/docflow-agent.git
cd docflow-agent
```

---

## 7. 后端运行方式

### 7.1 创建虚拟环境

在项目根目录执行：

```bash
python -m venv .venv
```

Windows PowerShell 激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果遇到 PowerShell 执行策略限制，可以使用：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

### 7.2 安装后端依赖

进入后端目录：

```bash
cd backend
```

安装依赖：

```bash
pip install -r requirements.txt
```

---

### 7.3 配置环境变量

在 `backend` 目录下创建 `.env` 文件。

示例：

```env
LLM_MODE=mock

OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

当前默认推荐使用：

```env
LLM_MODE=mock
```

这样即使没有真实 API Key，也可以先测试项目流程。

当需要接入真实大模型 API 时，可以改为：

```env
LLM_MODE=openai
```

注意：

```text
.env 文件不要上传到 GitHub。
```

---

### 7.4 启动后端服务

在 `backend` 目录下执行：

```bash
uvicorn main:app --reload
```

启动成功后访问：

```text
http://127.0.0.1:8000/docs
```

FastAPI 会自动生成接口调试页面。

---

## 8. 前端运行方式

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动前端：

```bash
npm run dev
```

默认访问地址：

```text
http://localhost:5173
```

---

## 9. API 接口说明

后端启动后可以通过以下地址查看接口文档：

```text
http://127.0.0.1:8000/docs
```

---

### 9.1 健康检查

```http
GET /health
```

用于检查后端服务是否正常运行。

示例返回：

```json
{
  "status": "ok",
  "message": "DocFlow-Agent backend is running."
}
```

---

### 9.2 上传文档

```http
POST /upload
```

功能：

上传文档并解析内容，系统会生成对应的 `doc_id`。

当前支持格式：

```text
.pdf
.docx
.txt
.md
```

示例返回：

```json
{
  "message": "文档上传并解析成功",
  "doc_id": "example-doc-id",
  "filename": "example.pdf",
  "total_chars": 12000,
  "total_chunks": 16
}
```

---

### 9.3 文档问答

```http
POST /ask
```

请求示例：

```json
{
  "doc_id": "example-doc-id",
  "question": "这份文档主要讲了什么？"
}
```

示例返回：

```json
{
  "doc_id": "example-doc-id",
  "filename": "example.pdf",
  "question": "这份文档主要讲了什么？",
  "answer": "这里是系统生成的回答",
  "related_chunks": [],
  "report_path": "storage/outputs/example-doc-id_report.md"
}
```

---

### 9.4 查询文档信息

```http
GET /documents/{doc_id}
```

功能：

根据 `doc_id` 查询文档基础信息。

---

## 10. 使用流程示例

### 第一步：启动后端

```bash
cd backend
uvicorn main:app --reload
```

---

### 第二步：打开接口页面

```text
http://127.0.0.1:8000/docs
```

---

### 第三步：上传文档

在 `/upload` 接口上传 PDF、Word、TXT 或 Markdown 文件。

上传成功后复制返回的 `doc_id`。

---

### 第四步：向文档提问

在 `/ask` 接口中输入：

```json
{
  "doc_id": "你的 doc_id",
  "question": "这份文档的主要内容是什么？"
}
```

---

### 第五步：查看报告

系统会在下面目录生成 Markdown 报告：

```text
backend/storage/outputs/
```

---

## 11. 当前版本说明

当前版本主要用于验证 DocFlow-Agent 的基础工程链路，重点不是实现复杂 Agent，而是先跑通一个真实可扩展的文档处理流程。

当前能力：

```text
文档上传
文档解析
文本切分
基础检索
Mock 模式回答
Markdown 报告生成
前端项目骨架
```

当前限制：

```text
暂未完成正式前端交互页面
暂未接入稳定的真实大模型 API
暂未实现向量数据库检索
暂未实现完整多轮 Agent 工作流
暂未实现用户登录和权限管理
```

---

## 12. Roadmap

### v0.1 Prototype

- [x] 创建项目基础结构
- [x] 搭建 FastAPI 后端
- [x] 创建 Vue 前端项目
- [x] 实现文档解析模块
- [x] 实现文本切分模块
- [x] 实现简易检索模块
- [x] 实现 Mock 模式 LLM 调用
- [x] 实现 Markdown 报告生成

---

### v0.2 Basic Agent

- [ ] 接入真实大模型 API
- [ ] 完成前端文件上传页面
- [ ] 完成前端文档问答页面
- [ ] 展示相关文档片段
- [ ] 支持报告下载
- [ ] 增加错误提示和加载状态

---

### v0.3 RAG Version

- [ ] 接入 Embedding 模型
- [ ] 使用 FAISS 或 Chroma 实现向量检索
- [ ] 优化长文档问答效果
- [ ] 增加回答引用来源
- [ ] 降低大模型幻觉

---

### v0.4 Tool-Calling Agent

- [ ] 增加工具调用流程
- [ ] 支持表格分析工具
- [ ] 支持图表生成工具
- [ ] 支持报告生成工具
- [ ] 增加 Agent 执行日志

---

### v0.5 Project Demo

- [ ] 增加项目截图
- [ ] 增加演示视频
- [ ] 完善部署文档
- [ ] 完善简历项目描述
- [ ] 整理项目复盘文档

---

## 13. 适用场景

DocFlow-Agent 适合以下场景：

- 学生整理课程资料
- 自动生成实验报告初稿
- 阅读论文或学习笔记
- 分析项目 README
- 整理简历项目材料
- 对上传文档进行问答
- 对表格数据进行基础分析
- 生成 Markdown 总结报告

---

## 14. 项目亮点

相比普通聊天机器人，本项目更关注真实任务处理流程。

主要特点：

- 支持真实文档输入
- 支持文档解析和切分
- 支持基于文档片段的问答
- 支持 Markdown 报告文件生成
- 后端模块化设计，便于后续扩展
- 前后端分离结构
- 预留 RAG、工具调用、多文档和记忆模块

---

## 15. 后续优化方向

后续将从以下方向继续完善：

1. 前端交互优化  
   完成文件上传、问答输入、回答展示、报告下载等页面。

2. RAG 检索升级  
   使用 Embedding 和向量数据库替代当前的关键词检索。

3. 工具调用增强  
   将文档解析、表格分析、图表生成、报告生成封装为 Agent 工具。

4. 多文档问答  
   支持多个文档之间的联合检索和综合回答。

5. 结果可解释性  
   回答时展示引用片段，说明答案来源。

6. 项目工程化  
   增加日志、异常处理、配置管理、测试用例和部署文档。

---

## 16. 开发者

Author: `w1016445161-netizen`

GitHub: https://github.com/w1016445161-netizen

---

## 17. License

This project is currently for learning and prototype development.

A formal open-source license may be added in future versions.
