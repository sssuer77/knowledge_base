/**
 * Import 模块 API — 对接 app/import_process/api/file_import_service.py (默认 :8000)
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export async function uploadFiles(files) {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `上传失败 (${res.status})`)
  }
  return res.json()
}

export async function fetchTaskStatus(taskId) {
  const res = await fetch(`${API_BASE}/status/${taskId}`)
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `状态查询失败 (${res.status})`)
  }
  return res.json()
}

function normalizeStatus(data) {
  return {
    status: data.status || 'processing',
    done_list: data.done_list ?? [],
    running_list: data.running_list ?? [],
  }
}

/**
 * SSE 流式订阅任务进度（实时推送，替代轮询）
 * @param {string} taskId
 * @param {{ onUpdate, onComplete, onError }} handlers
 * @returns {() => void} stop
 */
export function streamTaskStatus(taskId, { onUpdate, onComplete, onError }) {
  let es = null
  let stopped = false

  const stop = () => {
    stopped = true
    es?.close()
  }

  const applyUpdate = (raw) => {
    const data = normalizeStatus(raw)
    onUpdate?.(data)
    return data
  }

  const finish = (data) => {
    stop()
    onComplete?.(data)
  }

  // 拉取一次当前状态，避免 SSE 连接前丢失的上传阶段事件
  fetchTaskStatus(taskId)
    .then(applyUpdate)
    .catch(() => {})

  es = new EventSource(`${API_BASE}/stream/${taskId}`)

  es.addEventListener('ready', () => {
    fetchTaskStatus(taskId)
      .then(applyUpdate)
      .catch(() => {})
  })

  es.addEventListener('progress', (e) => {
    try {
      applyUpdate(JSON.parse(e.data))
    } catch { /* ignore */ }
  })

  es.addEventListener('final', (e) => {
    try {
      finish(applyUpdate(JSON.parse(e.data)))
    } catch (err) {
      stop()
      onError?.(err)
    }
  })

  es.addEventListener('error', (e) => {
    try {
      const payload = JSON.parse(e.data)
      stop()
      onError?.(new Error(payload.error || '处理失败'))
    } catch { /* SSE 连接级 error，见 onerror */ }
  })

  es.onerror = () => {
    if (stopped || es.readyState !== EventSource.CLOSED) return
    fetchTaskStatus(taskId)
      .then((raw) => {
        const data = applyUpdate(raw)
        if (data.status === 'completed' || data.status === 'failed') {
          finish(data)
        } else {
          onError?.(new Error('SSE 连接中断'))
        }
      })
      .catch((err) => onError?.(err))
  }

  return stop
}

/** @deprecated 保留兼容，推荐使用 streamTaskStatus */
export function pollTaskStatus(taskId, { interval = 1000, onUpdate, onComplete, onError }) {
  let timer = null
  let stopped = false

  const stop = () => {
    stopped = true
    if (timer) clearInterval(timer)
  }

  const tick = async () => {
    if (stopped) return
    try {
      const data = await fetchTaskStatus(taskId)
      onUpdate?.(normalizeStatus(data))
      if (data.status === 'completed' || data.status === 'failed') {
        stop()
        onComplete?.(normalizeStatus(data))
      }
    } catch (err) {
      stop()
      onError?.(err)
    }
  }

  tick()
  timer = setInterval(tick, interval)
  return stop
}
