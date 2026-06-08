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
      onUpdate?.(data)
      if (data.status === 'completed' || data.status === 'failed') {
        stop()
        onComplete?.(data)
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
