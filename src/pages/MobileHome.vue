<template>
  <div class="home">
    <div class="hero">
      <Live2DWidget @click="handleWaifuClick" />
      
      <!-- 话题气泡容器 (左上角) -->
      <div class="topic-bubbles-container" v-if="topics.length > 0">
        <div 
          v-for="(t, idx) in topics" 
          :key="t.time + t.topic"
          :class="['topic-bubble', { 'is-revealed': t.revealed }]"
          :style="getTopicBubbleStyle(idx)"
          @click="toggleTopicReveal(idx)"
        >
          <div class="bubble-content">
            <template v-if="!t.revealed">
              <i class="fas fa-user-secret secret-icon"></i>
              <span class="topic-text">秘密...</span>
            </template>
            <template v-else>
              <span class="topic-text revealed">{{ t.topic }}</span>
              <span class="time-text">{{ formatReminderTime(t.time) }}</span>
              <div class="bubble-actions" @click.stop="deleteTopic(idx)">
                <i class="fas fa-trash-alt remove-icon"></i>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- 任务提醒小气泡容器 (右上角) -->
      <div class="reminder-bubbles-container" v-if="reminders.length > 0">
        <div 
          v-for="(r, idx) in reminders" 
          :key="r.time + r.task"
          class="reminder-bubble"
          :style="getBubbleStyle(idx)"
          @click="deleteReminder(idx)"
        >
          <div class="bubble-content">
            <span class="task-text">{{ r.task }}</span>
            <span class="time-text">{{ formatReminderTime(r.time) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部按钮栏 -->
    <div class="inputbar-mini" v-if="!isExpanded">
      <button class="expand-btn" :disabled="isLoading" @click="expandInput">
        <i class="fas fa-comment-dots"></i>
        <span>{{ isLoading ? 'Pero正在思考中...' : '点击与 Pero 对话...' }}</span>
      </button>
      <div class="mini-tools">
        <button class="tool-btn-mini" @click="toSettings"><i class="fas fa-cog"></i></button>
        <button class="tool-btn-mini" @click="openHistory"><i class="fas fa-history"></i></button>
      </div>
    </div>

    <!-- 展开后的全屏/半屏输入区域 -->
    <Transition name="fade-slide">
      <div class="expanded-input-overlay" v-if="isExpanded" @click.self="collapseInput">
        <div class="expanded-input-card">
          <div class="card-header">
            <span class="title">与 Pero 对话</span>
            <button class="close-btn" @click="collapseInput"><i class="fas fa-times"></i></button>
          </div>
          <textarea 
            ref="inputRef"
            v-model="text" 
            class="expanded-textarea" 
            placeholder="在这里输入你想说的话..."
            @keyup.ctrl.enter="onSend"
          ></textarea>
          <div class="card-footer">
            <span class="hint">Ctrl + Enter 发送</span>
            <button class="send-btn" :disabled="!text.trim() || isLoading" @click="onSend">
              <el-icon><Promotion /></el-icon>
              <span>发送</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <HistoryOverlay 
      v-if="showHistory" 
      :messages="messages"
      @close="showHistory=false" 
      @delete="deleteMessageAt"
      @regenerate="regenerateAndClose"
      @copy="copyMessage"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Haptics, ImpactStyle } from '@capacitor/haptics'
import { LocalNotifications } from '@capacitor/local-notifications'
import { Capacitor } from '@capacitor/core'
import Live2DWidget from '../components/Live2DWidget.vue'
import HistoryOverlay from '../components/HistoryOverlay.vue'
import { chat as chatApi, chatStream, getRelevantMemories, saveMemory, deleteMemoriesByMsgTimestamp, getDefaultPrompts } from '../api'
import { Promotion } from '@element-plus/icons-vue'

const router = useRouter()
const text = ref('')
const isExpanded = ref(false) // 是否展开大输入框
const inputRef = ref(null)
const messages = ref([])
const modelName = ref('请先获取模型')
const apiBase = ref('https://api.openai.com')
const temperature = ref(0.7)
const topP = ref(1)
const frequencyPenalty = ref(0)
const presencePenalty = ref(0)
const stream = ref(false)
const memoryRounds = ref(40)
const showHistory = ref(false)
const chatPreview = ref(null) // 引用聊天预览区域
const isLoading = ref(false) // 是否正在请求中

// 定时提醒任务列表
const reminders = ref(lsGet('ppc.reminders', []))
// 主动话题列表
const topics = ref(lsGet('ppc.topics', []))

// 初始化通知权限
const initNotifications = async () => {
  if (Capacitor.isNativePlatform()) {
    try {
      const perm = await LocalNotifications.checkPermissions()
      if (perm.display !== 'granted') {
        await LocalNotifications.requestPermissions()
      }
    } catch (e) {
      console.warn('Notifications permission failed', e)
    }
  }
}

// 发送系统通知
const sendSystemNotification = async (title, body) => {
  if (Capacitor.isNativePlatform()) {
    try {
      await LocalNotifications.schedule({
        notifications: [
          {
            title,
            body,
            id: Date.now(),
            schedule: { at: new Date(Date.now() + 1000) }, // 1秒后立即发送
            sound: 'beep.wav',
            attachments: [],
            actionTypeId: '',
            extra: null
          }
        ]
      })
    } catch (e) {
      console.warn('Notification failed', e)
    }
  }
}

// 检查提醒任务和主动话题
function checkReminders() {
  if (isLoading.value) return
  
  const now = new Date().getTime()
  
  // 1. 检查任务提醒
  const toTriggerReminder = reminders.value.filter(r => {
    const targetTime = new Date(r.time).getTime()
    return now >= targetTime
  })

  if (toTriggerReminder.length > 0) {
    const task = toTriggerReminder[0]
    reminders.value = reminders.value.filter(r => r.time !== task.time)
    lsSet('ppc.reminders', reminders.value)
    onSend(`【管理系统提醒：Pero，你与主人的约定时间已到，请主动提醒主人。约定内容：${task.task}】`)
    
    // 发送系统级通知 (App环境)
    sendSystemNotification('Pero 的任务提醒', task.task)
    return // 优先处理任务
  }

  // 2. 检查主动话题
  const toTriggerTopic = topics.value.filter(t => {
    const targetTime = new Date(t.time).getTime()
    return now >= targetTime
  })

  if (toTriggerTopic.length > 0) {
    const topic = toTriggerTopic[0]
    topics.value = topics.value.filter(t => t.time !== topic.time)
    lsSet('ppc.topics', topics.value)
    onSend(`【管理系统提醒：Pero，你刚才有话题想找主人聊哦，内容是：${topic.topic}；去和主人聊天吧！】`)
    
    // 发送系统级通知 (App环境)
    sendSystemNotification('Pero 想找你聊天', topic.topic)
  }
}

onMounted(() => {
  // 初始化通知
  initNotifications()
  // 每 10 秒检查一次提醒
  setInterval(checkReminders, 10000)
})

// 移除提醒任务
function removeReminder(idx) {
  reminders.value.splice(idx, 1)
  lsSet('ppc.reminders', reminders.value)
}

// 移除话题
function removeTopic(idx) {
  topics.value.splice(idx, 1)
  lsSet('ppc.topics', topics.value)
}

// 切换话题揭晓状态
function toggleTopicReveal(idx) {
  topics.value[idx].revealed = !topics.value[idx].revealed
  lsSet('ppc.topics', topics.value)
}

// 处理角色点击事件（增加震动）
const handleWaifuClick = async () => {
  // 如果在 App 环境，提供微弱震动反馈
  if (Capacitor.isNativePlatform()) {
    try {
      await Haptics.impact({ style: ImpactStyle.Light })
    } catch (e) {
      console.warn('Haptics failed', e)
    }
  }
  
  // 触发原本的点击交互逻辑
  window.dispatchEvent(new CustomEvent('ppc:waifu-click'))
}

// 删除任务并取消通知
const deleteReminder = async (idx) => {
  const reminder = reminders.value[idx]
  if (Capacitor.isNativePlatform() && reminder.id) {
    try {
      await LocalNotifications.cancel({
        notifications: [{ id: Math.abs(reminder.id) }]
      })
    } catch (e) {
      console.warn('Cancel notification failed', e)
    }
  }
  reminders.value.splice(idx, 1)
  lsSet('ppc.reminders', reminders.value)
}

// 删除话题并取消通知
const deleteTopic = async (idx) => {
  const topic = topics.value[idx]
  if (Capacitor.isNativePlatform() && topic.id) {
    try {
      await LocalNotifications.cancel({
        notifications: [{ id: Math.abs(topic.id) }]
      })
    } catch (e) {
      console.warn('Cancel notification failed', e)
    }
  }
  topics.value.splice(idx, 1)
  lsSet('ppc.topics', topics.value)
}

// 格式化时间显示
function formatReminderTime(timeStr) {
  try {
    const d = new Date(timeStr)
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch (e) {
    return ''
  }
}

// 获取话题气泡样式 (左侧区域)
function getTopicBubbleStyle(idx) {
  const baseOffsets = [
    { top: '10%', left: '5%' },
    { top: '35%', left: '15%' },
    { top: '20%', left: '40%' },
    { top: '55%', left: '5%' },
    { top: '70%', left: '30%' }
  ]
  
  const offset = baseOffsets[idx % baseOffsets.length]
  const jitterX = idx >= baseOffsets.length ? (Math.sin(idx) * 10) : 0
  const jitterY = idx >= baseOffsets.length ? (Math.cos(idx) * 10) : 0
  
  const delay = (idx * 0.8) + 's'
  const duration = (4 + (idx % 2)) + 's'
  
  return {
    top: `calc(${offset.top} + ${jitterY}px)`,
    left: `calc(${offset.left} + ${jitterX}px)`,
    animationDelay: delay,
    animationDuration: duration,
    zIndex: 100 - idx
  }
}

// 获取任务气泡样式 (右侧区域)
function getBubbleStyle(idx) {
  // 调整基础位置偏移，使其更紧凑并位于头像右上角区域
  const baseOffsets = [
    { top: '0%', right: '0%' },
    { top: '25%', right: '35%' },
    { top: '15%', right: '65%' },
    { top: '50%', right: '10%' },
    { top: '65%', right: '45%' },
    { top: '40%', right: '70%' },
    { top: '10%', right: '30%' },
    { top: '75%', right: '15%' }
  ]
  
  // 如果任务超过预设偏移量，加入微小的随机扰动避免完全重叠
  const offset = baseOffsets[idx % baseOffsets.length]
  const jitterX = idx >= baseOffsets.length ? (Math.sin(idx) * 10) : 0
  const jitterY = idx >= baseOffsets.length ? (Math.cos(idx) * 10) : 0
  
  // 随机动画延迟，让每个气泡浮动不同步
  const delay = (idx * 0.7) + 's'
  const duration = (3 + (idx % 3)) + 's'
  
  return {
    top: `calc(${offset.top} + ${jitterY}px)`,
    right: `calc(${offset.right} + ${jitterX}px)`,
    animationDelay: delay,
    animationDuration: duration,
    zIndex: 100 - idx // 越新的任务越靠前
  }
}

function regenerateAndClose(idx) {
  showHistory.value = false
  regenerateAt(idx)
}

function lsGet(key, fallback) {
  try { const v = localStorage.getItem(key); if (v===null||v===undefined) return fallback; try { return JSON.parse(v) } catch(_) { return v } } catch(_) { return fallback }
}
function lsSet(key, value) {
  try { const v = typeof value === 'string' ? value : JSON.stringify(value); localStorage.setItem(key, v) } catch(_) {}
}
function persistMessages() {
  try { 
    const arr = messages.value.map(m => ({ 
      role: m.role, 
      content: m.content, 
      timestamp: m.timestamp 
    })); 
    lsSet('ppc.messages', arr) 
  } catch(_) {}
}

function toSettings() { router.push('/settings') }
function openHistory() { showHistory.value = true }

function expandInput() {
  if (isLoading.value) return
  isExpanded.value = true
  setTimeout(() => {
    if (inputRef.value) inputRef.value.focus()
  }, 300)
}

function collapseInput() {
  isExpanded.value = false
}

// 滚动到底部函数
function scrollToBottom() {
  if (chatPreview.value) {
    setTimeout(() => {
      chatPreview.value.scrollTop = chatPreview.value.scrollHeight
    }, 100)
  }
}

// 解析并保存记忆
async function parseAndSaveMemory(text, msgTimestamp = null) {
  if (!text) return
  const memoryMatch = text.match(/<MEMORY>([\s\S]*?)<\/MEMORY>/)
  if (memoryMatch) {
    try {
      const content = memoryMatch[1].trim()
      const memoryData = JSON.parse(content)
      if (memoryData.content && memoryData.tags) {
        await saveMemory(memoryData, msgTimestamp)
        console.log('记忆已保存:', memoryData.content)
      }
    } catch (e) {
      console.error('解析 MEMORY JSON 失败:', e)
    }
  }
}

// 预设未来系统通知（核心：让通知在应用关闭后依然生效）
const scheduleFutureNotification = async (id, title, body, timeStr) => {
  if (Capacitor.isNativePlatform()) {
    try {
      const scheduleDate = new Date(timeStr)
      // 如果时间还没过，就预设通知
      if (scheduleDate > new Date()) {
        await LocalNotifications.schedule({
          notifications: [
            {
              title,
              body,
              id: Math.abs(id), // ID 必须是整数
              schedule: { at: scheduleDate },
              sound: 'beep.wav'
            }
          ]
        })
        console.log(`[Notification] 已预设未来通知: ${title} at ${timeStr}`)
      }
    } catch (e) {
      console.warn('Schedule notification failed', e)
    }
  }
}

// 解析 Pero 状态标签
function parsePeroStatus(content) {
  if (!content) return
  
  // 1. 解析旧版 PEROCUE
  const perocueMatch = content.match(/<PEROCUE>([\s\S]*?)<\/PEROCUE>/)
  if (perocueMatch) {
    try {
      const statusMap = JSON.parse(perocueMatch[1].trim())
      if (statusMap.mood) {
        localStorage.setItem('ppc.mood', statusMap.mood)
        window.dispatchEvent(new CustomEvent('ppc:mood', { detail: statusMap.mood }))
      }
      if (statusMap.vibe) {
        localStorage.setItem('ppc.vibe', statusMap.vibe)
        window.dispatchEvent(new CustomEvent('ppc:vibe', { detail: statusMap.vibe }))
      }
      if (statusMap.mind) {
        localStorage.setItem('ppc.mind', statusMap.mind)
        window.dispatchEvent(new CustomEvent('ppc:mind', { detail: statusMap.mind }))
      }
    } catch (e) {
      console.error('解析 PEROCUE JSON 失败:', e)
    }
  }

  // 2. 解析新版 CLICK_MESSAGES
  const clickRegex = /<CLICK_MESSAGES>([\s\S]*?)<\/CLICK_MESSAGES>/
  const clickMatch = content.match(clickRegex)
  if (clickMatch) {
    try {
      const messages = JSON.parse(clickMatch[1].trim())
      if (Array.isArray(messages) && messages.length >= 3) {
        let cur = {}
        try {
          const saved = localStorage.getItem('ppc.waifu.texts')
          if (saved) cur = JSON.parse(saved)
        } catch (e) {}
        
        cur.click_messages_01 = messages[0]
        cur.click_messages_02 = messages[1]
        cur.click_messages_03 = messages[2]
        // 移除多余字段
        delete cur['click_messages_04']
        delete cur['click_messages_05']
        delete cur['click_messages_06']
        
        localStorage.setItem('ppc.waifu.texts', JSON.stringify(cur))
        window.dispatchEvent(new CustomEvent('ppc:waifu-texts-updated', { detail: cur }))
      }
    } catch (e) {
      console.warn('Failed to parse click messages JSON:', e)
    }
  }

  // 3. 解析 IDLE_MESSAGES
  const idleRegex = /<IDLE_MESSAGES>([\s\S]*?)<\/IDLE_MESSAGES>/
  const idleMatch = content.match(idleRegex)
  if (idleMatch) {
    try {
      const messages = JSON.parse(idleMatch[1].trim())
      if (Array.isArray(messages) && messages.length >= 2) {
        let cur = {}
        try {
          const saved = localStorage.getItem('ppc.waifu.texts')
          if (saved) cur = JSON.parse(saved)
        } catch (e) {}
        
        cur.idleMessages_01 = messages[0]
        cur.idleMessages_02 = messages[1]
        // 移除多余的旧挂机字段
        delete cur['idleMessages_03']
        delete cur['idleMessages_04']
        delete cur['idleMessages_05']
        
        localStorage.setItem('ppc.waifu.texts', JSON.stringify(cur))
        window.dispatchEvent(new CustomEvent('ppc:waifu-texts-updated', { detail: cur }))
      }
    } catch (e) {
      console.warn('Failed to parse idle messages JSON:', e)
    }
  }

  // 4. 解析 BACK_MESSAGES
  const backRegex = /<BACK_MESSAGES>([\s\S]*?)<\/BACK_MESSAGES>/
  const backMatch = content.match(backRegex)
  if (backMatch) {
    try {
      const messages = JSON.parse(backMatch[1].trim())
      if (Array.isArray(messages) && messages.length >= 1) {
        let cur = {}
        try {
          const saved = localStorage.getItem('ppc.waifu.texts')
          if (saved) cur = JSON.parse(saved)
        } catch (e) {}
        
        cur.visibilityBack = messages[0]
        
        localStorage.setItem('ppc.waifu.texts', JSON.stringify(cur))
        window.dispatchEvent(new CustomEvent('ppc:waifu-texts-updated', { detail: cur }))
      }
    } catch (e) {
      console.warn('Failed to parse back messages JSON:', e)
    }
  }

  // 5. 解析 REMINDER (支持多个标签)
  const reminderRegex = /<REMINDER>([\s\S]*?)<\/REMINDER>/g
  let match
  while ((match = reminderRegex.exec(content)) !== null) {
    try {
      const data = JSON.parse(match[1].trim())
      if (data.time && data.task) {
        // 添加到提醒列表（去重）
        const exists = reminders.value.some(r => r.time === data.time && r.task === data.task)
        if (!exists) {
          const rId = Date.now() + Math.floor(Math.random() * 1000)
          data.id = rId
          reminders.value.push(data)
          lsSet('ppc.reminders', reminders.value)
          console.log('新提醒已添加:', data)
          // 立即向系统预设未来通知
          scheduleFutureNotification(rId, 'Pero 的任务提醒', data.task, data.time)
        }
      }
    } catch (e) {
      console.warn('Failed to parse reminder JSON:', e)
    }
  }

  // 6. 解析 TOPIC (支持多个标签)
  const topicRegex = /<TOPIC>([\s\S]*?)<\/TOPIC>/g
  let tMatch
  while ((tMatch = topicRegex.exec(content)) !== null) {
    try {
      const data = JSON.parse(tMatch[1].trim())
      if (data.time && data.topic) {
        // 添加到话题列表（去重）
        const exists = topics.value.some(t => t.time === data.time && t.topic === data.topic)
        if (!exists) {
          const tId = Date.now() + Math.floor(Math.random() * 1000)
          data.id = tId
          // 初始设为不显示（秘密）
          data.revealed = false
          topics.value.push(data)
          lsSet('ppc.topics', topics.value)
          console.log('新主动话题已添加:', data)
          // 立即向系统预设未来通知
          scheduleFutureNotification(tId, 'Pero 想找你聊天', data.topic, data.time)
        }
      }
    } catch (e) {
      console.warn('Failed to parse topic JSON:', e)
    }
  }
}

// 清理消息中的隐藏标签
function cleanMessageContent(text) {
  if (!text) return ''
  if (text === '__loading__') return '正在思考...'
  return text
    .replace(/<PEROCUE>[\s\S]*?<\/PEROCUE>/g, '')
    .replace(/<MEMORY>[\s\S]*?<\/MEMORY>/g, '')
    .replace(/<CLICK_MESSAGES>[\s\S]*?<\/CLICK_MESSAGES>/g, '')
    .replace(/<IDLE_MESSAGES>[\s\S]*?<\/IDLE_MESSAGES>/g, '')
    .replace(/<BACK_MESSAGES>[\s\S]*?<\/BACK_MESSAGES>/g, '')
    .replace(/<REMINDER>[\s\S]*?<\/REMINDER>/g, '')
    .replace(/<TOPIC>[\s\S]*?<\/TOPIC>/g, '')
    .trim()
}

// 获取当前环境信息 Prompt (时间、地点、天气)
function getEnvPrompt() {
  const d = new Date()
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  const timeStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')} ${weekdays[d.getDay()]}`
  
  const location = localStorage.getItem('ppc.location') || '未知地点'
  const weather = localStorage.getItem('ppc.weather') || '未知天气'
  
  return `[Current Environment]\nTime: ${timeStr}\nLocation: ${location}\nWeather: ${weather}`
}

async function onSend(systemMsg = null) {
  const t = typeof systemMsg === 'string' ? systemMsg : String(text.value || '').trim()
  if (!t || isLoading.value) return
  
  // 只有非系统消息才清空输入框
  if (!systemMsg) text.value = ''
  isLoading.value = true
  
  const now = Date.now()
  const user = { role: 'user', content: t, timestamp: now }
  messages.value = [...messages.value, user, { role: 'assistant', content: '__loading__', timestamp: now + 1 }]
  
  // 发送消息后折叠
  isExpanded.value = false
  
  // 发送“正在思考”状态到 Live2D 气泡
  window.dispatchEvent(new CustomEvent('ppc:chat', { detail: 'Pero正在思考中...' }))
  
  const idx = messages.value.length - 1
  persistMessages()
  scrollToBottom() // 新消息添加后滚动到底部
  try {
    // 获取默认提示词并设置回退逻辑
    const defaults = await getDefaultPrompts()
    const systemPrompt = String(lsGet('ppc.systemPrompt', '') || '').trim() || defaults.system_prompt_default
    const personaText = String(lsGet('ppc.personaText', '') || '').trim() || defaults.persona_prompt_default
    const postSystemPrompt = String(lsGet('ppc.postSystemPrompt', '') || '').trim() || defaults.post_prompt_default
    const userName = String(lsGet('ppc.userName', '') || '').trim()
    const userPersona = String(lsGet('ppc.userPersonaText', '') || '').trim()
    
    // 构建请求消息，添加提示词
    // 根据设置的记忆轮次截断历史记录（1轮 = 1对消息）
    const limitCount = memoryRounds.value * 2
    let reqForApi = messages.value.slice(0, idx).slice(-limitCount)
    
    // 注入当前环境信息
    reqForApi = [{ role: 'system', content: getEnvPrompt() }, ...reqForApi]
    
    // 检索并注入长期记忆
    const relevantMemories = await getRelevantMemories(t)
    if (relevantMemories.length > 0) {
      const memoryPrompt = `<LONG_TERM_MEMORY>\n${relevantMemories.map(m => `[${m.realTime || '未知时间'}] ${m.content}`).join('\n')}\n</LONG_TERM_MEMORY>`
      reqForApi = [{ role: 'system', content: memoryPrompt }, ...reqForApi]
    }
    
    // 如果有系统提示词，添加到消息开头
    if (systemPrompt && !reqForApi.some(m => m.role === 'system' && m.content.includes(systemPrompt))) {
      reqForApi = [{ role: 'system', content: systemPrompt }, ...reqForApi]
    }
    
    // 如果有人设提示词，添加到系统提示词之后或消息开头
    if (personaText && !reqForApi.some(m => m.content.includes(personaText))) {
      const systemIndex = reqForApi.findIndex(m => m.role === 'system')
      if (systemIndex >= 0) {
        reqForApi.splice(systemIndex + 1, 0, { role: 'system', content: personaText })
      } else {
        reqForApi = [{ role: 'system', content: personaText }, ...reqForApi]
      }
    }

    // 如果有用户设定，添加到系统/人设提示词之后
    if (userName || userPersona) {
      const userSettingPrompt = `[User Info]\nName: ${userName || 'User'}\nDescription: ${userPersona || 'No description'}`
      if (!reqForApi.some(m => m.content.includes(userSettingPrompt))) {
        let lastSystemIndex = -1
        for (let i = 0; i < reqForApi.length; i++) {
          if (reqForApi[i].role === 'system') lastSystemIndex = i
          else break // 只在开头的系统消息序列中寻找
        }
        reqForApi.splice(lastSystemIndex + 1, 0, { role: 'system', content: userSettingPrompt })
      }
    }
    
    // 如果有后置提示词，添加到用户消息之后
    if (postSystemPrompt && reqForApi.length > 0) {
      const lastUserIndex = reqForApi.map(m => m.role).lastIndexOf('user')
      if (lastUserIndex >= 0) {
        const userMsg = reqForApi[lastUserIndex].content
        if (!userMsg.includes(postSystemPrompt)) {
          reqForApi[lastUserIndex] = {
            role: 'user',
            content: `${userMsg}\n\n${postSystemPrompt}`
          }
        }
      }
    }
    
    const baseReq = reqForApi
    if (stream.value) {
      const final = await chatStream(baseReq, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value }, (_, full) => {
        messages.value.splice(idx, 1, { role: 'assistant', content: String(full || '') })
        scrollToBottom() // 流式更新时持续滚动到底部
      })
      messages.value.splice(idx, 1, { role: 'assistant', content: String(final || '') || '（暂无内容）', timestamp: messages.value[idx].timestamp })
      parsePeroStatus(String(final || ''))
      await parseAndSaveMemory(String(final || ''), messages.value[idx].timestamp)
      
      // 发送聊天事件到 Live2D 气泡
      window.dispatchEvent(new CustomEvent('ppc:chat', { detail: cleanMessageContent(String(final || '')) }))

      persistMessages()
      scrollToBottom() // 最终消息更新后滚动到底部
    } else {
      const r = await chatApi(baseReq, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value })
      messages.value.splice(idx, 1, { role: 'assistant', content: String(r?.content || '') || '（暂无内容）', timestamp: messages.value[idx].timestamp })
      parsePeroStatus(String(r?.content || ''))
      await parseAndSaveMemory(String(r?.content || ''), messages.value[idx].timestamp)
      
      // 发送聊天事件到 Live2D 气泡
      window.dispatchEvent(new CustomEvent('ppc:chat', { detail: cleanMessageContent(String(r?.content || '')) }))

      persistMessages()
      scrollToBottom() // 消息更新后滚动到底部
    }
  } catch (e) {
    const m = e?.response?.data?.detail || e?.message || '请求失败'
    messages.value.splice(idx, 1, { role: 'assistant', content: `错误：${m}` })
    persistMessages()
  } finally {
    text.value = ''
    isLoading.value = false
  }
}

