<template>
  <div class="flex h-screen overflow-hidden bg-[#0a0a0a] text-gray-100">
    <!-- 移动端遮罩 -->
    <Transition name="fade">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        @click="sidebarOpen = false"
      />
    </Transition>

    <!-- 侧边栏 -->
    <aside
      :class="[
        'fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col border-r border-white/5 bg-[#0d0d0d] transition-transform duration-300 lg:static lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full',
      ]"
    >
      <div class="flex items-center gap-3 border-b border-white/5 px-5 py-5">
        <div
          class="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15 ring-1 ring-accent/30"
        >
          <Sparkles class="h-4.5 w-4.5 text-accent" :stroke-width="2" />
        </div>
        <div class="min-w-0 flex-1">
          <h1 class="truncate text-sm font-semibold tracking-tight">SyntheRank AI</h1>
          <p class="truncate text-xs text-gray-500">多路重排智能智库</p>
        </div>
        <button
          class="rounded-lg p-1.5 text-gray-500 transition hover:bg-white/5 hover:text-gray-300 lg:hidden"
          @click="sidebarOpen = false"
        >
          <X class="h-4 w-4" />
        </button>
      </div>

      <button
        class="mx-3 mt-4 flex items-center gap-2 rounded-xl border border-white/8 bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-gray-200 transition hover:border-accent/30 hover:bg-accent/10 hover:text-white"
        @click="startNewChat"
      >
        <MessageSquarePlus class="h-4 w-4 text-accent" />
        新对话
      </button>

      <div class="mt-4 flex-1 overflow-y-auto px-3 pb-4">
        <p class="mb-2 px-2 text-[11px] font-medium uppercase tracking-wider text-gray-600">
          历史记录
        </p>
        <div v-if="chatHistory.length === 0" class="px-2 py-8 text-center text-xs text-gray-600">
          暂无对话，开始提问吧
        </div>
        <button
          v-for="chat in chatHistory"
          :key="chat.id"
          :class="[
            'group mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition',
            activeChatId === chat.id
              ? 'bg-accent/10 text-white ring-1 ring-accent/20'
              : 'text-gray-400 hover:bg-white/5 hover:text-gray-200',
          ]"
          @click="switchChat(chat.id)"
        >
          <MessageSquare class="h-3.5 w-3.5 shrink-0 opacity-60" />
          <span class="truncate">{{ chat.title }}</span>
        </button>
      </div>

      <div class="border-t border-white/5 px-5 py-4">
        <p class="text-[11px] text-gray-600">RAG · RRF · BGE Rerank</p>
      </div>
    </aside>

    <!-- 主区域 -->
    <main class="relative flex min-w-0 flex-1 flex-col">
      <!-- 顶栏 -->
      <header
        class="flex shrink-0 items-center justify-between border-b border-white/5 bg-[#0a0a0a]/80 px-4 py-3 backdrop-blur-xl sm:px-6"
      >
        <div class="flex items-center gap-3">
          <button
            class="rounded-lg p-2 text-gray-400 transition hover:bg-white/5 hover:text-gray-200 lg:hidden"
            @click="sidebarOpen = true"
          >
            <PanelLeft class="h-4 w-4" />
          </button>
          <div>
            <h2 class="text-sm font-medium text-gray-200">
              {{ activeChat?.title || '新对话' }}
            </h2>
            <p class="text-xs text-gray-600">多路检索 · 融合重排 · 智能生成</p>
          </div>
        </div>

        <!-- 处理进度状态栏 -->
        <div
          v-if="isProcessing"
          class="hidden items-center gap-1 rounded-full border border-white/8 bg-white/[0.03] px-3 py-1.5 sm:flex"
        >
          <Loader2 class="h-3.5 w-3.5 animate-spin text-accent" />
          <template v-for="(stage, index) in PIPELINE_STAGES" :key="stage">
            <span
              :class="[
                'text-xs transition-colors duration-300',
                pipelineIndex === index
                  ? 'font-medium text-accent'
                  : pipelineIndex > index
                    ? 'text-gray-500'
                    : 'text-gray-600',
              ]"
            >
              [{{ stage }}]
            </span>
            <ChevronRight
              v-if="index < PIPELINE_STAGES.length - 1"
              class="h-3 w-3 text-gray-700"
            />
          </template>
        </div>
      </header>

      <!-- 移动端进度条 -->
      <div
        v-if="isProcessing"
        class="flex items-center gap-2 border-b border-white/5 px-4 py-2 sm:hidden"
      >
        <Loader2 class="h-3.5 w-3.5 animate-spin text-accent" />
        <span class="text-xs text-accent">[{{ currentStage }}]</span>
      </div>

      <!-- 对话流 -->
      <div ref="chatContainer" class="flex-1 overflow-y-auto">
        <!-- 空状态 -->
        <div
          v-if="!activeChat?.messages.length"
          class="flex h-full flex-col items-center justify-center px-6 pb-32"
        >
          <div
            class="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/10 ring-1 ring-accent/20"
          >
            <Brain class="h-8 w-8 text-accent" />
          </div>
          <h3 class="mb-2 text-xl font-semibold text-gray-100">多路重排智能智库</h3>
          <p class="mb-8 max-w-md text-center text-sm text-gray-500 text-balance">
            融合本地知识库与网络搜索，经 RRF 融合与 BGE 重排，为你生成精准可溯源的回答
          </p>
          <div class="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
            <button
              v-for="hint in quickHints"
              :key="hint"
              class="rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3 text-left text-sm text-gray-400 transition hover:border-accent/20 hover:bg-accent/5 hover:text-gray-200"
              @click="submitQuestion(hint)"
            >
              {{ hint }}
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="mx-auto w-full max-w-4xl px-4 py-6 pb-36 sm:px-6">
          <div
            v-for="(msg, idx) in activeChat.messages"
            :key="idx"
            class="animate-slide-up mb-8"
          >
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div
                class="max-w-[85%] rounded-2xl rounded-br-md bg-accent px-4 py-3 text-sm leading-relaxed text-white shadow-glow sm:max-w-[75%]"
              >
                {{ msg.content }}
              </div>
            </div>

            <!-- AI 回答 -->
            <div v-else class="flex gap-3">
              <div
                class="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/10 ring-1 ring-accent/20"
              >
                <Bot class="h-4 w-4 text-accent" />
              </div>
              <div class="min-w-0 flex-1">
                <div
                  class="prose prose-invert prose-sm max-w-none prose-headings:text-gray-100 prose-p:text-gray-300 prose-strong:text-gray-100 prose-code:rounded prose-code:bg-white/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-accent prose-pre:bg-[#141414] prose-pre:ring-1 prose-pre:ring-white/5 prose-li:text-gray-300"
                  v-html="renderMarkdown(msg.content)"
                />

                <!-- 多路溯源展示区 -->
                <div v-if="msg.sources?.length" class="mt-5">
                  <div class="mb-3 flex items-center gap-2">
                    <Layers class="h-4 w-4 text-gray-500" />
                    <span class="text-xs font-medium uppercase tracking-wider text-gray-500">
                      检索溯源 · Top {{ msg.sources.length }}
                    </span>
                  </div>

                  <div
                    :class="[
                      'grid gap-3',
                      msg.sources.length > 2
                        ? 'sm:grid-cols-2'
                        : 'grid-cols-1',
                    ]"
                  >
                    <article
                      v-for="(source, sIdx) in msg.sources"
                      :key="sIdx"
                      class="group rounded-xl border border-white/6 bg-[#111111] p-4 transition hover:border-accent/20 hover:bg-[#141414]"
                    >
                      <div class="mb-3 flex items-start justify-between gap-2">
                        <span
                          :class="[
                            'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium',
                            source.type === 'local'
                              ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20'
                              : 'bg-sky-500/10 text-sky-400 ring-1 ring-sky-500/20',
                          ]"
                        >
                          <Database v-if="source.type === 'local'" class="h-3 w-3" />
                          <Globe v-else class="h-3 w-3" />
                          {{ source.type === 'local' ? '本地' : '搜索' }}
                        </span>
                        <span class="text-[11px] tabular-nums text-gray-600">
                          #{{ sIdx + 1 }}
                        </span>
                      </div>

                      <h4 class="mb-2 line-clamp-2 text-sm font-medium leading-snug text-gray-200 group-hover:text-white">
                        {{ source.title }}
                      </h4>

                      <div class="mb-3">
                        <div class="mb-1 flex items-center justify-between text-[11px]">
                          <span class="text-gray-600">相关性</span>
                          <span class="font-medium tabular-nums text-accent">
                            {{ formatScore(source.score) }}
                          </span>
                        </div>
                        <div class="h-1.5 overflow-hidden rounded-full bg-white/5">
                          <div
                            class="h-full rounded-full bg-gradient-to-r from-accent/70 to-accent transition-all duration-700"
                            :style="{ width: `${normalizeScore(source.score)}%` }"
                          />
                        </div>
                      </div>

                      <p class="line-clamp-3 text-xs leading-relaxed text-gray-500">
                        {{ source.content }}
                      </p>
                    </article>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载中占位 -->
          <div v-if="isProcessing" class="flex gap-3 animate-fade-in">
            <div
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/10 ring-1 ring-accent/20"
            >
              <Bot class="h-4 w-4 text-accent" />
            </div>
            <div class="flex items-center gap-2 rounded-2xl border border-white/5 bg-[#111] px-4 py-3">
              <span class="flex gap-1">
                <span class="h-2 w-2 animate-pulse-soft rounded-full bg-accent" />
                <span class="h-2 w-2 animate-pulse-soft rounded-full bg-accent [animation-delay:0.2s]" />
                <span class="h-2 w-2 animate-pulse-soft rounded-full bg-accent [animation-delay:0.4s]" />
              </span>
              <span class="text-sm text-gray-500">{{ currentStage }}...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部悬浮输入框 -->
      <div class="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a]/95 to-transparent px-4 pb-5 pt-10 sm:px-6">
        <div class="pointer-events-auto mx-auto max-w-3xl">
          <form
            class="flex items-end gap-2 rounded-2xl border border-white/10 bg-[#141414]/90 p-2 shadow-input backdrop-blur-xl transition focus-within:border-accent/40 focus-within:ring-1 focus-within:ring-accent/20"
            @submit.prevent="submitQuestion()"
          >
            <textarea
              ref="inputRef"
              v-model="inputText"
              rows="1"
              placeholder="输入你的问题，Enter 发送，Shift+Enter 换行..."
              class="max-h-36 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-gray-100 placeholder-gray-600 outline-none"
              :disabled="isProcessing"
              @keydown="handleKeydown"
              @input="autoResize"
            />
            <button
              type="submit"
              :disabled="!inputText.trim() || isProcessing"
              :class="[
                'mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition',
                inputText.trim() && !isProcessing
                  ? 'bg-accent text-white hover:bg-blue-500'
                  : 'bg-white/5 text-gray-600 cursor-not-allowed',
              ]"
            >
              <Send v-if="!isProcessing" class="h-4 w-4" />
              <Loader2 v-else class="h-4 w-4 animate-spin" />
            </button>
          </form>
          <p class="mt-2 text-center text-[11px] text-gray-600">
            SyntheRank AI · 本地知识库 + 网络搜索 · 多路重排
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { marked } from 'marked'
import { streamQuery } from './api'
import {
  Bot,
  Brain,
  ChevronRight,
  Database,
  Globe,
  Layers,
  Loader2,
  MessageSquare,
  MessageSquarePlus,
  PanelLeft,
  Send,
  Sparkles,
  X,
} from 'lucide-vue-next'

