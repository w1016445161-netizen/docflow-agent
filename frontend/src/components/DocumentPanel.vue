<template>
  <div class="document-page">
    <div class="document-card">
      <h1>DocFlow Agent</h1>
      <p class="subtitle">上传 TXT / PDF 文档，自动解析并生成结构化摘要</p>

      <div class="upload-box">
        <input
          type="file"
          accept=".txt,.pdf"
          @change="handleFileChange"
        />

        <div v-if="selectedFile" class="file-info">
          <p><strong>已选择文件：</strong>{{ selectedFile.name }}</p>
          <p><strong>文件大小：</strong>{{ formatFileSize(selectedFile.size) }}</p>
        </div>

        <div class="mode-selector">
          <label class="mode-option" :class="{ active: summaryMode === 'fast' }">
            <input type="radio" v-model="summaryMode" value="fast" :disabled="loading" />
            <span class="check-mark">{{ summaryMode === 'fast' ? '✓ ' : '' }}</span>快速摘要
          </label>
          <label class="mode-option" :class="{ active: summaryMode === 'deep' }">
            <input type="radio" v-model="summaryMode" value="deep" :disabled="loading" />
            <span class="check-mark">{{ summaryMode === 'deep' ? '✓ ' : '' }}</span>深度摘要
          </label>
        </div>

        <button :disabled="loading || !selectedFile" @click="handleSummarize">
          {{ loading ? (summaryMode === 'deep' ? '深度摘要中...' : '快速摘要中...') : '上传并生成摘要' }}
        </button>
      </div>

      <div v-if="error" class="error-box">
        {{ error }}
      </div>

      <div v-if="result" class="result-box">
        <h2>文档摘要结果</h2>

        <div class="meta-box">
          <span>摘要模式：{{ result.summary_mode === 'deep' ? '深度摘要' : '快速摘要' }}</span>
          <span>文件名：{{ result.filename }}</span>
          <span>类型：{{ result.file_type }}</span>
          <span>字符数：{{ result.char_count }}</span>
          <span v-if="result.is_truncated">已截断输入</span>
          <span v-else>全文输入</span>
        </div>

        <div class="summary-text" v-html="renderedSummary"></div>

        <div class="action-bar">
          <button class="action-btn" @click="copyText(result.summary, 'summary')">
            {{ copiedSummary ? '已复制' : '复制摘要' }}
          </button>
          <button class="action-btn" @click="exportMarkdown()">
            导出 Markdown
          </button>
          <button class="action-btn" :disabled="loading" @click="handleRegenerateSummary">
            {{ loading ? '生成中...' : '重新生成摘要' }}
          </button>
        </div>

        <div v-if="result.usage" class="usage-box">
          <span>模型：{{ result.model }}</span>
          <span>输入 Token：{{ result.usage.prompt_tokens }}</span>
          <span>输出 Token：{{ result.usage.completion_tokens }}</span>
          <span>总 Token：{{ result.usage.total_tokens }}</span>
        </div>

        <details class="preview-box">
          <summary>查看提取出的前 500 字文本</summary>
          <pre>{{ result.preview }}</pre>
        </details>
      </div>

      <div v-if="docId" class="qa-section">
        <h2>基于文档提问</h2>

        <div class="qa-input-area">
          <textarea
            v-model="question"
            placeholder="请输入关于文档的问题..."
            rows="3"
          ></textarea>

          <button
            :disabled="qaLoading || !question.trim()"
            @click="handleAsk"
          >
            {{ qaLoading ? "查询中..." : "提问" }}
          </button>
        </div>

        <div class="qa-tools-bar">
          <button
            class="action-btn"
            :disabled="qaLoading || !docId"
            @click="handleQuickAsk('请基于这份文档生成一份适合学生复习的学习笔记，包括核心概念、重点知识、易混点和复习建议。')"
          >
            生成学习笔记
          </button>
          <button
            class="action-btn"
            :disabled="qaLoading || !docId"
            @click="handleQuickAsk('请从这份文档中提取可执行的任务、待办事项、后续问题或改进建议。')"
          >
            生成行动项
          </button>
        </div>

        <div v-if="qaError" class="error-box">
          {{ qaError }}
        </div>

        <div v-if="qaResult" class="qa-answer">
          <h3>回答</h3>
          <div class="answer-text" v-html="renderedAnswer"></div>

          <div class="action-bar">
            <button class="action-btn" @click="copyText(qaResult.answer, 'answer')">
              {{ copiedAnswer ? '已复制' : '复制回答' }}
            </button>
          </div>

          <details v-if="qaResult.related_chunks?.length" class="chunks-box">
            <summary>查看相关原文片段（{{ qaResult.related_chunks.length }} 段）</summary>
            <div
              v-for="(chunk, idx) in qaResult.related_chunks"
              :key="idx"
              class="chunk-item"
            >
              <div class="chunk-meta">
                <span class="chunk-id">片段 #{{ chunk.chunk_id }}</span>
                <span class="chunk-score">相关度: {{ chunk.score }}</span>
              </div>
              <pre>{{ chunk.text.substring(0, 300) }}{{ chunk.text.length > 300 ? '...' : '' }}</pre>
            </div>
          </details>
        </div>

        <div v-if="qaHistory.length" class="qa-history">
          <h3>问答历史（{{ qaHistory.length }}）</h3>
          <div v-for="(item, idx) in [...qaHistory].reverse()" :key="idx" class="history-item">
            <div class="history-q"><strong>Q:</strong> {{ item.question }}</div>
            <div class="history-a" v-html="md.render(item.answer || '')"></div>
            <details v-if="item.related_chunks?.length" class="chunks-box">
              <summary>查看相关原文片段（{{ item.related_chunks.length }} 段）</summary>
              <div v-for="(chunk, cIdx) in item.related_chunks" :key="cIdx" class="chunk-item">
                <div class="chunk-meta">
                  <span class="chunk-id">片段 #{{ chunk.chunk_id }}</span>
                  <span class="chunk-score">相关度: {{ chunk.score }}</span>
                </div>
                <pre>{{ chunk.text.substring(0, 300) }}{{ chunk.text.length > 300 ? '...' : '' }}</pre>
              </div>
            </details>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import MarkdownIt from "markdown-it";