// 删除消息函数（按需删除：仅删除选中的消息及其关联的 AI 回复轮次，不再强制级联删除后续内容）
async function deleteMessageAt(idx) {
  try { 
    if (idx < 0 || idx >= messages.value.length) return
    
    // 确定要删除的索引范围
    let indicesToDelete = [idx]
    
    // 如果点击的是用户消息，且下一条是 AI 回复，则成对删除
    if (messages.value[idx].role === 'user' && idx + 1 < messages.value.length && messages.value[idx + 1].role === 'assistant') {
      indicesToDelete.push(idx + 1)
    } 
    // 如果点击的是 AI 回复，且前一条是用户消息，则成对删除
    else if (messages.value[idx].role === 'assistant' && idx > 0 && messages.value[idx - 1].role === 'user') {
      indicesToDelete.unshift(idx - 1)
    }

    // 收集要删除的时间戳，用于同步删除记忆
    const toDeleteTimestamps = indicesToDelete.map(i => messages.value[i].timestamp).filter(Boolean)

    // 修复 Bug：同步清理已触发但尚未手动删除的提醒和话题
    indicesToDelete.forEach(i => {
      const msg = messages.value[i]
      if (msg.role === 'assistant') {
        // 检查并清理 Reminder
        const reminderRegex = /<REMINDER>([\s\S]*?)<\/REMINDER>/g
        let rMatch
        while ((rMatch = reminderRegex.exec(msg.content)) !== null) {
          try {
            const data = JSON.parse(rMatch[1].trim())
            const rIdx = reminders.value.findIndex(r => r.time === data.time && r.task === data.task)
            if (rIdx !== -1) {
              deleteReminder(rIdx) // 使用现有的带通知取消逻辑的函数
            }
          } catch (e) {}
        }
        
        // 检查并清理 Topic
        const topicRegex = /<TOPIC>([\s\S]*?)<\/TOPIC>/g
        let tMatch
        while ((tMatch = topicRegex.exec(msg.content)) !== null) {
          try {
            const data = JSON.parse(tMatch[1].trim())
            const tIdx = topics.value.findIndex(t => t.time === data.time && t.topic === data.topic)
            if (tIdx !== -1) {
              deleteTopic(tIdx) // 使用现有的带通知取消逻辑的函数
            }
          } catch (e) {}
        }
      }
    })
    
    // 执行删除：由于是按需删除，我们使用 filter 重新构建数组，而不是 splice 级联
    messages.value = messages.value.filter((_, i) => !indicesToDelete.includes(i))
    
    // 同步删除数据库中的关联记忆
    for (const ts of toDeleteTimestamps) {
      await deleteMemoriesByMsgTimestamp(ts)
    }

    // 状态恢复：如果删除了最后的消息，需要根据剩余的最后一条 AI 消息恢复 Pero 的状态
    const lastAssistantMsg = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (lastAssistantMsg) {
      parsePeroStatus(lastAssistantMsg.content)
    } else if (messages.value.length === 0) {
      // 如果消息全删了，重置状态
      resetPeroState()
    }
    
    persistMessages()
    // 只有在历史记录面板没打开时才滚动（虽然删除通常在历史面板触发）
    if (!showHistory.value) scrollToBottom() 
  } catch(e) {
    console.error('删除消息失败:', e)
  }
}

