<template>
  <div class="chat">
    <div class="list" ref="listEl">
      <transition-group name="fade-up" tag="div" appear>
        <div v-for="(m,i) in messages" :key="i" class="msg" :class="m.role">
          <div class="avatar">
            <svg v-if="m.role==='assistant'" viewBox="0 0 48 48" width="28" height="28" aria-label="Girl" role="img">
              <defs>
                <linearGradient id="gGirl" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#3b82f6"/>
                  <stop offset="100%" stop-color="#f472b6"/>
                </linearGradient>
              </defs>
              <path d="M12 22c0-7 6-12 12-12s12 5 12 12v2c-3-2-6-3-12-3s-9 1-12 3z" fill="url(#gGirl)" opacity="0.9"/>
              <circle cx="24" cy="22" r="6" fill="#fff" opacity="0.95"/>
              <path d="M10 40c0-6 6-10 14-10s14 4 14 10" fill="url(#gGirl)" opacity="0.9"/>
            </svg>
            <svg v-else viewBox="0 0 48 48" width="28" height="28" aria-label="User" role="img">
              <defs>
                <linearGradient id="gU" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#f472b6"/>
                  <stop offset="100%" stop-color="#3b82f6"/>
                </linearGradient>
              </defs>
              <circle cx="24" cy="18" r="8" fill="url(#gU)" opacity="0.85"/>
              <path d="M10 40c0-7 6-12 14-12s14 5 14 12" fill="url(#gU)" opacity="0.85"/>
              <circle cx="24" cy="18" r="3" fill="#fff" opacity="0.9"/>
            </svg>
          </div>
          <div class="bubble">
            <div v-if="m.content==='__loading__'" class="content loading">
              <el-icon class="spin" size="18"><Loading /></el-icon>
              <span class="loading-text">正在生成...</span>
            </div>
            <div v-else class="content" v-html="formatContent(m.content)"></div>
            <div class="actions">
              <el-tooltip content="复制" placement="top" :offset="6" popper-class="cute-tip">
                <button class="mini-btn" @click="onCopy(i)" aria-label="复制">
                  <el-icon size="14"><DocumentCopy /></el-icon>
                </button>
              </el-tooltip>
              <el-tooltip v-if="m.role==='assistant'" content="重新生成" placement="top" :offset="6" popper-class="cute-tip">
                <button class="mini-btn" @click="onRegenerate(i)" aria-label="重新生成">
                  <el-icon size="14"><Refresh /></el-icon>
                </button>
              </el-tooltip>
              <el-tooltip content="修改文字" placement="top" :offset="6" popper-class="cute-tip">
                <button class="mini-btn" @click="onEdit(i)" aria-label="修改文字">
                  <el-icon size="14"><Edit /></el-icon>
                </button>
              </el-tooltip>
              <el-tooltip content="删除" placement="top" :offset="6" popper-class="cute-tip">
                <button class="mini-btn" @click="onDelete(i)" aria-label="删除">
                  <el-icon size="14"><Delete /></el-icon>
                </button>
              </el-tooltip>
            </div>
          </div>
        </div>
      </transition-group>
    </div>
    <form class="input" @submit.prevent="submit">
      <el-input
        v-model="text"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 6 }"
        placeholder="输入内容并发送（Shift+Enter换行）"
        clearable
        @keydown.enter="onKeydownEnter"
      />
      <el-button class="send gbtn" native-type="submit">发送</el-button>
    </form>
    <div class="eval-status" aria-live="polite">
      <span class="badge badge-eval">{{ progressText }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { Refresh, Edit, Delete, DocumentCopy, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
const props = defineProps({ messages: { type: Array, default: () => [] }, progressText: { type: String, default: '' } })
const emit = defineEmits(['send','regenerate','edit','delete'])
const text = ref('')
const listEl = ref(null)
watch(() => props.messages.length, async () => { await nextTick(); const el = listEl.value; if (el) el.scrollTop = el.scrollHeight }, { deep: false })
function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
}
function formatContent(t) {
  marked.setOptions({ gfm: true, breaks: true })
  const raw = String(t ?? '')
  const html = marked.parse(raw)
  const clean = DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
  return clean || escapeHtml(raw)
}
function onKeydownEnter(e) {
  if (e && e.shiftKey) return
  e && e.preventDefault()
  submit()
}
function submit() {
  const t = text.value.trim()
  if (!t) return
  emit('send', t)
  text.value = ''
}
function onRegenerate(index) { emit('regenerate', index) }
function onEdit(index) { emit('edit', index) }
function onDelete(index) { emit('delete', index) }
async function onCopy(index) {
  try {
    const m = props.messages[index]
    const text = String(m?.content || '')
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (_) {
    try {
      const m = props.messages[index]
      const text = String(m?.content || '')
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.focus(); ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      ElMessage.success('已复制到剪贴板')
    } catch (e) {
      ElMessage.error('复制失败')
    }
  }
}
</script>

<style scoped>
.chat { display: grid; grid-template-rows: 1fr auto auto; height: 80vh }
.list { padding: 12px 16px 6px; overflow: auto; display: flex; flex-direction: column; gap: 12px; background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(244,114,182,0.12)); border-top-left-radius: 16px; border-top-right-radius: 16px }
.msg { display: flex; padding: 6px 0; align-items: flex-end; gap: 10px }
.msg.assistant { justify-content: flex-start }
.msg.user { justify-content: flex-end }
.bubble { display: flex; flex-direction: column; max-width: 72% }
.msg.user .avatar { order: 1 }
.msg.user .bubble { order: 0 }
.msg.assistant .avatar { order: 0 }
.msg.assistant .bubble { order: 1 }
.avatar { width: 32px; height: 32px; display: grid; place-items: center; border-radius: 50%; background: linear-gradient(135deg, rgba(59,130,246,0.28), rgba(244,114,182,0.28)); box-shadow: 0 6px 14px rgba(0,0,0,0.18) }
.avatar svg { filter: drop-shadow(0 2px 6px rgba(0,0,0,0.22)) }
.msg .content { padding: 12px 14px; border-radius: 16px; border: none; background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.08)); backdrop-filter: blur(10px); box-shadow: 0 8px 20px rgba(0,0,0,0.15) }
.msg .content { white-space: normal }
.msg.user .content { background: linear-gradient(135deg, rgba(59,130,246,0.28), rgba(147,197,253,0.18)); border-color: rgba(59,130,246,0.35) }
.msg.assistant .content { background: linear-gradient(135deg, rgba(244,114,182,0.26), rgba(251,191,197,0.16)); border-color: rgba(244,114,182,0.35) }
.msg .content :deep(pre.md-code), .msg .content :deep(pre) { margin: 8px 0; padding: 12px 14px; background: rgba(12,16,26,0.92); border-radius: 10px; overflow: auto; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06); color: #e6e8eb; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; line-height: 1.55 }
.msg .content :deep(pre.md-code code), .msg .content :deep(pre code) { white-space: pre }
.msg .content :deep(code.md-inline), .msg .content :deep(:not(pre) > code) { background: rgba(12,16,26,0.85); border-radius: 6px; padding: 2px 6px; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace }
.msg .content :deep(p) { margin: 0.35em 0 }
.msg .content :deep(p:first-child) { margin-top: 0 }
.msg .content :deep(p:last-child) { margin-bottom: 0 }
.msg .content :deep(ul), .msg .content :deep(ol) { margin: 0.4em 0; padding-left: 1.2em }
.msg .content :deep(li) { margin: 0.2em 0 }
.msg .content :deep(blockquote) { margin: 0.4em 0; padding-left: 0.8em; border-left: 3px solid rgba(255,255,255,0.18) }
.msg .content :deep(img) { max-width: 100%; height: auto; border-radius: 8px }
.msg .content :deep(hr) { margin: 0.6em 0; border: none; border-top: 1px solid rgba(255,255,255,0.18) }
.msg .content :deep(h1) { font-size: 1.25rem; margin: 0.5em 0 0.3em }
.msg .content :deep(h2) { font-size: 1.15rem; margin: 0.5em 0 0.3em }
.msg .content :deep(h3) { font-size: 1.05rem; margin: 0.4em 0 0.25em }
.actions { display: flex; gap: 4px; margin-top: 6px; opacity: 0; pointer-events: none; transition: opacity .15s ease }
.msg.user .actions { justify-content: flex-end }
.msg.assistant .actions { justify-content: flex-start }
.bubble:hover .actions, .msg:hover .actions { opacity: 1; pointer-events: auto }
.mini-btn { width: 22px; height: 22px; border-radius: 6px; display: grid; place-items: center; color: rgba(207,211,220,0.65); background: transparent; border: none; outline: none; cursor: pointer; transition: background .16s ease, color .16s ease }
.mini-btn:hover { background: rgba(255,255,255,0.06); color: rgba(207,211,220,0.85) }
.input { display: grid; grid-template-columns: 1fr auto; gap: 8px; padding: 4px 8px; border-top: 1px solid rgba(255,255,255,0.08) }
.send { padding: 10px 16px }
.gbtn { position: relative; overflow: hidden; border-radius: 12px; background: linear-gradient(135deg, rgba(59,130,246,0.28), rgba(244,114,182,0.28)); border: 1px solid rgba(255,255,255,0.18); backdrop-filter: blur(6px); transition: transform .15s ease, box-shadow .15s ease }
.gbtn:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(59,130,246,0.25) }
.input :deep(.el-input__wrapper), .input :deep(.el-textarea__inner) { background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.06)); border: none; box-shadow: 0 6px 16px rgba(0,0,0,0.12) }
.input :deep(.el-input__inner), .input :deep(.el-textarea__inner) { color: #e6e8eb }
.input :deep(.el-input__inner::placeholder), .input :deep(.el-textarea__inner::placeholder) { color: rgba(236,240,255,0.92); font-weight: 500; letter-spacing: 0.4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; text-shadow: 0 1px 2px rgba(0,0,0,0.25) }
.eval-status { padding: 2px 8px; font-size: 12px; color: #e6e8eb; text-align: right; display: flex; justify-content: flex-end; gap: 8px; margin-top: 0; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; backdrop-filter: blur(6px); box-shadow: 0 6px 16px rgba(0,0,0,0.18); border: 1px solid rgba(255,255,255,0.18) }
.badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; box-shadow: 0 0 0 2px rgba(255,255,255,0.25) inset }
.badge-eval { background: linear-gradient(135deg, rgba(59,130,246,0.28), rgba(147,197,253,0.22)); }
.badge-eval::before { background: #60a5fa }
 
.fade-up-enter-active, .fade-up-leave-active { transition: opacity .28s ease, transform .28s ease }
.fade-up-enter-from, .fade-up-leave-to { opacity: 0; transform: translateY(6px) scale(0.98) }
.fade-up-move { transition: transform .24s ease }
@keyframes bubbleIn { from { opacity: 0; transform: translateY(6px) scale(0.98) } to { opacity: 1; transform: translateY(0) scale(1) } }
.msg .content { animation: bubbleIn .22s ease-out }
:deep(.content.loading) { display: inline-flex; align-items: center; gap: 8px }
:deep(.content.loading .loading-text) { opacity: 0.85 }
:deep(.content.loading .spin) { animation: spin 1s linear infinite }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
:deep(.list) { scrollbar-width: thin; scrollbar-color: rgba(59,130,246,0.6) rgba(255,255,255,0.08) }
:deep(.list)::-webkit-scrollbar { width: 8px; height: 8px }
:deep(.list)::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #3b82f6, #f472b6); border-radius: 8px; border: 2px solid rgba(255,255,255,0.15) }
:deep(.list)::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #2563eb, #ec4899) }
:deep(.list)::-webkit-scrollbar-track { background: rgba(255,255,255,0.06); border-radius: 8px }
@media (max-width: 768px) {
  .chat { height: calc(100vh - 220px) }
  .bubble { max-width: 88% }
  .list { padding: 8px 10px 6px }
  .msg .content { padding: 10px 12px; font-size: 14px; line-height: 1.6 }
  .mini-btn { width: 24px; height: 24px }
  .send { padding: 10px 14px }
  .eval-status { font-size: 11px; padding: 4px 8px }
}
</style>