const STORAGE_KEY = 'synthe_rank_chat_history'
const PIPELINE_STAGES = ['检索中', 'RRF融合', 'BGE重排', '智能生成']

const STAGE_KEYWORDS = [
  { stage: '检索中', keys: ['搜索', '切片', '知识图谱', '多路', '合并', '确认'] },
  { stage: 'RRF融合', keys: ['倒排融合', '融合'] },
  { stage: 'BGE重排', keys: ['重排序', '重排'] },
  { stage: '智能生成', keys: ['生成答案', '答案'] },
]

marked.setOptions({
  breaks: true,
  gfm: true,
})

const sidebarOpen = ref(false)
const inputText = ref('')
const inputRef = ref(null)
const chatContainer = ref(null)
const isProcessing = ref(false)
const pipelineIndex = ref(-1)
const currentStage = ref('')
const chatHistory = ref([])
const activeChatId = ref(null)

const quickHints = [
  'HAK 180 烫金机局部转印如何设置？',
  '多路检索 RRF 融合的原理是什么？',
  'BGE 重排模型如何提升检索精度？',
  '本地知识库与网络搜索如何协同？',
]

const activeChat = computed(() =>
  chatHistory.value.find((c) => c.id === activeChatId.value) ?? null,
)

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      chatHistory.value = Array.isArray(data) ? data : []
    }
  } catch {
    chatHistory.value = []
  }
}