// 重置 Pero 状态
function resetPeroState() {
  localStorage.removeItem('ppc.waifu.texts')
  localStorage.removeItem('ppc.mood')
  localStorage.removeItem('ppc.energy')
  localStorage.removeItem('ppc.vibe')
  localStorage.removeItem('ppc.mind')
  window.dispatchEvent(new CustomEvent('ppc:waifu-texts-updated', { detail: {} }))
  window.dispatchEvent(new CustomEvent('ppc:mood', { detail: '' }))
  window.dispatchEvent(new CustomEvent('ppc:vibe', { detail: '' }))
  window.dispatchEvent(new CustomEvent('ppc:mind', { detail: '' }))
}

// 复制消息函数
async function copyMessage(m) {
  const t = cleanMessageContent(String(m?.content || ''))
  try { 
    await navigator.clipboard.writeText(t)
    // 可以添加一个提示，告诉用户复制成功
    console.log('消息已复制到剪贴板')
  } catch(_) {
    try {
      const ta = document.createElement('textarea'); 
      ta.value = t; 
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta); 
      ta.select(); 
      document.execCommand('copy'); 
      document.body.removeChild(ta)
      console.log('消息已复制到剪贴板（备用方法）')
    } catch(_) {
      console.error('复制失败')
    }
  }
}

