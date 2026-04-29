<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE = 'http://127.0.0.1:8000'

const selectedFile = ref(null)
const uploadResult = ref(null)

const documents = ref([])
const selectedDocId = ref('')
const question = ref('这份文档主要讲了什么？')
const askResult = ref(null)

const memoryKey = ref('current_project')
const memoryValue = ref('DocFlow-Agent，一个面向文档处理和办公自动化的 AI 智能体项目')
const memoryData = ref(null)

const compareDocIds = ref([])
const compareQuestion = ref('请比较这些文档的主要内容、共同点和差异点。')
const compareResult = ref(null)

const loadingUpload = ref(false)
const loadingAsk = ref(false)
const loadingDocs = ref(false)
const loadingMemory = ref(false)
const loadingCompare = ref(false)

const selectedDoc = computed(() => {
  return documents.value.find(item => item.doc_id === selectedDocId.value)
})

function handleFileChange(event) {
  selectedFile.value = event.target.files[0]
}

function chartUrl(path) {
  if (!path) return ''

  let normalized = String(path).replaceAll('\\', '/')

  if (normalized.startsWith('storage/outputs/')) {
    normalized = normalized.replace('storage/outputs/', '')
  }

  if (normalized.startsWith('/outputs/')) {
    return `${API_BASE}${normalized}`
  }

  if (normalized.startsWith('outputs/')) {
    return `${API_BASE}/${normalized}`
  }

  return `${API_BASE}/outputs/${normalized}`
}

async function checkHealth() {
  try {
    const res = await axios.get(`${API_BASE}/health`)
    ElMessage.success(res.data.message || '后端连接成功')
  } catch (error) {
    ElMessage.error('无法连接后端，请确认 uvicorn main:app --reload 正在运行')
  }
}

async function loadDocuments() {
  loadingDocs.value = true

  try {
    const res = await axios.get(`${API_BASE}/documents`)
    documents.value = res.data.documents || []
  } catch (error) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loadingDocs.value = false
  }
}

async function uploadDocument() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择一个文件')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  loadingUpload.value = true

  try {
    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    uploadResult.value = res.data

    if (res.data.error) {
      ElMessage.error(res.data.error)
      return
    }

    ElMessage.success('上传并解析成功')

    await loadDocuments()

    if (res.data.doc_id) {
      selectedDocId.value = res.data.doc_id
    }
  } catch (error) {
    ElMessage.error('上传失败，请检查后端是否运行')
  } finally {
    loadingUpload.value = false
  }
}

async function askDocument() {
  if (!selectedDocId.value) {
    ElMessage.warning('请先选择一个文档')
    return
  }

  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  loadingAsk.value = true

  try {
    const res = await axios.post(`${API_BASE}/ask`, {
      doc_id: selectedDocId.value,
      question: question.value
    })

    askResult.value = res.data

    if (res.data.error) {
      ElMessage.error(res.data.error)
      return
    }

    ElMessage.success('问答完成')
  } catch (error) {
    ElMessage.error('提问失败')
  } finally {
    loadingAsk.value = false
  }
}

async function saveMemory() {
  if (!memoryKey.value.trim() || !memoryValue.value.trim()) {
    ElMessage.warning('key 和 value 都不能为空')
    return
  }

  loadingMemory.value = true

  try {
    const res = await axios.post(`${API_BASE}/memory`, {
      key: memoryKey.value,
      value: memoryValue.value
    })

    memoryData.value = res.data.memory
    ElMessage.success('记忆保存成功')
  } catch (error) {
    ElMessage.error('保存记忆失败')
  } finally {
    loadingMemory.value = false
  }
}

async function loadMemory() {
  loadingMemory.value = true

  try {
    const res = await axios.get(`${API_BASE}/memory`)
    memoryData.value = res.data
  } catch (error) {
    ElMessage.error('读取记忆失败')
  } finally {
    loadingMemory.value = false
  }
}

async function compareDocuments() {
  if (compareDocIds.value.length < 2) {
    ElMessage.warning('请至少选择两个文档进行对比')
    return
  }

  loadingCompare.value = true

  try {
    const res = await axios.post(`${API_BASE}/compare`, {
      doc_ids: compareDocIds.value,
      question: compareQuestion.value
    })

    compareResult.value = res.data

    if (res.data.error) {
      ElMessage.error(res.data.error)
      return
    }

    ElMessage.success('多文档对比完成')
  } catch (error) {
    ElMessage.error('多文档对比失败')
  } finally {
    loadingCompare.value = false
  }
}

onMounted(async () => {
  await checkHealth()
  await loadDocuments()
  await loadMemory()
})
</script>

