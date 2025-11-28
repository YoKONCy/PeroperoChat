import axios from 'axios'

const host = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : 'localhost'
const defaultBase = `http://${host}:8000`

function normalizeBase(u) {
  try {
    const s = String(u || '').trim()
    if (!s) return defaultBase
    if (/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(s)) return s.replace(/\/$/, '')
    if (s.startsWith('/')) {
      const origin = (typeof window !== 'undefined' && window.location && window.location.origin) ? window.location.origin : defaultBase
      return `${origin}${s}`.replace(/\/$/, '')
    }
    if (/^[^\/:]+(:\d+)?(\/.*)?$/.test(s)) return `http://${s}`.replace(/\/$/, '')
    return defaultBase
  } catch (_) {
    return defaultBase
  }
}

const rawBase = (import.meta.env && import.meta.env.VITE_API_BASE) ? import.meta.env.VITE_API_BASE : ''
const baseURL = normalizeBase(rawBase || defaultBase)

export const api = axios.create({
  baseURL,
  timeout: 60000,
})

export async function chat(messages, model, temperature = 0.7, apiBase, opts = {}) {
  const config = apiBase ? { params: { api_base: apiBase } } : { params: {} }
  const body = { messages, model, temperature }
  if (opts && typeof opts === 'object') {
    if (opts.topP !== undefined) body.top_p = opts.topP
    if (opts.frequencyPenalty !== undefined) body.frequency_penalty = opts.frequencyPenalty
    if (opts.presencePenalty !== undefined) body.presence_penalty = opts.presencePenalty
  }
  try {
    const aBase = String(localStorage.getItem('ppc.assist.apiBase') || '').trim()
    const aKey = String(localStorage.getItem('ppc.assist.apiKey') || '').trim()
    const aModel = String(localStorage.getItem('ppc.assist.modelName') || '').trim()
    if (aBase) config.params.assistant_api_base = aBase
    const headers = {
      ...(aKey ? { 'X-Assistant-Authorization': `Bearer ${aKey}` } : {}),
      ...(aModel ? { 'X-Assistant-Model': encodeURIComponent(aModel) } : {}),
      ...(opts && opts.disableMemory ? { 'X-Disable-Memory': '1' } : {}),
    }
    const r = await api.post('/api/chat', body, { ...config, headers })
    return r.data
  } catch (e) {
    const aBase = String(localStorage.getItem('ppc.assist.apiBase') || '').trim()
    const aKey = String(localStorage.getItem('ppc.assist.apiKey') || '').trim()
    const aModel = String(localStorage.getItem('ppc.assist.modelName') || '').trim()
    if (aBase) config.params.assistant_api_base = aBase
    const headers = {
      ...(aKey ? { 'X-Assistant-Authorization': `Bearer ${aKey}` } : {}),
      ...(aModel ? { 'X-Assistant-Model': encodeURIComponent(aModel) } : {}),
      ...(opts && opts.disableMemory ? { 'X-Disable-Memory': '1' } : {}),
    }
    const r = await api.post('/api/chat', body, { ...config, headers })
    return r.data
  }
}

export async function chatStream(messages, model, temperature = 0.7, apiBase, opts = {}, onChunk) {
  const params = new URLSearchParams()
  if (apiBase) params.set('api_base', apiBase)
  const aBase = String(localStorage.getItem('ppc.assist.apiBase') || '').trim()
  if (aBase) params.set('assistant_api_base', aBase)
  const body = { messages, model, temperature }
  if (opts && typeof opts === 'object') {
    if (opts.topP !== undefined) body.top_p = opts.topP
    if (opts.frequencyPenalty !== undefined) body.frequency_penalty = opts.frequencyPenalty
    if (opts.presencePenalty !== undefined) body.presence_penalty = opts.presencePenalty
  }
  body.stream = true
  const auth = api?.defaults?.headers?.common?.Authorization
  const aKey = String(localStorage.getItem('ppc.assist.apiKey') || '').trim()
  const aModel = String(localStorage.getItem('ppc.assist.modelName') || '').trim()
  const base = api?.defaults?.baseURL || defaultBase
  const url = `${String(base).replace(/\/$/, '')}/api/chat/stream?${params.toString()}`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(auth ? { Authorization: auth } : {}), ...(aKey ? { 'X-Assistant-Authorization': `Bearer ${aKey}` } : {}), ...(aModel ? { 'X-Assistant-Model': encodeURIComponent(aModel) } : {}), ...(opts && opts.disableMemory ? { 'X-Disable-Memory': '1' } : {}) },
    body: JSON.stringify(body)
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let full = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value, { stream: true })
    full += chunk
    if (typeof onChunk === 'function') onChunk(chunk, full)
  }
  return full
}

export async function uploadModel(file) {
  const form = new FormData()
  form.append('file', file)
  const r = await api.post('/api/models/3d/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return r.data
}

export async function resetAll() {
  const r = await api.post('/api/reset')
  return r.data
}


export async function getDefaultPrompts() {
  const r = await api.get('/api/config/prompts')
  return r.data
}

export async function memoryList(type = '', limit = 50, offset = 0) {
  const params = {}
  if (type) params.type = type
  params.limit = limit
  params.offset = offset
  const r = await api.get('/api/memory/list', { params })
  return r.data
}

export async function memoryInsert(item) {
  const r = await api.post('/api/memory/insert', item)
  return r.data
}

export async function memoryDelete(id) {
  const params = new URLSearchParams()
  params.set('id', String(id))
  const base = api?.defaults?.baseURL || defaultBase
  const url = `${String(base).replace(/\/$/, '')}/api/memory/delete?${params.toString()}`
  const auth = api?.defaults?.headers?.common?.Authorization
  const r = await fetch(url, { method: 'POST', headers: { ...(auth ? { Authorization: auth } : {}) } })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return await r.json()
}

export async function memorySelect(messages, model) {
  const aBase = String(localStorage.getItem('ppc.assist.apiBase') || '').trim()
  const aKey = String(localStorage.getItem('ppc.assist.apiKey') || '').trim()
  const aModel = String(localStorage.getItem('ppc.assist.modelName') || '').trim()
  const headers = {
    ...(aKey ? { 'X-Assistant-Authorization': `Bearer ${aKey}` } : {}),
    ...(aModel ? { 'X-Assistant-Model': aModel } : {}),
  }
  const config = aBase ? { params: { assistant_api_base: aBase }, headers } : { headers }
  const r = await api.post('/api/memory/select', { messages, model }, config)
  return r.data
}

export async function memoryMaintain(model) {
  const aBase = String(localStorage.getItem('ppc.assist.apiBase') || '').trim()
  const aKey = String(localStorage.getItem('ppc.assist.apiKey') || '').trim()
  const aModel = String(localStorage.getItem('ppc.assist.modelName') || '').trim()
  const headers = {
    ...(aKey ? { 'X-Assistant-Authorization': `Bearer ${aKey}` } : {}),
    ...(aModel ? { 'X-Assistant-Model': aModel } : {}),
  }
  const config = aBase ? { params: { assistant_api_base: aBase }, headers } : { headers }
  const r = await api.post('/api/memory/maintain', { model }, config)
  return r.data
}

//