// 重新生成消息函数
async function regenerateAt(idx) {
  try {
    const msg = messages.value[idx]
    if (!msg || msg.role !== 'assistant' || isLoading.value) return
    
    isLoading.value = true
    // 确保索引有效
    if (idx < 0 || idx >= messages.value.length) return
    
    // 设置加载状态
    const originalTimestamp = msg.timestamp || Date.now()
    messages.value.splice(idx, 1, { role: 'assistant', content: '__loading__', timestamp: originalTimestamp })
    
    // 发送“正在思考”状态到 Live2D 气泡
    window.dispatchEvent(new CustomEvent('ppc:chat', { detail: 'Pero正在思考中...' }))
    
    scrollToBottom() // 滚动到底部显示加载状态
    
    // 获取提示词并设置回退逻辑
    const defaults = await getDefaultPrompts()
    const systemPrompt = String(lsGet('ppc.systemPrompt', '') || '').trim() || defaults.system_prompt_default
    const personaText = String(lsGet('ppc.personaText', '') || '').trim() || defaults.persona_prompt_default
    const postSystemPrompt = String(lsGet('ppc.postSystemPrompt', '') || '').trim() || defaults.post_prompt_default
    const userName = String(lsGet('ppc.userName', '') || '').trim()
    const userPersona = String(lsGet('ppc.userPersonaText', '') || '').trim()
    
    // 构建请求消息，添加提示词
    // 根据设置的记忆轮次截断历史记录（1轮 = 1对消息）
    const limitCount = memoryRounds.value * 2
    let baseReq = messages.value.slice(0, idx).slice(-limitCount)
    
    // 注入当前时间
    baseReq = [{ role: 'system', content: getEnvPrompt() }, ...baseReq]
    
    // 检索并注入长期记忆（获取上一条用户消息作为检索词）
    const lastUserMsg = baseReq.slice().reverse().find(m => m.role === 'user')?.content || ''
    const relevantMemories = await getRelevantMemories(lastUserMsg)
    if (relevantMemories.length > 0) {
      const memoryPrompt = `<LONG_TERM_MEMORY>\n${relevantMemories.map(m => `[${m.realTime || '未知时间'}] ${m.content}`).join('\n')}\n</LONG_TERM_MEMORY>`
      baseReq = [{ role: 'system', content: memoryPrompt }, ...baseReq]
    }
    
    // 如果有系统提示词，添加到消息开头
    if (systemPrompt && !baseReq.some(m => m.role === 'system' && m.content.includes(systemPrompt))) {
      baseReq = [{ role: 'system', content: systemPrompt }, ...baseReq]
    }
    
    // 如果有人设提示词，添加到系统提示词之后或消息开头
    if (personaText && !baseReq.some(m => m.content.includes(personaText))) {
      const systemIndex = baseReq.findIndex(m => m.role === 'system')
      if (systemIndex >= 0) {
        baseReq.splice(systemIndex + 1, 0, { role: 'system', content: personaText })
      } else {
        baseReq = [{ role: 'system', content: personaText }, ...baseReq]
      }
    }

    // 如果有用户设定，添加到系统/人设提示词之后
    if (userName || userPersona) {
      const userSettingPrompt = `[User Info]\nName: ${userName || 'User'}\nDescription: ${userPersona || 'No description'}`
      if (!baseReq.some(m => m.content.includes(userSettingPrompt))) {
        let lastSystemIndex = -1
        for (let i = 0; i < baseReq.length; i++) {
          if (baseReq[i].role === 'system') lastSystemIndex = i
          else break // 只在开头的系统消息序列中寻找
        }
        baseReq.splice(lastSystemIndex + 1, 0, { role: 'system', content: userSettingPrompt })
      }
    }
    
    // 如果有后置提示词，添加到用户消息之后
    if (postSystemPrompt && baseReq.length > 0) {
      const lastUserIndex = baseReq.map(m => m.role).lastIndexOf('user')
      if (lastUserIndex >= 0) {
        const userMsg = baseReq[lastUserIndex].content
        if (!userMsg.includes(postSystemPrompt)) {
          baseReq[lastUserIndex] = {
            role: 'user',
            content: `${userMsg}\n\n${postSystemPrompt}`
          }
        }
      }
    }
    
    try {
      if (stream.value) {
        const final = await chatStream(baseReq, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value }, (_, full) => {
          messages.value.splice(idx, 1, { role: 'assistant', content: String(full || ''), timestamp: originalTimestamp })
          scrollToBottom() // 流式更新时持续滚动到底部
        })
        messages.value.splice(idx, 1, { role: 'assistant', content: String(final || '') || '（暂无内容）', timestamp: originalTimestamp })
        parsePeroStatus(String(final || ''))
        await parseAndSaveMemory(String(final || ''), originalTimestamp)
        
        // 发送聊天事件到 Live2D 气泡
        window.dispatchEvent(new CustomEvent('ppc:chat', { detail: cleanMessageContent(String(final || '')) }))

        persistMessages()
        scrollToBottom() // 最终消息更新后滚动到底部
      } else {
        const r = await chatApi(baseReq, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value })
        messages.value.splice(idx, 1, { role: 'assistant', content: String(r?.content || '') || '（暂无内容）', timestamp: originalTimestamp })
        parsePeroStatus(String(r?.content || ''))
        await parseAndSaveMemory(String(r?.content || ''), originalTimestamp)
        
        // 发送聊天事件到 Live2D 气泡
        window.dispatchEvent(new CustomEvent('ppc:chat', { detail: cleanMessageContent(String(r?.content || '')) }))

        persistMessages()
        scrollToBottom() // 消息更新后滚动到底部
      }
    } catch (error) {
      console.error('重新生成失败:', error)
      messages.value.splice(idx, 1, { role: 'assistant', content: '重新生成失败，请重试' })
      persistMessages()
    } finally {
      isLoading.value = false
    }
  } catch (error) {
    console.error('重新生成出错:', error)
    isLoading.value = false
  }
}

