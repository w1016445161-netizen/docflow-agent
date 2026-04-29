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

        <button :disabled="loading || !selectedFile" @click="handleSummarize">
          {{ loading ? "正在解析与总结..." : "上传并生成摘要" }}
        </button>
      </div>

      <div v-if="error" class="error-box">
        {{ error }}
      </div>

      <div v-if="result" class="result-box">
        <h2>文档摘要结果</h2>

        <div class="meta-box">
          <span>文件名：{{ result.filename }}</span>
          <span>类型：{{ result.file_type }}</span>
          <span>字符数：{{ result.char_count }}</span>
          <span v-if="result.is_truncated">已截断输入</span>
          <span v-else>全文输入</span>
        </div>

        <div class="summary-text" v-html="renderedSummary"></div>

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
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import MarkdownIt from "markdown-it";
import { summarizeDocument } from "../api/document";

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
});

const selectedFile = ref(null);
const loading = ref(false);
const error = ref("");
const result = ref(null);

const renderedSummary = computed(() => {
  if (!result.value) {
    return "";
  }

  return md.render(result.value.summary || "");
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

  try {
    result.value = await summarizeDocument(selectedFile.value);
  } catch (err) {
    error.value = err.message || "文档摘要生成失败，请检查后端服务。";
  } finally {
    loading.value = false;
  }
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
</style>