<template>
  <div id="l2d-panel" class="l2d-panel">
    <div class="l2d-fabs">
      <el-tooltip content="更换模型" placement="left" :offset="8" popper-class="cute-tip">
        <button class="fab fab-switch" @click="onSwitchModel" aria-label="更换模型">
          <i class="fa-solid fa-shuffle"></i>
        </button>
      </el-tooltip>
      <el-tooltip content="换装" placement="left" :offset="8" popper-class="cute-tip">
        <button class="fab fab-dress" @click="onRandTextures" aria-label="换装">
          <i class="fa-solid fa-shirt"></i>
        </button>
      </el-tooltip>
    </div>
  </div>
  <div class="l2d-status">
    <div class="stat stat-time">
      <i class="fa-solid fa-clock"></i>
      <span>{{ nowText }}</span>
    </div>
    <div class="stat stat-mood">
      <i class="fa-solid fa-heart"></i>
      <span>{{ moodText }}</span>
    </div>
  </div>
  <div class="l2d-status mental">
    <div class="stat stat-mind">
      <i class="fa-solid fa-brain"></i>
      <span>{{ mindText }}</span>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { ref } from 'vue'

function ensureFontAwesome() {
  const exists = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).some(l => String(l.href || '').includes('fontawesome'))
  if (!exists) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://fastly.jsdelivr.net/npm/@fortawesome/fontawesome-free@6/css/all.min.css'
    document.head.appendChild(link)
  }
}

function loadAutoload() {
  return new Promise((resolve, reject) => {
    if (window.__live2d_autoload_loaded) { resolve() ; return }
    const s = document.createElement('script')
    s.src = '/live2d-widget/autoload.js'
    s.onload = () => { window.__live2d_autoload_loaded = true; resolve() }
    s.onerror = () => reject(new Error('autoload.js failed'))
    document.body.appendChild(s)
  })
}

function moveWidgetIntoPanel() {
  const panel = document.getElementById('l2d-panel')
  const waifu = document.getElementById('waifu')
  const toggle = document.getElementById('waifu-toggle')
  if (toggle) toggle.remove()
  const tool = document.getElementById('waifu-tool')
  if (tool) tool.remove()
  const canvas = document.getElementById('live2d')
  if (waifu && panel && !panel.contains(waifu)) {
    panel.appendChild(waifu)
    waifu.style.bottom = '0'
    waifu.style.left = '0'
    waifu.style.position = 'relative'
    if (canvas) { try { canvas.style.width = '360px'; canvas.style.height = '360px'; canvas.style.display = 'block' } catch {} }
  }
}

let observer = null
let tick = null
const nowText = ref('')
const moodText = ref('Pero心情：软萌中')
const mindText = ref('Pero心理活动："Pero要永远跟主人在一起！"')