onMounted(() => {
  const saved = lsGet('ppc.messages', [])
  if (Array.isArray(saved)) {
    messages.value = saved
      .filter(m => m && typeof m === 'object' && typeof m.role === 'string')
      .map(m => ({ 
        role: String(m.role), 
        content: String(m.content || ''),
        timestamp: m.timestamp // 恢复时间戳用于关联记忆
      }))
  }
  const base = String(lsGet('ppc.apiBase', apiBase.value) || '').trim()
  const model = String(lsGet('ppc.modelName', modelName.value) || '').trim()
  const ms = lsGet('ppc.modelSettings', null)
  if (base) apiBase.value = base
  if (model) modelName.value = model
  if (ms && typeof ms === 'object') {
    if (ms.temperature !== undefined) temperature.value = Number(ms.temperature)
    if (ms.topP !== undefined) topP.value = Number(ms.topP)
    if (ms.frequencyPenalty !== undefined) frequencyPenalty.value = Number(ms.frequencyPenalty)
    if (ms.presencePenalty !== undefined) presencePenalty.value = Number(ms.presencePenalty)
    if (ms.stream !== undefined) stream.value = !!ms.stream
    if (ms.memoryRounds !== undefined) memoryRounds.value = Number(ms.memoryRounds)
  }
  // 组件挂载后滚动到底部
  setTimeout(scrollToBottom, 300)
})
</script>

