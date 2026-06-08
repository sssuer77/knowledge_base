<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#0a0a0f] text-zinc-100">
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
        'fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-white/5 bg-[#0f0f14] transition-transform duration-300 lg:static lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full',
      ]"
    >
      <div class="flex items-center gap-3 border-b border-white/5 px-5 py-5">
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/15 ring-1 ring-blue-500/30">
          <Sparkles class="h-5 w-5 text-blue-400" />
        </div>
        <div class="min-w-0">
          <h1 class="truncate text-sm font-semibold tracking-wide text-white">SyntheRank AI</h1>
          <p class="truncate text-xs text-zinc-500">多路重排智能智库</p>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto px-3 py-4">
        <p class="mb-2 px-2 text-[11px] font-medium uppercase tracking-wider text-zinc-600">对话历史</p>
        <div v-if="conversations.length === 0" class="px-2 py-8 text-center text-sm text-zinc-600">
          暂无对话，开始提问吧
        </div>
        <button
          v-for="conv in conversations"
          :key="conv.id"
          type="button"
          :class="[
            'group mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left transition-colors',
            conv.id === activeConversationId
              ? 'bg-blue-500/10 text-blue-100 ring-1 ring-blue-500/20'
              : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200',
          ]"
          @click="switchConversation(conv.id)"
        >
          <MessageSquare class="h-4 w-4 shrink-0 opacity-60" />
          <span class="truncate text-sm">{{ conv.title }}</span>
        </button>
      </div>

      <div class="border-t border-white/5 p-4">
        <button
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-500 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-blue-500/20 transition hover:bg-blue-400 active:scale-[0.98]"
          @click="startNewConversation"
        >
          <Plus class="h-4 w-4" />
          新对话
        </button>
      </div>
    </aside>

    <!-- 主区域 -->
    <main class="relative flex min-w-0 flex-1 flex-col">
      <!-- 顶栏 -->
      <header class="flex items-center justify-between border-b border-white/5 bg-[#0a0a0f]/80 px-4 py-3 backdrop-blur-md lg:px-6">
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="rounded-lg p-2 text-zinc-400 transition hover:bg-white/5 hover:text-white lg:hidden"
            @click="sidebarOpen = true"
          >
            <Menu class="h-5 w-5" />
          </button>
          <div>
            <h2 class="text-sm font-medium text-zinc-200">{{ activeConversation?.title || '新对话' }}</h2>
            <p class="text-xs text-zinc-600">RAG · RRF 融合 · BGE 重排</p>
          </div>
        </div>

        <!-- 处理状态 -->
        <div v-if="isProcessing" class="flex items-center gap-2">
          <Loader2 class="h-4 w-4 animate-spin text-blue-400" />
          <div class="flex items-center gap-1.5 text-xs">
            <template v-for="(stage, index) in pipelineStages" :key="stage.key">
              <span
                :class="[
                  'rounded-full px-2.5 py-1 font-medium transition-all duration-300',
                  stageIndex === index
                    ? 'bg-blue-500/20 text-blue-300 ring-1 ring-blue-500/40'
                    : stageIndex > index
                      ? 'text-zinc-500'
                      : 'text-zinc-700',
                ]"
              >
                {{ stage.label }}
              </span>
              <ChevronRight v-if="index < pipelineStages.length - 1" class="h-3 w-3 text-zinc-700" />
            </template>
          </div>
        </div>
      </header>

      <!-- 对话 + 溯源 -->
      <div class="flex min-h-0 flex-1 flex-col lg:flex-row">
        <!-- 对话流 -->
        <section class="flex min-h-0 flex-1 flex-col">
          <div ref="chatContainer" class="flex-1 overflow-y-auto px-4 py-6 lg:px-8">
            <!-- 空状态 -->
            <div
              v-if="!activeConversation?.messages.length"
              class="mx-auto flex h-full max-w-2xl flex-col items-center justify-center text-center"
            >
              <div class="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500/20 to-blue-600/5 ring-1 ring-blue-500/20">
                <Brain class="h-8 w-8 text-blue-400" />
              </div>
              <h3 class="mb-2 text-xl font-semibold text-white">多路重排智能智库</h3>
              <p class="max-w-md text-sm leading-relaxed text-zinc-500">
                融合本地知识库与联网搜索，经 RRF 融合与 BGE 重排，为你提供可溯源的智能回答。
              </p>
              <div class="mt-8 flex flex-wrap justify-center gap-2">
                <button
                  v-for="hint in quickHints"
                  :key="hint"
                  type="button"
                  class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-zinc-400 transition hover:border-blue-500/30 hover:bg-blue-500/10 hover:text-blue-200"
                  @click="submitQuery(hint)"
                >
                  {{ hint }}
                </button>
              </div>
            </div>

            <!-- 消息列表 -->
            <div v-else class="mx-auto max-w-3xl space-y-8">
              <template v-for="(msg, msgIndex) in activeConversation.messages" :key="msgIndex">
                <!-- 用户消息 -->
                <div v-if="msg.role === 'user'" class="flex justify-end">
                  <div class="max-w-[85%] rounded-2xl rounded-br-md bg-blue-500 px-4 py-3 text-sm leading-relaxed text-white shadow-lg shadow-blue-500/10">
                    {{ msg.content }}
                  </div>
                </div>

                <!-- AI 回答 -->
                <div v-else class="flex gap-3">
                  <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/15 ring-1 ring-blue-500/25">
                    <Bot class="h-4 w-4 text-blue-400" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <div
                      class="prose prose-invert prose-sm max-w-none rounded-2xl rounded-tl-md border border-white/5 bg-[#12121a] px-5 py-4 text-zinc-300"
                      v-html="renderMarkdown(msg.content)"
                    />
                    <button
                      v-if="msg.sources?.length"
                      type="button"
                      class="mt-2 flex items-center gap-1.5 text-xs text-zinc-500 transition hover:text-blue-400"
                      @click="highlightSources(msgIndex)"
                    >
                      <FileSearch class="h-3.5 w-3.5" />
                      查看 {{ msg.sources.length }} 条溯源文档
                    </button>
                  </div>
                </div>
              </template>

              <!-- 加载占位 -->
              <div v-if="isProcessing" class="flex gap-3">
                <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/15">
                  <Bot class="h-4 w-4 text-blue-400" />
                </div>
                <div class="flex items-center gap-2 rounded-2xl border border-white/5 bg-[#12121a] px-5 py-4">
                  <span class="flex gap-1">
                    <span class="h-2 w-2 animate-bounce rounded-full bg-blue-400 [animation-delay:-0.3s]" />
                    <span class="h-2 w-2 animate-bounce rounded-full bg-blue-400 [animation-delay:-0.15s]" />
                    <span class="h-2 w-2 animate-bounce rounded-full bg-blue-400" />
                  </span>
                  <span class="text-sm text-zinc-500">正在生成回答...</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部输入框 -->
          <div class="border-t border-white/5 bg-gradient-to-t from-[#0a0a0f] to-transparent px-4 pb-6 pt-4 lg:px-8">
            <div class="mx-auto max-w-3xl">
              <div
                class="flex items-end gap-2 rounded-2xl border border-white/10 bg-[#14141c] p-2 shadow-2xl shadow-black/40 ring-1 ring-white/5 transition focus-within:border-blue-500/40 focus-within:ring-blue-500/20"
              >
                <textarea
                  ref="inputRef"
                  v-model="inputText"
                  rows="1"
                  placeholder="输入你的问题，Enter 发送，Shift+Enter 换行..."
                  class="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none"
                  :disabled="isProcessing"
                  @input="autoResize"
                  @keydown="handleKeydown"
                />
                <button
                  type="button"
                  :disabled="!canSend"
                  :class="[
                    'mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition active:scale-95',
                    canSend
                      ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/25 hover:bg-blue-400'
                      : 'bg-white/5 text-zinc-600 cursor-not-allowed',
                  ]"
                  @click="submitQuery()"
                >
                  <Send class="h-4 w-4" />
                </button>
              </div>
              <p class="mt-2 text-center text-[11px] text-zinc-600">
                SyntheRank AI · 本地知识库 + 联网搜索 · 多路重排
              </p>
            </div>
          </div>
        </section>

        <!-- 溯源面板 -->
        <aside
          :class="[
            'flex flex-col border-t border-white/5 bg-[#0c0c12] lg:w-[380px] lg:shrink-0 lg:border-l lg:border-t-0',
            activeSources.length ? 'min-h-[280px] lg:min-h-0' : 'hidden lg:flex',
          ]"
        >
          <div class="flex items-center justify-between border-b border-white/5 px-4 py-3.5">
            <div class="flex items-center gap-2">
              <Layers class="h-4 w-4 text-blue-400" />
              <h3 class="text-sm font-medium text-zinc-200">多路溯源</h3>
              <span
                v-if="activeSources.length"
                class="rounded-full bg-blue-500/15 px-2 py-0.5 text-[11px] font-medium text-blue-300"
              >
                Top {{ activeSources.length }}
              </span>
            </div>
            <button
              v-if="activeSources.length"
              type="button"
              class="rounded-lg p-1.5 text-zinc-500 transition hover:bg-white/5 hover:text-zinc-300 lg:hidden"
              @click="activeSources = []"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto p-4">
            <div v-if="!activeSources.length" class="flex h-full flex-col items-center justify-center py-12 text-center">
              <Search class="mb-3 h-8 w-8 text-zinc-700" />
              <p class="text-sm text-zinc-600">检索完成后，溯源文档将在此展示</p>
            </div>

            <div v-else class="space-y-3">
              <article
                v-for="(source, idx) in activeSources"
                :key="idx"
                class="group rounded-xl border border-white/5 bg-[#12121a] p-4 transition hover:border-blue-500/20 hover:bg-[#14141f]"
              >
                <div class="mb-2.5 flex items-start justify-between gap-2">
                  <span
                    :class="[
                      'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium',
                      source.type === 'local'
                        ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20'
                        : 'bg-violet-500/10 text-violet-400 ring-1 ring-violet-500/20',
                    ]"
                  >
                    <Database v-if="source.type === 'local'" class="h-3 w-3" />
                    <Globe v-else class="h-3 w-3" />
                    {{ source.type === 'local' ? '本地' : '搜索' }}
                  </span>
                  <span class="text-[11px] font-mono text-zinc-500">{{ formatScore(source.score) }}</span>
                </div>

                <h4 class="mb-2 line-clamp-2 text-sm font-medium leading-snug text-zinc-200 group-hover:text-white">
                  {{ source.title }}
                </h4>

                <!-- 相关性进度条 -->
                <div class="mb-3">
                  <div class="mb-1 flex justify-between text-[10px] text-zinc-600">
                    <span>相关性</span>
                    <span>{{ Math.round(source.score * 100) }}%</span>
                  </div>
                  <div class="h-1.5 overflow-hidden rounded-full bg-white/5">
                    <div
                      class="h-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-700"
                      :style="{ width: `${Math.min(source.score * 100, 100)}%` }"
                    />
                  </div>
                </div>

                <p class="line-clamp-3 text-xs leading-relaxed text-zinc-500">
                  {{ source.content }}
                </p>
              </article>
            </div>
          </div>
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import {
  Bot,
  Brain,
  ChevronRight,
  Database,
  FileSearch,
  Globe,
  Layers,
  Loader2,
  Menu,
  MessageSquare,
  Plus,
  Search,
  Send,
  Sparkles,
  X,
} from 'lucide-vue-next'
import { marked } from 'marked'