import { summarizeDocumentStream, askQuestion } from "../api/document";

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
});

const summaryMode = ref("fast");
const selectedFile = ref(null);
const loading = ref(false);
const error = ref("");
const result = ref(null);

const docId = ref(null);
const question = ref("");
const qaLoading = ref(false);
const qaError = ref("");
const qaResult = ref(null);
const qaHistory = ref([]);
const copiedSummary = ref(false);
const copiedAnswer = ref(false);

const renderedSummary = computed(() => {
  if (!result.value) {
    return "";
  }

  return md.render(result.value.summary || "");
});

const renderedAnswer = computed(() => {
  if (!qaResult.value) {
    return "";
  }

  return md.render(qaResult.value.answer || "");
});

function handleFileChange(event) {
  const file = event.target.files[0];

  error.value = "";
  result.value = null;

  if (!file) {
    selectedFile.value = null;
    return;
  }

  const filename = file.name.toLowerCase();

  if (!filename.endsWith(".txt") && !filename.endsWith(".pdf")) {
    selectedFile.value = null;
    error.value = "暂时只支持上传 TXT 或 PDF 文件。";
    return;
  }

  selectedFile.value = file;
}

async function handleSummarize() {
  if (!selectedFile.value) {
    return;
  }

  loading.value = true;
  error.value = "";
  result.value = null;
  docId.value = null;
  question.value = "";
  qaResult.value = null;
  qaError.value = "";
  qaHistory.value = [];

  result.value = { summary: "" };

  try {
    await summarizeDocumentStream(selectedFile.value, (event) => {
      if (event.type === "meta") {
        docId.value = event.data.doc_id;
        result.value = {
          ...event.data,
          summary: "",
        };
      } else if (event.type === "delta") {
        result.value = {
          ...result.value,
          summary: (result.value.summary || "") + event.data,
        };
      } else if (event.type === "error") {
        throw new Error(event.data);
      }
    }, summaryMode.value);
  } catch (err) {
    error.value = err.message || "文档摘要生成失败，请检查后端服务。";
    result.value = null;
  } finally {
    loading.value = false;
  }
}

async function handleRegenerateSummary() {
  if (!selectedFile.value) return;
  loading.value = true;
  error.value = "";
  result.value = null;
  docId.value = null;
  qaResult.value = null;
  qaError.value = "";
  result.value = { summary: "" };
  try {
    await summarizeDocumentStream(selectedFile.value, (event) => {
      if (event.type === "meta") {
        docId.value = event.data.doc_id;
        result.value = { ...event.data, summary: "" };
      } else if (event.type === "delta") {
        result.value = {
          ...result.value,
          summary: (result.value.summary || "") + event.data,
        };
      } else if (event.type === "error") {
        throw new Error(event.data);
      }
    }, summaryMode.value);
  } catch (err) {
    error.value = err.message || "文档摘要生成失败，请检查后端服务。";
    result.value = null;
  } finally {
    loading.value = false;
  }
}

