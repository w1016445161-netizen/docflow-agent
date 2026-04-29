<template>
  <div class="chat-page">
    <div class="chat-card">
      <h1>DocFlow Agent</h1>
      <p class="subtitle">基于 FastAPI + Vue + 阿里云百炼的文档智能体</p>

      <div class="input-area">
        <textarea
          v-model="message"
          placeholder="请输入你的问题，例如：请用三句话介绍这个文档智能体项目。"
          rows="5"
        ></textarea>

        <button :disabled="loading || !message.trim()" @click="handleSend">
          {{ loading ? "模型思考中..." : "发送问题" }}
        </button>
      </div>

      <div v-if="error" class="error-box">
        {{ error }}
      </div>

      <div v-if="answer" class="answer-box">
        <h2>模型回复</h2>

        <div class="answer-text" v-html="renderedAnswer"></div>

        <div v-if="usage" class="usage-box">
          <span>模型：{{ model }}</span>
          <span>输入 Token：{{ usage.prompt_tokens }}</span>
          <span>输出 Token：{{ usage.completion_tokens }}</span>
          <span>总 Token：{{ usage.total_tokens }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import MarkdownIt from "markdown-it";
import { sendChatMessage } from "../api/chat";

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
});

const message = ref("");
const answer = ref("");
const model = ref("");
const usage = ref(null);
const loading = ref(false);
const error = ref("");

const renderedAnswer = computed(() => {
  return md.render(answer.value || "");
});

async function handleSend() {
  if (!message.value.trim()) {
    return;
  }

  loading.value = true;
  error.value = "";
  answer.value = "";
  model.value = "";
  usage.value = null;

  try {
    const result = await sendChatMessage(message.value);

    model.value = result.model;
    answer.value = result.content;
    usage.value = result.usage;
  } catch (err) {
    error.value = err.message || "请求失败，请检查后端服务是否启动。";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.chat-page {
  min-height: 100vh;
  background: #f5f7fb;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 60px 20px;
}

.chat-card {
  width: 100%;
  max-width: 860px;
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

.input-area {
  margin-top: 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

textarea {
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

textarea:focus {
  border-color: #2563eb;
}

button {
  width: 140px;
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

.answer-box {
  margin-top: 28px;
  padding: 22px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.answer-box h2 {
  margin: 0 0 12px 0;
  font-size: 20px;
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

.answer-text :deep(pre) {
  background: #111827;
  color: #f9fafb;
  padding: 14px;
  border-radius: 10px;
  overflow-x: auto;
  line-height: 1.6;
}

.answer-text :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.usage-box {
  margin-top: 18px;
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

.error-box {
  margin-top: 20px;
  padding: 14px;
  border-radius: 10px;
  background: #fef2f2;
  color: #b91c1c;
}
</style>