const STORAGE_KEY = 'syntheRank_conversations'

const pipelineStages = [
  { key: 'retrieve', label: '检索中' },
  { key: 'rrf', label: 'RRF融合' },
  { key: 'rerank', label: 'BGE重排' },
  { key: 'generate', label: '智能生成' },
]

const quickHints = [
  'HAK 180 烫金机局部转印如何设置？',
  'RRF 融合与 BGE 重排的区别是什么？',
  '如何优化 RAG 检索召回率？',
]

const conversations = ref([])
const activeConversationId = ref(null)
const inputText = ref('')
const isProcessing = ref(false)
const stageIndex = ref(-1)
const activeSources = ref([])
const sidebarOpen = ref(false)
const chatContainer = ref(null)
const inputRef = ref(null)

const activeConversation = computed(() =>
  conversations.value.find((c) => c.id === activeConversationId.value) ?? null,
)

const canSend = computed(() => inputText.value.trim().length > 0 && !isProcessing.value)

marked.setOptions({ breaks: true, gfm: true })

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function formatScore(score) {
  return (score ?? 0).toFixed(3)
}

function generateId() {
  return `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function loadConversations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    conversations.value = raw ? JSON.parse(raw) : []
  } catch {
    conversations.value = []
  }
}

function saveConversations() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.value))
}

function startNewConversation() {
  const conv = {
    id: generateId(),
    title: '新对话',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
  conversations.value.unshift(conv)
  activeConversationId.value = conv.id
  activeSources.value = []
  sidebarOpen.value = false
  saveConversations()
}

function switchConversation(id) {
  activeConversationId.value = id
  activeSources.value = []
  sidebarOpen.value = false
  const lastAssistant = [...(conversations.value.find((c) => c.id === id)?.messages ?? [])]
    .reverse()
    .find((m) => m.role === 'assistant')
  if (lastAssistant?.sources) {
    activeSources.value = lastAssistant.sources
  }
}

function ensureActiveConversation() {
  if (!activeConversationId.value || !activeConversation.value) {
    startNewConversation()
  }
  return conversations.value.find((c) => c.id === activeConversationId.value)
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submitQuery()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function highlightSources(msgIndex) {
  const conv = activeConversation.value
  if (!conv) return
  const msg = conv.messages[msgIndex]
  if (msg?.sources) {
    activeSources.value = msg.sources
  }
}

/**
 * 模拟后端 RAG 查询流程
 * 返回结构: { answer: string, sources: Array<{ title, content, score, type }> }
 */
async function askQuestion(query) {
  const stageDurations = [900, 700, 800, 1200]

  for (let i = 0; i < pipelineStages.length; i++) {
    stageIndex.value = i
    await new Promise((r) => setTimeout(r, stageDurations[i]))
  }

  const mockSources = [
    {
      title: 'HAK 180 烫金机操作手册 - 局部转印设置',
      content:
        '在出厂默认状态下，局部转印功能需在操作面板进入「高级设置」→「转印区域」，设置起始位置 50mm 与结束位置 170mm，确认后执行试印校准。',
      score: 0.94,
      type: 'local',
    },
    {
      title: '烫金机温度与压力参数对照表',
      content:
        '不同材质纸张对应不同温度区间：铜版纸 120-140°C，特种纸 100-120°C。局部转印时需确保压力均匀，避免边缘模糊。',
      score: 0.87,
      type: 'local',
    },
    {
      title: 'HP 热转印纸打印与转印操作指南',
      content:
        '热转印前需镜像翻转设计稿，使用光滑耐热台面，追踪转印时间。缓慢移动速度不超过 12.7mm/s 以确保转印质量。',
      score: 0.72,
      type: 'search',
    },
    {
      title: 'RRF 多路召回融合算法原理',
      content:
        'Reciprocal Rank Fusion 通过倒数排名融合多路检索结果，无需分数归一化，能有效提升异构检索源的融合效果。',
      score: 0.65,
      type: 'local',
    },
    {
      title: 'BGE Reranker 在 RAG 中的应用实践',
      content:
        'BGE 重排模型基于 Cross-Encoder 架构，对 query-document 对进行精细相关性打分，显著提升 Top-K 结果质量。',
      score: 0.58,
      type: 'search',
    },
  ]

  const answer = `## 关于「${query}」的回答

根据本地知识库与联网搜索的多路检索结果，经 **RRF 融合** 与 **BGE 重排** 后，为您整理如下：

### 操作步骤

1. **进入设置菜单**：在 HAK 180 操作面板选择「高级设置」→「转印区域」
2. **设定转印范围**：起始位置设为 **50 mm**，结束位置设为 **170 mm**
3. **参数校准**：根据纸张材质调整温度（铜版纸 120-140°C），执行试印确认效果
4. **压力检查**：确保转印压力均匀，避免局部边缘模糊

### 技术说明

本回答综合了 **${mockSources.filter((s) => s.type === 'local').length}** 条本地文档与 **${mockSources.filter((s) => s.type === 'search').length}** 条联网搜索结果。BGE 重排后最高相关性得分为 **${mockSources[0].score.toFixed(2)}**。

> 如需更精确的操作指导，建议参考右侧溯源面板中的原始文档。`

  return { answer, sources: mockSources }
}

async function submitQuery(text) {
  const query = (text ?? inputText.value).trim()
  if (!query || isProcessing.value) return

  const conv = ensureActiveConversation()
  if (conv.title === '新对话') {
    conv.title = query.length > 24 ? `${query.slice(0, 24)}...` : query
  }

  conv.messages.push({ role: 'user', content: query })
  inputText.value = ''
  autoResize()
  isProcessing.value = true
  stageIndex.value = -1
  activeSources.value = []
  sidebarOpen.value = false
  saveConversations()
  await scrollToBottom()

  try {
    const { answer, sources } = await askQuestion(query)
    conv.messages.push({ role: 'assistant', content: answer, sources })
    activeSources.value = sources
    conv.updatedAt = Date.now()
    saveConversations()
  } catch (err) {
    conv.messages.push({
      role: 'assistant',
      content: `抱歉，处理请求时出现错误：${err?.message || '未知错误'}`,
      sources: [],
    })
    saveConversations()
  } finally {
    isProcessing.value = false
    stageIndex.value = -1
    await scrollToBottom()
  }
}

watch(activeConversationId, () => scrollToBottom())

onMounted(() => {
  loadConversations()
  if (conversations.value.length > 0) {
    activeConversationId.value = conversations.value[0].id
    const lastAssistant = [...conversations.value[0].messages]
      .reverse()
      .find((m) => m.role === 'assistant')
    if (lastAssistant?.sources) {
      activeSources.value = lastAssistant.sources
    }
  }
})
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

:deep(.prose) {
  --tw-prose-body: #d4d4d8;
  --tw-prose-headings: #fafafa;
  --tw-prose-bold: #fafafa;
  --tw-prose-links: #60a5fa;
  --tw-prose-code: #93c5fd;
  --tw-prose-quotes: #a1a1aa;
  --tw-prose-bullets: #52525b;
}

:deep(.prose h2) {
  margin-top: 1.25em;
  margin-bottom: 0.5em;
  font-size: 1.05rem;
  font-weight: 600;
}

:deep(.prose h3) {
  margin-top: 1em;
  margin-bottom: 0.4em;
  font-size: 0.95rem;
  font-weight: 600;
}

:deep(.prose p) {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
  line-height: 1.7;
}

:deep(.prose ol),
:deep(.prose ul) {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
  padding-left: 1.25em;
}

:deep(.prose li) {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

:deep(.prose blockquote) {
  border-left: 3px solid #3b82f6;
  padding-left: 1em;
  font-style: normal;
  color: #a1a1aa;
}

:deep(.prose strong) {
  color: #e4e4e7;
}

:deep(.prose code) {
  background: rgba(59, 130, 246, 0.1);
  padding: 0.15em 0.4em;
  border-radius: 0.25rem;
  font-size: 0.85em;
}

:deep(.prose code)::before,
:deep(.prose code)::after {
  content: none;
}
</style>