<template>
  <div class="page">
    <div class="header">
      <div class="header-title">DocFlow-Agent</div>
      <div class="header-subtitle">
        面向文档处理、Excel 分析、图表生成、多文档对比和用户记忆的 AI 智能体前端界面
      </div>
    </div>

    <div class="grid">
      <el-card class="card">
        <div class="card-title">1. 上传文档</div>

        <div class="row">
          <input
            type="file"
            accept=".pdf,.docx,.txt,.md,.xlsx,.xls"
            @change="handleFileChange"
          />

          <el-button
            type="primary"
            :loading="loadingUpload"
            @click="uploadDocument"
          >
            上传并解析
          </el-button>
        </div>

        <div class="hint">
          支持 PDF、Word、TXT、Markdown、Excel。Excel 会自动生成表格分析和图表。
        </div>

        <div v-if="uploadResult" class="block">
          <div class="answer-box">
            <strong>上传结果：</strong>
            <div>文件名：{{ uploadResult.filename }}</div>
            <div>doc_id：{{ uploadResult.doc_id }}</div>
            <div>文件类型：{{ uploadResult.file_type }}</div>
            <div>文本长度：{{ uploadResult.total_chars }}</div>
            <div>片段数量：{{ uploadResult.total_chunks }}</div>
          </div>

          <div
            v-if="uploadResult.chart_paths && uploadResult.chart_paths.length"
            class="block"
          >
            <strong>自动生成图表：</strong>
            <div class="chart-list mt">
              <img
                v-for="path in uploadResult.chart_paths"
                :key="path"
                class="chart-img"
                :src="chartUrl(path)"
                alt="chart"
              />
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="card">
        <div class="card-title">2. 文档列表</div>

        <div class="row mb">
          <el-button :loading="loadingDocs" @click="loadDocuments">
            刷新文档列表
          </el-button>
        </div>

        <el-table
          :data="documents"
          height="300"
          border
          size="small"
        >
          <el-table-column prop="filename" label="文件名" min-width="160" />
          <el-table-column prop="total_chunks" label="片段数" width="80" />
          <el-table-column label="选择" width="90">
            <template #default="{ row }">
              <el-button
                size="small"
                type="primary"
                @click="selectedDocId = row.doc_id"
              >
                选择
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="hint">
          当前选择文档：
          <strong>{{ selectedDoc ? selectedDoc.filename : '未选择' }}</strong>
        </div>
      </el-card>

      <el-card class="card full">
        <div class="card-title">3. 文档问答</div>

        <div class="row">
          <el-select
            v-model="selectedDocId"
            placeholder="选择一个文档"
            style="width: 360px"
          >
            <el-option
              v-for="doc in documents"
              :key="doc.doc_id"
              :label="doc.filename"
              :value="doc.doc_id"
            />
          </el-select>

          <el-input
            v-model="question"
            placeholder="请输入你想问的问题"
            style="flex: 1"
          />

          <el-button
            type="primary"
            :loading="loadingAsk"
            @click="askDocument"
          >
            提问
          </el-button>
        </div>

        <div v-if="askResult" class="block">
          <div class="answer-box">
            <strong>回答：</strong>
            <div class="mt">{{ askResult.answer }}</div>
          </div>

          <div class="hint">
            报告路径：{{ askResult.report_path }}
          </div>

          <el-collapse class="mt">
            <el-collapse-item title="查看检索到的相关片段">
              <div
                v-for="chunk in askResult.related_chunks"
                :key="chunk.chunk_id"
                class="code-box mb"
              >
                chunk_id: {{ chunk.chunk_id }}
                score: {{ chunk.score }}

                {{ chunk.text }}
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-card>

      <el-card class="card">
        <div class="card-title">4. 用户记忆</div>

        <el-input
          v-model="memoryKey"
          placeholder="记忆 key，例如 current_project"
          class="mb"
        />

        <el-input
          v-model="memoryValue"
          type="textarea"
          :rows="3"
          placeholder="记忆内容"
          class="mb"
        />

        <div class="row">
          <el-button
            type="primary"
            :loading="loadingMemory"
            @click="saveMemory"
          >
            保存记忆
          </el-button>

          <el-button
            :loading="loadingMemory"
            @click="loadMemory"
          >
            查看记忆
          </el-button>
        </div>

        <div v-if="memoryData" class="block">
          <div class="code-box">
            {{ JSON.stringify(memoryData, null, 2) }}
          </div>
        </div>
      </el-card>

      <el-card class="card">
        <div class="card-title">5. 多文档对比</div>

        <el-select
          v-model="compareDocIds"
          multiple
          placeholder="选择至少两个文档"
          style="width: 100%"
          class="mb"
        >
          <el-option
            v-for="doc in documents"
            :key="doc.doc_id"
            :label="doc.filename"
            :value="doc.doc_id"
          />
        </el-select>

        <el-input
          v-model="compareQuestion"
          type="textarea"
          :rows="3"
          placeholder="输入对比问题"
          class="mb"
        />

        <el-button
          type="primary"
          :loading="loadingCompare"
          @click="compareDocuments"
        >
          开始对比
        </el-button>

        <div v-if="compareResult" class="block">
          <div class="answer-box">
            <strong>对比结果：</strong>
            <div class="mt">{{ compareResult.answer }}</div>
          </div>

          <el-collapse class="mt">
            <el-collapse-item title="查看多文档上下文">
              <div
                v-for="(ctx, index) in compareResult.contexts"
                :key="index"
                class="code-box mb"
              >
                文件：{{ ctx.filename }}
                chunk_id: {{ ctx.chunk_id }}

                {{ ctx.text }}
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-card>
    </div>
  </div>
</template>