<style>
.home { height: 100vh; display: flex; flex-direction: column; position: relative; overflow: hidden; background: transparent }
.hero { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  justify-content: flex-end; 
  overflow: visible; 
  z-index: 1; 
  padding-bottom: 90px; /* 增加底部间距，避开输入栏 */
}

/* 提醒气泡样式 */
.reminder-bubbles-container {
  position: absolute;
  top: 260px; /* 心理状态标签下方 */
  right: 15px;
  width: 140px;
  height: 200px;
  pointer-events: none;
  z-index: 10;
}

.reminder-bubble {
  position: absolute;
  pointer-events: auto;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(8px);
  border: 1.5px solid rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  padding: 12px;
  min-width: 60px;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 4px 15px rgba(219, 39, 119, 0.1),
    inset 0 0 10px rgba(255, 255, 255, 0.5);
  cursor: pointer;
  animation: taskBubbleFloat 4s ease-in-out infinite;
  transition: all 0.3s ease;
}

.reminder-bubble:hover {
  transform: scale(1.1);
  background: rgba(255, 255, 255, 0.6);
  box-shadow: 0 6px 20px rgba(219, 39, 119, 0.2);
}

.bubble-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 80px;
}

.task-text {
  font-family: 'ZCOOL KuaiLe', cursive;
  font-size: 12px;
  color: #db2777;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.2;
}