function saveHistory() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistory.value))
}

function generateId() {
  return `chat_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function startNewChat() {
  const id = generateId()
  const chat = {
    id,
    title: '新对话',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
  chatHistory.value.unshift(chat)
  activeChatId.value = id
  sidebarOpen.value = false
  saveHistory()
}

function switchChat(id) {
  activeChatId.value = id
  sidebarOpen.value = false
  scrollToBottom()
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function formatScore(score) {
  const pct = normalizeScore(score)
  return `${pct.toFixed(1)}%`
}

function normalizeScore(score) {
  const val = Number(score)
  if (Number.isNaN(val)) return 0
  return val <= 1 ? val * 100 : Math.min(val, 100)
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 144)}px`
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submitQuestion()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function resolvePipelineStage(runningList = [], doneList = []) {
  const active = runningList.at(-1) || doneList.at(-1) || ''
  for (let i = 0; i < STAGE_KEYWORDS.length; i++) {
    if (STAGE_KEYWORDS[i].keys.some((k) => active.includes(k))) {
      return i
    }
  }
  if (doneList.length === 0) return 0
  if (doneList.some((d) => d.includes('重排'))) return 2
  if (doneList.some((d) => d.includes('融合'))) return 1
  return Math.min(Math.floor(doneList.length / 2), PIPELINE_STAGES.length - 1)
}

function updatePipelineFromProgress(payload = {}) {
  const { running_list: runningList = [], done_list: doneList = [] } = payload
  const idx = resolvePipelineStage(runningList, doneList)
  pipelineIndex.value = idx
  currentStage.value = runningList.at(-1) || PIPELINE_STAGES[idx]
}

/** 对接 query_service：POST /query + SSE /stream/{session_id} */
async function askQuestion(question, sessionId, onStreamDelta) {
  return streamQuery(question, sessionId, {
    onProgress: updatePipelineFromProgress,
    onDelta: (_delta, full) => onStreamDelta?.(full),
  })
}

async function submitQuestion(text) {
  const question = (text ?? inputText.value).trim()
  if (!question || isProcessing.value) return

  if (!activeChatId.value) {
    startNewChat()
  }

  const chat = chatHistory.value.find((c) => c.id === activeChatId.value)
  if (!chat) return

  if (chat.messages.length === 0) {
    chat.title = question.length > 24 ? `${question.slice(0, 24)}...` : question
  }

  chat.messages.push({ role: 'user', content: question, timestamp: Date.now() })
  inputText.value = ''
  autoResize()
  saveHistory()
  scrollToBottom()

  isProcessing.value = true
  pipelineIndex.value = 0
  currentStage.value = PIPELINE_STAGES[0]

  const assistantMsg = {
    role: 'assistant',
    content: '',
    sources: [],
    timestamp: Date.now(),
  }
  chat.messages.push(assistantMsg)

  try {
    const result = await askQuestion(question, chat.id, (partial) => {
      assistantMsg.content = partial
      scrollToBottom()
    })
    assistantMsg.content = result.answer
    assistantMsg.sources = result.sources ?? []
    if (result.sessionId && result.sessionId !== chat.id) {
      const oldId = chat.id
      chat.id = result.sessionId
      if (activeChatId.value === oldId) activeChatId.value = result.sessionId
    }
    chat.updatedAt = Date.now()
    saveHistory()
  } catch (err) {
    assistantMsg.content = `抱歉，处理请求时发生错误：${err.message}`
    saveHistory()
  } finally {
    isProcessing.value = false
    pipelineIndex.value = -1
    currentStage.value = ''
    scrollToBottom()
  }
}

onMounted(() => {
  loadHistory()
  if (chatHistory.value.length > 0) {
    activeChatId.value = chatHistory.value[0].id
  }
})

watch(
  () => activeChat.value?.messages.length,
  () => scrollToBottom(),
)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

:deep(.prose table) {
  font-size: 0.8rem;
}
:deep(.prose th),
:deep(.prose td) {
  border-color: rgba(255, 255, 255, 0.08);
  padding: 0.4rem 0.75rem;
}
:deep(.prose blockquote) {
  border-left-color: #3b82f6;
  color: #9ca3af;
}
</style>
