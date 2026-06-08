<template>
  <div class="min-h-screen bg-[#0a0a0a] text-gray-100">
    <header class="border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl">
      <div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-4 sm:px-6">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15 ring-1 ring-accent/30">
            <Upload class="h-4 w-4 text-accent" />
          </div>
          <div>
            <h1 class="text-sm font-semibold">文档导入服务</h1>
            <p class="text-xs text-gray-500">PDF / MD → 解析 → 切分 → 向量化 → 入库</p>
          </div>
        </div>
        <a
          href="http://127.0.0.1:8001/chat.html"
          class="text-xs text-gray-500 transition hover:text-accent"
        >
          前往智能智库 →
        </a>
      </div>
    </header>

    <main class="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <!-- 上传区 -->
      <section
        :class="[
          'relative rounded-2xl border-2 border-dashed p-10 text-center transition',
          isDragging
            ? 'border-accent bg-accent/5'
            : 'border-white/10 bg-[#111] hover:border-white/20',
        ]"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".pdf,.md,.markdown,.txt"
          class="hidden"
          @change="handleFileSelect"
        />
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 ring-1 ring-accent/20">
          <FileUp class="h-7 w-7 text-accent" />
        </div>
        <h2 class="mb-2 text-lg font-medium">拖拽文件到此处，或点击选择</h2>
        <p class="mb-6 text-sm text-gray-500">支持 PDF、Markdown 等格式，可多文件批量上传</p>
        <button
          class="rounded-xl bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-500"
          :disabled="isUploading"
          @click="fileInput?.click()"
        >
          选择文件
        </button>
      </section>

      <!-- 待上传文件列表 -->
      <section v-if="pendingFiles.length" class="mt-6 animate-fade-in">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-sm font-medium text-gray-300">待上传 ({{ pendingFiles.length }})</h3>
          <button
            class="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:opacity-50"
            :disabled="isUploading"
            @click="startUpload"
          >
            <span v-if="isUploading" class="flex items-center gap-2">
              <Loader2 class="h-4 w-4 animate-spin" /> 上传中...
            </span>
            <span v-else>开始导入</span>
          </button>
        </div>
        <ul class="space-y-2">
          <li
            v-for="(file, idx) in pendingFiles"
            :key="idx"
            class="flex items-center justify-between rounded-xl border border-white/6 bg-[#111] px-4 py-3"
          >
            <div class="flex items-center gap-3 min-w-0">
              <FileText class="h-4 w-4 shrink-0 text-gray-500" />
              <span class="truncate text-sm">{{ file.name }}</span>
              <span class="shrink-0 text-xs text-gray-600">{{ formatSize(file.size) }}</span>
            </div>
            <button class="text-gray-600 transition hover:text-red-400" @click="removePending(idx)">
              <X class="h-4 w-4" />
            </button>
          </li>
        </ul>
      </section>

      <!-- 任务进度 -->
      <section v-if="tasks.length" class="mt-8">
        <h3 class="mb-4 text-sm font-medium text-gray-300">导入任务</h3>
        <div class="space-y-4">
          <article
            v-for="task in tasks"
            :key="task.taskId"
            class="animate-fade-in rounded-2xl border border-white/6 bg-[#111] p-5"
          >
            <div class="mb-4 flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium">{{ task.fileName }}</p>
                <p class="mt-0.5 truncate text-xs text-gray-600">{{ task.taskId }}</p>
              </div>
              <span
                :class="[
                  'shrink-0 rounded-md px-2 py-0.5 text-[11px] font-medium',
                  statusClass(task.status),
                ]"
              >
                {{ statusLabel(task.status) }}
              </span>
            </div>

            <!-- 当前运行节点 -->
            <div v-if="task.runningList?.length" class="mb-3 flex items-center gap-2 text-xs text-accent">
              <Loader2 class="h-3.5 w-3.5 animate-spin" />
              <span>{{ task.runningList.join('、') }}</span>
            </div>

            <!-- 已完成节点 -->
            <div v-if="task.doneList?.length" class="space-y-1.5">
              <p class="text-[11px] uppercase tracking-wider text-gray-600">已完成步骤</p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="(step, sIdx) in task.doneList"
                  :key="sIdx"
                  class="rounded-md bg-white/5 px-2 py-0.5 text-[11px] text-gray-400"
                >
                  {{ step }}
                </span>
              </div>
            </div>

            <!-- 进度条 -->
            <div class="mt-4">
              <div class="mb-1 flex justify-between text-[11px] text-gray-600">
                <span>进度</span>
                <span>{{ taskProgress(task) }}%</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-white/5">
                <div
                  class="h-full rounded-full bg-gradient-to-r from-accent/70 to-accent transition-all duration-500"
                  :style="{ width: `${taskProgress(task)}%` }"
                />
              </div>
            </div>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FileText, FileUp, Loader2, Upload, X } from 'lucide-vue-next'
import { pollTaskStatus, uploadFiles } from './api'

const TOTAL_STEPS = 8

const fileInput = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const pendingFiles = ref([])
const tasks = ref([])

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function handleFileSelect(e) {
  addFiles([...e.target.files])
  e.target.value = ''
}

function handleDrop(e) {
  isDragging.value = false
  addFiles([...e.dataTransfer.files])
}

function addFiles(files) {
  const allowed = files.filter((f) =>
    /\.(pdf|md|markdown|txt)$/i.test(f.name),
  )
  pendingFiles.value.push(...allowed)
}

function removePending(idx) {
  pendingFiles.value.splice(idx, 1)
}

function statusLabel(status) {
  const map = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status || '未知'
}

function statusClass(status) {
  const map = {
    pending: 'bg-gray-500/10 text-gray-400 ring-1 ring-gray-500/20',
    processing: 'bg-accent/10 text-accent ring-1 ring-accent/20',
    completed: 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20',
    failed: 'bg-red-500/10 text-red-400 ring-1 ring-red-500/20',
  }
  return map[status] || map.pending
}

function taskProgress(task) {
  if (task.status === 'completed') return 100
  if (task.status === 'failed') return 100
  const done = task.doneList?.length ?? 0
  return Math.min(Math.round((done / TOTAL_STEPS) * 100), 95)
}

async function startUpload() {
  if (!pendingFiles.value.length || isUploading.value) return
  isUploading.value = true

  try {
    const fileMap = [...pendingFiles.value]
    const result = await uploadFiles(fileMap)
    const taskIds = result.task_ids ?? []

    taskIds.forEach((taskId, idx) => {
      const task = {
        taskId,
        fileName: fileMap[idx]?.name || `文件 ${idx + 1}`,
        status: 'processing',
        doneList: [],
        runningList: [],
      }
      tasks.value.unshift(task)

      pollTaskStatus(taskId, {
        onUpdate: (data) => {
          task.status = data.status
          task.doneList = data.done_list ?? []
          task.runningList = data.running_list ?? []
        },
        onComplete: (data) => {
          task.status = data.status
          task.doneList = data.done_list ?? []
          task.runningList = []
        },
        onError: () => {
          task.status = 'failed'
        },
      })
    })

    pendingFiles.value = []
  } catch (err) {
    alert(`上传失败：${err.message}`)
  } finally {
    isUploading.value = false
  }
}
</script>