.time-text {
  font-size: 10px;
  color: rgba(219, 39, 119, 0.6);
  margin-top: 2px;
}

@keyframes taskBubbleFloat {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33% { transform: translate(3px, -8px) rotate(2deg); }
  66% { transform: translate(-3px, -4px) rotate(-2deg); }
}

/* 话题气泡样式 (左侧) */
.topic-bubbles-container {
  position: absolute;
  top: 280px; /* 比任务气泡稍低一点点 */
  left: 15px;
  width: 140px;
  height: 200px;
  pointer-events: none;
  z-index: 10;
}

.topic-bubble {
  position: absolute;
  pointer-events: auto;
  background: rgba(255, 255, 255, 0.25); /* 秘密态更透明 */
  backdrop-filter: blur(10px);
  border: 1.5px solid rgba(255, 255, 255, 0.4);
  border-radius: 50%; /* 秘密态是圆形的 */
  width: 60px;
  height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.15);
  cursor: pointer;
  animation: topicBubbleFloat 5s ease-in-out infinite;
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  overflow: hidden;
}

.topic-bubble.is-revealed {
  border-radius: 24px 24px 24px 4px;
  width: auto;
  height: auto;
  min-width: 80px;
  max-width: 130px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.5);
  aspect-ratio: auto;
}