async function handleAsk() {
  if (!docId.value || !question.value.trim()) {
    return;
  }

  qaLoading.value = true;
  qaError.value = "";
  qaResult.value = null;

  try {
    qaResult.value = await askQuestion(docId.value, question.value);
    qaHistory.value.push({
      question: question.value,
      answer: qaResult.value.answer,
      related_chunks: qaResult.value.related_chunks,
    });
  } catch (err) {
    qaError.value = err.message || "提问失败，请检查后端服务。";
  } finally {
    qaLoading.value = false;
  }
}

async function handleQuickAsk(questionText) {
  if (!docId.value) return;
  qaLoading.value = true;
  qaError.value = "";
  qaResult.value = null;
  try {
    question.value = questionText;
    qaResult.value = await askQuestion(docId.value, questionText);
    qaHistory.value.push({
      question: questionText,
      answer: qaResult.value.answer,
      related_chunks: qaResult.value.related_chunks,
    });
  } catch (err) {
    qaError.value = err.message || "请求失败，请检查后端服务。";
  } finally {
    qaLoading.value = false;
  }
}

function copyText(text, target) {
  navigator.clipboard.writeText(text || "");
  if (target === "summary") {
    copiedSummary.value = true;
    setTimeout(() => (copiedSummary.value = false), 2000);
  } else if (target === "answer") {
    copiedAnswer.value = true;
    setTimeout(() => (copiedAnswer.value = false), 2000);
  }
}

function exportMarkdown() {
  if (!result.value) return;
  const r = result.value;
  const now = new Date().toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" });
  let md = `# DocFlow 文档分析报告\n\n`;
  md += `> 生成时间：${now}\n\n`;
  md += `## 文档信息\n\n`;
  md += `| 字段 | 值 |\n`;
  md += `|------|----|\n`;
  md += `| 文件名 | ${r.filename || ""} |\n`;
  md += `| 文件类型 | ${r.file_type || ""} |\n`;
  md += `| 字符数 | ${r.char_count || 0} |\n`;
  md += `| 摘要模式 | ${r.summary_mode === "deep" ? "深度摘要" : "快速摘要"} |\n`;
  md += `| 状态 | ${r.is_truncated ? "已截断输入" : "全文输入"} |\n\n`;
  md += `## 结构化摘要\n\n${r.summary || ""}\n\n`;
  if (qaHistory.value.length) {
    md += `---\n\n## 问答历史\n\n`;
    [...qaHistory.value].reverse().forEach((item, idx) => {
      md += `### Q${qaHistory.value.length - idx}: ${item.question}\n\n`;
      md += `${item.answer || ""}\n\n`;
      if (item.related_chunks?.length) {
        md += `<details>\n<summary>参考片段（${item.related_chunks.length} 段）</summary>\n\n`;
        item.related_chunks.forEach((chunk) => {
          md += `- **片段 #${chunk.chunk_id}**（相关度: ${chunk.score}）\n`;
          md += `  \`${chunk.text.substring(0, 200)}${chunk.text.length > 200 ? "..." : ""}\`\n\n`;
        });
        md += `</details>\n\n`;
      }
    });
  }
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `docflow-summary-${Date.now()}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function formatFileSize(size) {
  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(2)} KB`;
  }

  return `${(size / 1024 / 1024).toFixed(2)} MB`;
}
</script>

<style scoped>
.document-page {
  min-height: 100vh;
  background: #f5f7fb;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 60px 20px;
}