function formatNow() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${day} ${hh}:${mm}:${ss}`
}
function onSwitchModel() {
  try { if (window.WaifuWidget && typeof window.WaifuWidget.loadOtherModel === 'function') window.WaifuWidget.loadOtherModel() } catch {}
}
function onRandTextures() {
  try { if (window.WaifuWidget && typeof window.WaifuWidget.loadRandModel === 'function') window.WaifuWidget.loadRandModel() } catch {}
}

onMounted(async () => {
  ensureFontAwesome()
  try { await loadAutoload() } catch {}
  setTimeout(() => {
    if (!document.getElementById('waifu') && typeof window.initWidget === 'function') {
      try { window.initWidget({ waifuPath: '/live2d-widget/waifu-tips.json', apiPath: 'https://api.zsq.im/live2d' }) } catch {}
    }
    moveWidgetIntoPanel()
  }, 50)
  observer = new MutationObserver(() => moveWidgetIntoPanel())
  observer.observe(document.body, { childList: true, subtree: true })
  nowText.value = formatNow()
  try {
    const m = String(localStorage.getItem('ppc.mood') || '').trim()
    if (m) moodText.value = `Pero心情：${m}`
    const md = String(localStorage.getItem('ppc.mind') || '').trim()
    if (md) mindText.value = `Pero心理活动：${md}`
  } catch {}
  tick = setInterval(() => { nowText.value = formatNow() }, 1000)
  window.addEventListener('ppc:mood', e => { try { moodText.value = `Pero心情：${String(e.detail || '').trim() || '软萌中'}` } catch {} })
  window.addEventListener('ppc:mind', e => { try { mindText.value = `Pero心理活动：${String(e.detail || '').trim() || '"Pero要永远跟主人在一起！"'}` } catch {} })
})

onBeforeUnmount(() => {
  try { if (observer) observer.disconnect() } catch {}
  try { if (tick) clearInterval(tick) } catch {}
  try { window.removeEventListener('ppc:mood', () => {}) } catch {}
  try { window.removeEventListener('ppc:mind', () => {}) } catch {}
})
</script>

<style>
.l2d-panel { position: relative; height: 380px; display: block; padding: 8px }
.l2d-panel #waifu { position: relative !important; bottom: 0 !important; left: 0 !important; transform: none !important; margin: 0 !important; display: inline-block !important; line-height: 0; overflow: hidden }
.l2d-panel #live2d { width: 360px; height: 360px; display: block }
.l2d-panel #waifu-tips { position: absolute !important; top: 18px !important; left: 8px !important; padding: 12px 14px !important; border-radius: 16px !important; border: none !important; background: linear-gradient(135deg, rgba(244,114,182,0.26), rgba(251,191,197,0.16)) !important; backdrop-filter: blur(10px) !important; box-shadow: 0 8px 20px rgba(0,0,0,0.15) !important; color: #e6e8eb !important; line-height: 1.7 !important; opacity: 1 !important; margin: 0 !important; animation: none !important; z-index: 2 !important; max-width: calc(100% - 24px) !important }
.l2d-panel #waifu-tips::after { content: ""; position: absolute; width: 14px; height: 14px; right: -6px; bottom: -6px; background: linear-gradient(135deg, rgba(244,114,182,0.26), rgba(251,191,197,0.16)); transform: rotate(45deg); box-shadow: 0 8px 16px rgba(0,0,0,0.15); border-radius: 2px; pointer-events: none }
.l2d-panel #waifu-tips .fa-lg { display: none }
.l2d-panel #waifu-tips.waifu-tips-active { opacity: 1 }
.l2d-panel #waifu-tool { right: 8px; top: 8px }
.l2d-panel #waifu-tool { display: none !important }

.l2d-fabs { position: absolute; right: 10px; bottom: 10px; display: grid; gap: 10px; z-index: 3 }
.fab { width: 42px; height: 42px; border-radius: 50%; display: grid; place-items: center; color: #e6e8eb; background: linear-gradient(135deg, rgba(59,130,246,0.24), rgba(244,114,182,0.22)); border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 10px 24px rgba(0,0,0,0.22); backdrop-filter: blur(10px); cursor: pointer; outline: none; transition: transform .14s ease, box-shadow .14s ease }
.fab:hover { transform: translateY(-2px); box-shadow: 0 14px 32px rgba(59,130,246,0.28) }
.fab i { font-size: 16px; filter: drop-shadow(0 2px 6px rgba(59,130,246,0.35)) }
@keyframes floaty { 0% { transform: translateY(0) } 50% { transform: translateY(-3px) } 100% { transform: translateY(0) } }
.fab-switch { animation: floaty 3.2s ease-in-out infinite }
.fab-dress { animation: floaty 3.2s ease-in-out infinite; animation-delay: .8s }

.l2d-status { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 8px; margin-top: 6px }
.l2d-status .stat { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 14px; color: #e6e8eb; background: linear-gradient(180deg, rgba(59,130,246,0.10), rgba(244,114,182,0.10)); backdrop-filter: blur(8px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.14) }
.l2d-status .stat i { filter: drop-shadow(0 2px 6px rgba(59,130,246,0.35)) }
.l2d-status .stat-time i { color: #93c5fd }
.l2d-status .stat-mood i { color: #fda4af }
.l2d-status.mental { grid-template-columns: 1fr }
.l2d-status .stat-mind i { color: #a78bfa }
</style>
