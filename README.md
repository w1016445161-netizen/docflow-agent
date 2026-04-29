# DocFlow-Agent

DocFlow-Agent 是一个面向学习、实验报告、课程文档和项目资料整理的 AI 文档处理 Agent 原型项目。

当前项目处于 v0.1 开发阶段，目标是实现文档上传、文档解析、文本切分、相关片段检索、基于大模型的文档问答，以及 Markdown 报告生成。

## 当前进度

- 已完成项目基础目录搭建
- 已配置 Python 虚拟环境和依赖文件
- 已搭建 FastAPI 后端基础结构
- 已实现文档解析、文本切分、简易检索、Mock 模式 LLM 调用和报告生成模块
- 已创建 Vue 前端项目骨架，后续将继续完善上传、问答和结果展示页面

## 技术栈

- Python
- FastAPI
- pypdf
- python-docx
- OpenAI-compatible API
- Vue 3
- Element Plus

## 项目功能规划

1. 支持 PDF、Word、TXT、Markdown 文档上传与解析
2. 支持长文档切分和相关片段检索
3. 支持基于文档内容的问答
4. 支持自动生成 Markdown 文档问答报告
5. 后续计划接入真实大模型 API 和 RAG 向量检索

## 后续计划

- 接入真实大模型 API
- 完成 Vue 前端上传和文档问答页面
- 增加 RAG 向量检索能力
- 支持文档总结和 Markdown 报告导出
- 增加 Agent 工具调用日志
- 完善项目演示截图和部署说明