.secret-icon {
  font-size: 18px;
  color: #3b82f6;
  margin-bottom: 2px;
  opacity: 0.8;
}

.topic-text {
  font-family: 'ZCOOL KuaiLe', cursive;
  font-size: 11px;
  color: #3b82f6;
  line-height: 1.2;
  text-align: center;
}

.topic-text.revealed {
  font-size: 13px;
  font-weight: bold;
}

.bubble-actions {
  margin-top: 6px;
  width: 100%;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid rgba(59, 130, 246, 0.1);
  padding-top: 4px;
}

.remove-icon {
  font-size: 12px;
  color: rgba(59, 130, 246, 0.5);
  transition: color 0.3s;
}

.remove-icon:hover {
  color: #ef4444;
}

@keyframes topicBubbleFloat {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(-4px, 6px) rotate(-1deg); }
}

.inputbar-mini {
  position: fixed;
  bottom: 30px;
  left: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 100;
}

.expand-btn {
  flex: 1;
  height: 50px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 25px;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.expand-btn:active {
  transform: scale(0.95);
  background: rgba(255, 255, 255, 0.25);
}

.mini-tools {
  display: flex;
  gap: 8px;
}

.tool-btn-mini {
  width: 50px;
  height: 50px;
  border-radius: 25px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tool-btn-mini:active {
  transform: scale(0.9);
}

/* 展开后的样式 */
.expanded-input-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(5px);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
}

.expanded-input-card {
  width: 100%;
  background: rgba(28, 28, 30, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px 24px 0 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  color: #fff;
  font-weight: 600;
  font-size: 17px;
}

.close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 16px;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.expanded-textarea {
  width: 100%;
  height: 150px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 16px;
  color: white;
  font-size: 16px;
  resize: none;
  outline: none;
  font-family: inherit;
}

.expanded-textarea:focus {
  border-color: #409eff;
  background: rgba(255, 255, 255, 0.08);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

.send-btn {
  background: #409eff;
  border: none;
  padding: 10px 24px;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

/* 动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(100%);
}

.fade-slide-enter-to,
.fade-slide-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.bubble-container { display: grid; gap: 2px }
.bubble { 
  max-width: 75%; 
  position: relative; 
  border-radius: 20px; 
  padding: 12px 16px; 
  margin: 8px 0; 
  word-break: break-word; 
  line-height: 1.6; 
  font-size: 15px; 
  box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
  transition: all .2s ease;
  animation: bubbleFloat 5.6s ease-in-out infinite;
}
.bubble.user { 
  margin-left: auto; 
  background: linear-gradient(135deg, #3b82f6, #2563eb); 
  color: #fff; 
  border: none;
  font-family: 'Quicksand', sans-serif;
  border-radius: 20px 20px 4px 20px;
}
.bubble.assistant { 
  margin-right: auto; 
  background: rgba(255, 255, 255, 0.4); 
  backdrop-filter: blur(12px) saturate(150%);
  color: #db2777; 
  border: 1.5px solid rgba(255, 255, 255, 0.5);
  font-family: 'ZCOOL KuaiLe', cursive;
  font-size: 17px;
  border-radius: 24px 24px 24px 8px;
  box-shadow: 
    0 8px 32px rgba(219, 39, 119, 0.1),
    inset 0 0 15px rgba(255, 255, 255, 0.5),
    inset 0 -5px 10px rgba(219, 39, 119, 0.05);
  position: relative;
}
.bubble.assistant::before {
  content: "";
  position: absolute;
  top: 6px;
  left: 12px;
  width: 20px;
  height: 10px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  transform: rotate(-15deg);
  filter: blur(1px);
  pointer-events: none;
  display: block !important;
}
.bubble.assistant::after { 
  content: ""; 
  position: absolute; 
  left: -7px; 
  bottom: 12px; 
  width: 12px; 
  height: 12px; 
  background: rgba(255, 255, 255, 0.4); 
  backdrop-filter: blur(12px);
  transform: rotate(45deg); 
  border-left: 1.5px solid rgba(255, 255, 255, 0.5); 
  border-bottom: 1.5px solid rgba(255, 255, 255, 0.5);
  z-index: -1;
}
.bubble pre { background: #1e293b; color: #e2e8f0; border-radius: 8px; padding: 8px; overflow: auto }
.bubble code { background: rgba(0,0,0,0.2); border-radius: 4px; padding: 2px 4px }
@keyframes bubbleFloat { 
  0%, 100% { transform: translateY(0) rotate(0deg); } 
  33% { transform: translateY(-4px) rotate(1deg); } 
  66% { transform: translateY(-2px) rotate(-1deg); } 
}
.bubble-tools { display: flex; gap: 6px; align-items: center; max-width: 68% }
.bubble-tools.user { margin-left: auto; justify-content: flex-end }
.bubble-tools.assistant { margin-right: auto; justify-content: flex-start }
.tool-btn { width: 22px; height: 22px; display: grid; place-items: center; border-radius: 6px; border: 1px solid #e5e7eb; background: #f9fafb; color: #6b7280 }
.tool-btn:disabled { opacity: 0.5 }
.input { height: 40px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.08); background: rgba(255, 255, 255, 0.5); backdrop-filter: blur(4px); color: #111; padding: 0 12px; transition: all 0.2s }
.input:focus { background: rgba(255, 255, 255, 0.8); border-color: #3b82f6; outline: none; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) }
.btn { width: 40px; height: 40px; display: grid; place-items: center; padding: 0; border-radius: 12px; background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff; border: none; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); cursor: pointer }
.btn-secondary { height: 40px; padding: 0 14px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.08); background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(4px); color: #374151; display: inline-flex; align-items: center; justify-content: center; white-space: nowrap; cursor: pointer; transition: all 0.2s }
.btn-secondary:hover { background: rgba(255, 255, 255, 0.8); border-color: rgba(0,0,0,0.15) }
@media (max-width: 768px) { 
  .hero { min-height: 400px }
}
</style>