.document-card {
  width: 100%;
  max-width: 920px;
  background: #ffffff;
  border-radius: 18px;
  padding: 32px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

h1 {
  margin: 0;
  font-size: 32px;
  color: #111827;
}

.subtitle {
  margin-top: 10px;
  color: #6b7280;
  font-size: 15px;
}

.upload-box {
  margin-top: 28px;
  padding: 22px;
  border: 1px dashed #cbd5e1;
  border-radius: 14px;
  background: #f9fafb;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

input[type="file"] {
  font-size: 15px;
}

.mode-selector {
  display: flex;
  gap: 16px;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  background: #ffffff;
  font-size: 14px;
  cursor: pointer;
  color: #6b7280;
}

.mode-option input[type="radio"] {
  margin: 0;
}

.file-info {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
  color: #374151;
}

.file-info p {
  margin: 6px 0;
}

button {
  width: 170px;
  border: none;
  border-radius: 10px;
  background: #2563eb;
  color: white;
  padding: 12px 18px;
  font-size: 15px;
  cursor: pointer;
}

button:hover:not(:disabled) {
  background: #1d4ed8;
}

button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.error-box {
  margin-top: 20px;
  padding: 14px;
  border-radius: 10px;
  background: #fef2f2;
  color: #b91c1c;
}

.result-box {
  margin-top: 28px;
  padding: 24px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.result-box h2 {
  margin: 0 0 16px 0;
  font-size: 22px;
  color: #111827;
}

.meta-box {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 22px;
  font-size: 13px;
  color: #4b5563;
}

.meta-box span {
  background: #eef2ff;
  padding: 6px 10px;
  border-radius: 8px;
}

.summary-text {
  line-height: 1.8;
  color: #374151;
  font-size: 15px;
}

.summary-text :deep(h2) {
  margin-top: 24px;
  margin-bottom: 10px;
  font-size: 20px;
  color: #111827;
}

.summary-text :deep(h3) {
  margin-top: 18px;
  margin-bottom: 8px;
  font-size: 17px;
  color: #111827;
}

.summary-text :deep(p) {
  margin: 0 0 12px 0;
}

.summary-text :deep(ul),
.summary-text :deep(ol) {
  padding-left: 24px;
  margin: 10px 0;
}

.summary-text :deep(li) {
  margin: 6px 0;
}

.summary-text :deep(strong) {
  font-weight: 700;
  color: #111827;
}

.summary-text :deep(code) {
  background: #eef2ff;
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 14px;
}

.summary-text :deep(pre) {
  background: #111827;
  color: #f9fafb;
  padding: 14px;
  border-radius: 10px;
  overflow-x: auto;
  line-height: 1.6;
}

.usage-box {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: #4b5563;
}

.usage-box span {
  background: #eef2ff;
  padding: 6px 10px;
  border-radius: 8px;
}

.preview-box {
  margin-top: 22px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
}

.preview-box summary {
  cursor: pointer;
  font-weight: 600;
  color: #374151;
}

.preview-box pre {
  margin-top: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #4b5563;
  line-height: 1.6;
}

.qa-section {
  margin-top: 32px;
  padding: 24px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.qa-section h2 {
  margin: 0 0 16px 0;
  font-size: 22px;
  color: #111827;
}

.qa-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-input-area textarea {
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  padding: 14px;
  font-size: 15px;
  line-height: 1.6;
  outline: none;
  font-family: inherit;
}

.qa-input-area textarea:focus {
  border-color: #2563eb;
}

.qa-tools-bar {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.qa-answer {
  margin-top: 20px;
}

.qa-answer h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #111827;
}

.answer-text {
  line-height: 1.8;
  color: #374151;
  font-size: 15px;
}

.answer-text :deep(p) {
  margin: 0 0 12px 0;
}

.answer-text :deep(ul) {
  padding-left: 22px;
  margin: 10px 0;
}

.answer-text :deep(ol) {
  padding-left: 22px;
  margin: 10px 0;
}

.answer-text :deep(li) {
  margin: 6px 0;
}

.answer-text :deep(strong) {
  font-weight: 700;
  color: #111827;
}

.answer-text :deep(code) {
  background: #eef2ff;
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 14px;
}

.chunks-box {
  margin-top: 20px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
}

.chunks-box summary {
  cursor: pointer;
  font-weight: 600;
  color: #374151;
}

.chunk-item {
  margin-top: 12px;
  padding: 10px;
  background: #f3f4f6;
  border-radius: 8px;
}

.chunk-item pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}

.action-bar {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.action-btn {
  width: auto;
  background: #ffffff;
  color: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
}

.action-btn:active {
  background: #eff6ff;
}

.chunk-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
}

.chunk-id {
  background: #eef2ff;
  padding: 2px 8px;
  border-radius: 4px;
  color: #4f46e5;
  font-weight: 600;
}

.chunk-score {
  background: #f0fdf4;
  padding: 2px 8px;
  border-radius: 4px;
  color: #16a34a;
  font-weight: 600;
}

.qa-history {
  margin-top: 28px;
  border-top: 1px solid #e5e7eb;
  padding-top: 20px;
}

.qa-history > h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #111827;
}

.history-item {
  margin-bottom: 20px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.history-q {
  font-size: 14px;
  color: #374151;
  margin-bottom: 10px;
}

.history-a {
  line-height: 1.8;
  color: #374151;
  font-size: 15px;
}

.history-a :deep(p) {
  margin: 0 0 12px 0;
}

.history-a :deep(ul) {
  padding-left: 22px;
  margin: 10px 0;
}

.history-a :deep(ol) {
  padding-left: 22px;
  margin: 10px 0;
}

.history-a :deep(li) {
  margin: 6px 0;
}

.history-a :deep(strong) {
  font-weight: 700;
  color: #111827;
}

.history-a :deep(code) {
  background: #eef2ff;
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 14px;
}

.check-mark {
  font-weight: 700;
}

.mode-option.active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #2563eb;
  font-weight: 700;
  box-shadow: 0 0 0 1px #2563eb;
}
</style>