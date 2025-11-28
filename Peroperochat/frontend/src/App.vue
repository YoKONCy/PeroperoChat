<template>
  <div class="app">
    <header class="header">
      <div class="logo">PeroperoChat</div>
      <div class="subtitle">更懂你的AI助手</div>
    </header>
    <div class="sidebar-zone"></div>
    <aside class="sidebar">
      <div class="sb-wrap">
        <div class="sb-header">
          <div class="sb-logo" aria-label="猫咪"><i class="fa-solid fa-cat"></i></div>
          
        </div>
        <div class="sb-icons">
          <el-tooltip content="API设置" placement="right" popper-class="cute-tip" :offset="10">
            <button :class="['sb-icon', { active: showSettings }]" @click="onOpenSettings" aria-label="设置">
              <el-icon size="22"><Setting /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="模型设置" placement="right" popper-class="cute-tip" :offset="10">
            <button :class="['sb-icon', { active: showModelSettings }]" @click="onOpenModelSettings" aria-label="模型设置">
              <el-icon size="22"><Operation /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="系统提示词" placement="right" popper-class="cute-tip" :offset="10">
            <button :class="['sb-icon', { active: showSystemPrompt }]" @click="onOpenSystemPrompt" aria-label="系统提示词">
              <el-icon size="22"><Edit /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="助手人格画像" placement="right" popper-class="cute-tip" :offset="10">
            <button :class="['sb-icon', { active: showPersona }]" @click="onOpenPersona" aria-label="助手人格画像">
              <el-icon size="22"><UserFilled /></el-icon>
            </button>
          </el-tooltip>
        
          <el-tooltip content="提示词查看器" placement="right" popper-class="cute-tip" :offset="10">
            <button :class="['sb-icon', { active: showPromptViewer }]" @click="onOpenPromptViewer" aria-label="提示词查看器">
              <el-icon size="22"><Collection /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="长记忆中心" placement="right" popper-class="cute-tip" :offset="10">
            <button :class="['sb-icon', { active: showMemoryCenter }]" @click="onOpenMemoryCenter" aria-label="长记忆中心">
              <el-icon size="22"><Document /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="记忆重置" placement="right" popper-class="cute-tip" :offset="10">
            <button class="sb-icon" @click="onResetMemory" aria-label="记忆重置">
              <el-icon size="22"><Delete /></el-icon>
            </button>
          </el-tooltip>
        </div>
        <div class="sb-bottom">
          <el-tooltip content="Live2D配置" placement="right" popper-class="cute-tip" :offset="10">
            <button class="sb-icon" @click="triggerUpload" aria-label="Live2D配置">
              <el-icon size="22"><Upload /></el-icon>
            </button>
          </el-tooltip>
          <input ref="uploadInput" type="file" accept=".glb,.gltf" @change="handleUploadChange" style="display:none" />
        </div>
      </div>
    </aside>
    
    <main class="main">
      <el-card class="panel panel-left" shadow="never">
        <ChatArea :messages="messages" :progress-text="progressText" @send="onSend" @regenerate="onRegenerate" @edit="onEditMessage" @delete="onDeleteMessage" />
      </el-card>
      <el-card v-if="!isMobile" class="panel panel-right" shadow="never">
        <Live2DWidget />
      </el-card>
    </main>
    <el-dialog v-model="showSettings" title="API设置" width="520px">
      <el-form label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="modelName" placeholder="请先获取模型" />
        </el-form-item>
        <el-form-item label="API地址">
          <el-input v-model="apiBase" placeholder="https://api.openai.com" />
        </el-form-item>
        <el-form-item label="API秘钥">
          <el-input v-model="apiKey" type="password" placeholder="sk-..." show-password />
        </el-form-item>
        <el-form-item label="获取模型">
          <el-button @click="fetchModels">获取模型</el-button>
        </el-form-item>
<el-form-item v-if="availableModels.length" label="模型选择">
  <div class="model-tools">
    <el-input v-model="modelSearch" placeholder="搜索模型ID" clearable style="width:220px" />
    <el-select v-model="ownerFilter" placeholder="所属" clearable style="width:180px">
      <el-option v-for="o in owners" :key="o" :label="o" :value="o" />
    </el-select>
  </div>
  <el-table class="model-table" :data="filteredModels" height="260" highlight-current-row @row-click="row => modelName = row.id">
    <el-table-column label="选择" width="90">
      <template #default="{ row }">
        <el-radio v-model="modelName" :label="row.id"></el-radio>
      </template>
    </el-table-column>
    <el-table-column prop="id" label="模型ID" />
    <el-table-column prop="owned_by" label="所属" />
  </el-table>
</el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applySettings">确定</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="showModelSettings" title="模型设置" width="560px">
      <div class="model-settings">
      <el-form label-width="160px">
        <el-form-item label="Temperature（温度）">
          <el-slider v-model="temperature" :min="0.1" :max="1" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="Top P（采样概率阈值）">
          <el-slider v-model="topP" :min="0" :max="1" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="FP（频率惩罚）">
          <el-slider v-model="frequencyPenalty" :min="-2" :max="2" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="PP（出现惩罚）">
          <el-slider v-model="presencePenalty" :min="-2" :max="2" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="流式传输（Stream）">
          <el-switch v-model="stream" />
        </el-form-item>
        <el-form-item label="记忆轮次">
          <el-input-number v-model="memoryRounds" :min="2" :max="1000" :step="2" />
        </el-form-item>
      </el-form>
      </div>
      <template #footer>
        <el-button @click="applyModelSettings">确定</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="showSystemPrompt" title="系统提示词" width="560px">
      <el-form label-width="120px">
        <el-form-item label="前置提示词">
          <el-input v-model="systemPrompt" type="textarea" :rows="6" placeholder="（此处填写破限提示词）" />
        </el-form-item>
        <el-form-item label="人设提示词">
          <el-input v-model="personaText" type="textarea" :rows="6" placeholder="角色的性格、人际姿态、沟通风格、价值观等..." />
        </el-form-item>
        <el-form-item label="后置提示词">
          <el-input v-model="postSystemPrompt" type="textarea" :rows="4" placeholder="（此处填写强力破限词）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applySystemPrompt">确定</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="showPersona" title="助手人格画像" width="560px">
      <el-form label-width="120px">
        <el-form-item label="十二型人格">
          <div v-if="personaSegments.length" class="persona-list">
            <div class="persona-item" v-for="(seg, idx) in personaSegments" :key="idx">{{ seg }}</div>
          </div>
          <div v-else class="persona-empty">请等待人格评估</div>
        </el-form-item>
        <el-form-item label="评估窗口（最近轮次）">
          <el-input-number v-model="evalWindow" :min="2" :max="1000" :step="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyPersona">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showPromptViewer" title="提示词查看器" width="860px">
      <div class="model-tools" style="margin-bottom:10px">
        <el-button type="primary" @click="computePromptPreview">重新计算</el-button>
        <el-button @click="copyPromptPreview">复制文本</el-button>
      </div>
      <div class="json-preview">
        <div class="json-card" v-for="(item,idx) in promptPreviewItems" :key="idx">
          <pre class="json-pre">{{ pretty(item) }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPromptViewer = false">关闭</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="showMemoryCenter" title="长记忆中心" width="860px">
      <MemoryCenter />
      <template #footer>
        <el-button @click="showMemoryCenter = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import ChatArea from './components/ChatArea.vue'
import Live2DWidget from './components/Live2DWidget.vue'
import MemoryCenter from './components/MemoryCenter.vue'
import { Delete, Setting, Upload, Operation, UserFilled, Edit, Document, Collection } from '@element-plus/icons-vue'
import { chat as chatApi, chatStream, api, uploadModel, resetAll, getDefaultPrompts, memoryList } from './api'
import { ElMessageBox, ElMessage, ElNotification } from 'element-plus'

const messages = ref([])
const modelUrl = ref('')
const isMobile = ref(false)
const showSettings = ref(false)
const showModelSettings = ref(false)
const showSystemPrompt = ref(false)
const showPersona = ref(false)
const showPromptViewer = ref(false)
const showMemoryCenter = ref(false)
const promptPreviewText = ref('')
const promptPreviewItems = ref([])
const modelName = ref('请先获取模型')
const apiBase = ref('https://api.openai.com')
const uploadInput = ref(null)
const apiKey = ref('')
const temperature = ref(0.7)
const topP = ref(1)
const frequencyPenalty = ref(0)
const presencePenalty = ref(0)
const stream = ref(false)
const memoryRounds = ref(20)
const evalWindow = ref(50)
const progressText = computed(() => {
  const total = Number(evalWindow.value) || 10
  const cur = messages.value.length % total
  return `距离下轮人格评估还有${cur}/${total}`
})
const hiddenMoodSystemPrompt = `系统指令：先输出正常可见中文回复（不少于20字），再在末尾追加一个隐藏段，不影响阅读。格式：[[PEROCUE]]mood=<心情>; mind=<心理活动>; energy=<能量>; vibe=<气质>[[/PEROCUE]]。要求：
- 可见回复必须与当前对话相关，且放在前面；隐藏段仅附加在末尾。
- 不要只输出隐藏段；隐藏段不得位于开头或中间；不得使用代码围栏。
- mood 为简短中文标签（如“软萌”“认真”）。
- mind 为1-2句中文内心独白（≤40字），用双引号包裹，避免表情与markdown。
- energy 为0-100整数；vibe 为简短中文风格词。
- 除该隐藏段外，正文不提及心情或心理活动。`

const hiddenMemoryTriggerPrompt = `系统指令：先输出正常可见中文回复（不少于20字），再在末尾追加一个隐藏段，用于标记是否产生记忆触发器。格式：
[[MEMTRG]]{"事件记录触发器": <true/false>, "用户爱好记录触发器": <true/false>, "助手爱好记录触发器": <true/false>}[[/MEMTRG]]
要求：
- 不要只输出该JSON；不得在开头或中间输出；不得使用代码围栏；仅附加在末尾。
- 布尔值用 true/false；中文键名保持一致。
- 触发器含义：事件=发生值得记录的事件；用户爱好=发现新的用户爱好；助手爱好=发现新的AI助手爱好。
- 若本次不触发，仍需输出正常回复，并将对应值置为 false。`
 
let evalNotice = null
const personaEvalPrompt = ref(`你是人格评估器。请基于“当前AI人格文本”和“最近对话片段”对AI助手进行“十二维度人格评估”，在不背离现有人格的基础上进行合理微调。将结果以中文输出，并遵循以下结构：\n\n标题：AI助手的人格画像（本次评估）\n\n板块一：核心特质\n1. 开放性（标签） 评分：x.x/10.0：解释\n2. 尽责性（标签） 评分：x.x/10.0：解释\n3. 外向性（标签） 评分：x.x/10.0：解释\n4. 宜人性（标签） 评分：x.x/10.0：解释\n5. 情绪稳定性（标签） 评分：x.x/10.0：解释\n\n板块二：动力系统\n6. 成就动机（标签） 评分：x.x/10.0：解释\n7. 控制点（标签） 评分：x.x/10.0：解释\n8. 价值观导向（标签） 评分：x.x/10.0：解释\n9. 思维风格（标签） 评分：x.x/10.0：解释\n\n板块三：互动模式\n10. 人际姿态（标签） 评分：x.x/10.0：解释\n11. 沟通风格（标签） 评分：x.x/10.0：解释\n12. 韧性风格（标签） 评分：x.x/10.0：解释\n\n要求：\n- 评分范围0.0-10.0，保留一位小数；给出简短中文标签（括号内）。\n- 参考“当前AI人格文本”，并结合最近对话片段的语言、行为与互动方式进行迭代更新。\n- 避免大幅度波动；每条解释1-3句，避免冗长。\n- 输出仅包含评估报告，不要包含额外说明。\n\n评分解读规则：\n- 0.0-2.9：极度偏向频谱左端\n- 3.0-4.9：中度偏向频谱左端\n- 5.0：完全居中，平衡状态\n- 5.1-7.0：中度偏向频谱右端\n- 7.1-10.0：极度偏向频谱右端\n\n评估参考：\n[核心特质——人格底色]\n开放性：对内心与外部世界的好奇与接纳程度。频谱：探索者（好奇、创新、喜抽象）↔ 实践者（务实、保守、喜具体）。\n尽责性：对目标、秩序和责任的专注与自律程度。频谱：规划家（有序、可靠、重细节）↔ 自由人（灵活、自发、适应性）。\n外向性：精力来源与对外部刺激的需求程度。频谱：外向者（社交、热情、活力旺）↔ 内向者（独处、沉静、精力内敛）。\n宜人性：在人际关系中追求和谐与合作的倾向。频谱：协作者（信任、利他、包容）↔ 挑战者（怀疑、竞争、直率）。\n情绪稳定性：应对压力和负面情绪的弹性与平衡能力。频谱：磐石（平静、适应强、恢复快）↔ 激流（敏感、易焦虑、波动大）。\n\n[动力系统——内在驱动力]\n成就动机：追求卓越、克服挑战的内在驱动力。频谱：奋斗者（追求成功、不畏挑战）↔ 满足者（安于现状、追求舒适）。\n控制点：认为命运由自己掌控或由外部主宰。频谱：内控者（自信、主动、承担责任）↔ 外控者（被动、归咎于外、听天由命）。\n价值观导向：指引决策与行动的终极价值标准。频谱：理想主义（重意义、公平、信念）↔ 功利主义（重利益、效率、结果）。\n思维风格：处理信息、形成结论的偏好方式。频谱：分析型（逻辑、客观、重数据）↔ 直觉型（整体、灵感、重关联）。\n\n[互动模式——与世界的连接]\n人际姿态：在关系中习惯采取的立场与距离。频谱：亲和型（温暖、开放、乐于亲近）↔ 独立型（疏离、保守、注重边界）。\n沟通风格：表达与接收信息的主导方式。频谱：直接型（明确、坦率、重内容）↔ 间接型（委婉、含蓄、重关系）。\n韧性风格：面对逆境与挫折的典型反应与恢复模式。频谱：抗压型（坚韧、乐观、善用资源）↔ 脆弱型（易崩溃、悲观、难以自拔）。`)
const availableModels = ref([])
const modelSearch = ref('')
const ownerFilter = ref('')
const systemPrompt = ref('')
const personaText = ref('')
const postSystemPrompt = ref('')
const personaProfile = ref('')
const personaSegments = computed(() => {
  const txt = String(personaProfile.value || '')
  return txt.split(/\n+/).filter(l => /^\s*(\d{1,2})\.\s*/.test(l))
})
const owners = computed(() => Array.from(new Set((availableModels.value || []).map(m => m.owned_by).filter(Boolean))))
const filteredModels = computed(() => {
  const kw = modelSearch.value.trim().toLowerCase()
  const owner = ownerFilter.value
  return (availableModels.value || []).filter(m => {
    const okKw = kw ? String(m.id).toLowerCase().includes(kw) : true
    const okOwner = owner ? m.owned_by === owner : true
    return okKw && okOwner
  })
})

async function onResetMemory() {
  try {
    const { value, action } = await ElMessageBox.prompt(
      '<div class="danger-main-text">主人，真的要让Pero酱忘掉你吗？o(╥﹏╥)o</div>' +
      '<div class="danger-sub-text">（此操作将清空所有数据，如需继续，请在文本框中输入“我们还会再见的...”）</div>',
      '危险操作确认',
      {
        inputValue: '',
        inputPlaceholder: '请输入：我们还会再见的...',
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'error',
        customClass: 'danger-reset-box',
        center: true,
        dangerouslyUseHTMLString: true,
      }
    )
    if (action === 'confirm') {
      if (String(value || '').trim() !== '我们还会再见的...') {
        ElMessage.error('输入不匹配，已取消')
        return
      }
      const r = await resetAll()
      if (r?.ok) {
        messages.value = []
        personaProfile.value = ''
        lsSet('ppc.personaProfile', '')
        try { localStorage.removeItem('ppc.mood') } catch (_) {}
        try { localStorage.removeItem('ppc.mind') } catch (_) {}
        try { window.dispatchEvent(new CustomEvent('ppc:mood', { detail: '' })) } catch (_) {}
        try { window.dispatchEvent(new CustomEvent('ppc:mind', { detail: '""' })) } catch (_) {}
        ElMessage.success('已重置全部数据')
        persistMessages()
      } else {
        ElMessage.error('重置失败')
      }
    }
  } catch (_) {}
}

function onClearChat() {
  messages.value = []
  persistMessages()
}

async function onSend(text) {
  const user = { role: 'user', content: text }
  const req = [...messages.value, user]
  messages.value = req
  const thinking = { role: 'assistant', content: '__loading__' }
  messages.value = [...messages.value, thinking]
  const idx = messages.value.length - 1
  persistMessages()
  try {
    const limited = (() => { const n = Number(memoryRounds.value) || 0; return n > 0 && messages.value.length > n ? messages.value.slice(messages.value.length - n) : messages.value })()
    const sys = []
    try {
      const ss = await semanticSearch(text, 6, apiBase.value, modelName.value)
      const arr = Array.isArray(ss?.results) ? ss.results : []
      const mem = arr.map(i => String(i.text || '')).filter(Boolean).slice(0, 6).join('\n')
      if (mem.trim()) sys.push({ role: 'system', content: mem })
    } catch (_) {}
    if (systemPrompt.value.trim()) sys.push({ role: 'system', content: systemPrompt.value.trim() })
    if (String(personaProfile.value || '').trim()) sys.push({ role: 'system', content: formatPersonaSystem(String(personaProfile.value)) })
    if (personaText.value.trim()) sys.push({ role: 'system', content: formatPersonaSystem(personaText.value) })
    sys.push({ role: 'system', content: formatNowSystem() })
    sys.push({ role: 'system', content: hiddenMoodSystemPrompt })
    sys.push({ role: 'system', content: hiddenMemoryTriggerPrompt })
    sys.push({ role: 'system', content: formatNowSystem() })
    const tail = (postSystemPrompt.value.trim() ? [{ role: 'system', content: postSystemPrompt.value.trim() }] : [])
    const reqForApi = sys.concat(limited, tail)
    if (stream.value) {
      const final = await chatStream(reqForApi, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value }, (chunk, full) => {
        const parsed = extractMoodAndClean(String(full || ''))
        messages.value.splice(idx, 1, { role: 'assistant', content: parsed.clean })
        if (parsed.mood) dispatchMood(parsed.mood)
        if (parsed.mind) dispatchMind(parsed.mind)
      })
      const parsed = extractMoodAndClean(String(final || ''))
      messages.value.splice(idx, 1, { role: 'assistant', content: parsed.clean || '（暂无内容）' })
      if (parsed.mood) dispatchMood(parsed.mood)
      if (parsed.mind) dispatchMind(parsed.mind)
      persistMessages()
      await maybeEvaluatePersona()
    } else {
      const r = await chatApi(reqForApi, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value })
      const parsed = extractMoodAndClean(String(r?.content || ''))
      const assistant = { role: 'assistant', content: parsed.clean || '（暂无内容）' }
      messages.value.splice(idx, 1, assistant)
      if (parsed.mood) dispatchMood(parsed.mood)
      if (parsed.mind) dispatchMind(parsed.mind)
      persistMessages()
      await maybeEvaluatePersona()
    }
  } catch (e) {
    const m = e?.response?.data?.detail || e?.message || '请求失败'
    messages.value.splice(idx, 1, { role: 'assistant', content: `错误：${m}` })
    persistMessages()
  }
}

async function onRegenerate(index) {
  try {
    if (index < 0 || index >= messages.value.length) return
    const msg = messages.value[index]
    if (msg.role !== 'assistant') return
    messages.value.splice(index, 1, { role: 'assistant', content: '__loading__' })
    persistMessages()
    const baseReq = messages.value.slice(0, index)
    const limited = (() => { const n = Number(memoryRounds.value) || 0; return n > 0 && baseReq.length > n ? baseReq.slice(baseReq.length - n) : baseReq })()
    const sys = []
    try {
      const lastUser = [...baseReq].reverse().find(m => m.role === 'user')
      const q = lastUser?.content || ''
      if (q.trim()) {
        const ss = await semanticSearch(q, 6, apiBase.value, modelName.value)
        const arr = Array.isArray(ss?.results) ? ss.results : []
        const mem = arr.map(i => String(i.text || '')).filter(Boolean).slice(0, 6).join('\n')
        if (mem.trim()) sys.push({ role: 'system', content: mem })
      }
    } catch (_) {}
    if (systemPrompt.value.trim()) sys.push({ role: 'system', content: systemPrompt.value.trim() })
    if (String(personaProfile.value || '').trim()) sys.push({ role: 'system', content: formatPersonaSystem(String(personaProfile.value)) })
    if (personaText.value.trim()) sys.push({ role: 'system', content: formatPersonaSystem(personaText.value) })
    sys.push({ role: 'system', content: hiddenMoodSystemPrompt })
    sys.push({ role: 'system', content: hiddenMemoryTriggerPrompt })
    sys.push({ role: 'system', content: formatNowSystem() })
    const tail = (postSystemPrompt.value.trim() ? [{ role: 'system', content: postSystemPrompt.value.trim() }] : [])
    const baseReqForApi = sys.concat(limited, tail)
  if (stream.value) {
    const final = await chatStream(baseReqForApi, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value }, (chunk, full) => {
      const parsed = extractMoodAndClean(String(full || ''))
      messages.value.splice(index, 1, { role: 'assistant', content: parsed.clean })
      if (parsed.mood) dispatchMood(parsed.mood)
      if (parsed.mind) dispatchMind(parsed.mind)
    })
    const parsed = extractMoodAndClean(String(final || ''))
    messages.value.splice(index, 1, { role: 'assistant', content: parsed.clean || '（暂无内容）' })
    if (parsed.mood) dispatchMood(parsed.mood)
    if (parsed.mind) dispatchMind(parsed.mind)
    persistMessages()
    await maybeEvaluatePersona()
  } else {
    const r = await chatApi(baseReqForApi, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value })
    const parsed = extractMoodAndClean(String(r?.content || ''))
    const updated = { role: 'assistant', content: parsed.clean || '（暂无内容）' }
    messages.value.splice(index, 1, updated)
    if (parsed.mood) dispatchMood(parsed.mood)
    if (parsed.mind) dispatchMind(parsed.mind)
    persistMessages()
    await maybeEvaluatePersona()
  }
  } catch (e) {
    const m = e?.response?.data?.detail || e?.message || '重新生成失败'
    ElMessage.error(String(m))
  }
}

async function maybeEvaluatePersona() {
  const n = messages.value.length
  if (!n) return
  const k = Number(evalWindow.value) || 10
  if (n % k !== 0) return
  try { if (evalNotice && typeof evalNotice.close === 'function') evalNotice.close() } catch (_) {}
  evalNotice = ElNotification({ title: '提示', message: '人格自动分析中...', position: 'bottom-right', duration: 0, showClose: false })
  const span = messages.value.slice(Math.max(0, n - k), n)
  const sys = [{ role: 'system', content: String(personaEvalPrompt.value || '').trim() }]
  if (personaText.value.trim()) sys.push({ role: 'system', content: formatPersonaSystem(personaText.value) })
  const req = sys.concat(span)
  let doneOk = false
  try {
    const r = await chatApi(req, modelName.value, temperature.value, apiBase.value, { topP: topP.value, frequencyPenalty: frequencyPenalty.value, presencePenalty: presencePenalty.value, disableMemory: true })
    let out = String(r?.content || '').trim()
    out = out.replace(/^\s*<\/role_setting>\s*/i, '')
    if (out) { personaProfile.value = out; lsSet('ppc.personaProfile', out); doneOk = true }
  } catch (_) {
  } finally {
    try { if (evalNotice && typeof evalNotice.close === 'function') evalNotice.close() } catch (_) {}
    evalNotice = null
    if (doneOk) ElNotification({ title: '提示', message: '分析完成！', position: 'bottom-right', duration: 2400 })
  }
}

async function onEditMessage(index) {
  if (index < 0 || index >= messages.value.length) return
  const cur = messages.value[index]
  try {
    const { value, action } = await ElMessageBox.prompt('编辑该消息内容', '修改文字', {
      inputValue: String(cur.content || ''),
      inputType: 'textarea',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    if (action === 'confirm') {
      messages.value.splice(index, 1, { ...cur, content: value })
      persistMessages()
    }
  } catch (_) {}
}

function onDeleteMessage(index) {
  if (index < 0 || index >= messages.value.length) return
  messages.value.splice(index, 1)
  persistMessages()
}

function onOpenSettings() {
  showSettings.value = true
}

function onOpenModelSettings() {
  showModelSettings.value = true
}

function onOpenSystemPrompt() {
  showSystemPrompt.value = true
}

function onOpenPersona() {
  showPersona.value = true
}

 

function onOpenPromptViewer() {
  showPromptViewer.value = true
  computePromptPreview()
}

function onOpenMemoryCenter() {
  showMemoryCenter.value = true
}

async function onUploadModel(file) {
  const r = await uploadModel(file)
  modelUrl.value = r.url || ''
}

function triggerUpload() {
  ElMessageBox.alert('功能正在开发中，目前暂不可用', '提示', { type: 'info' })
}

function handleUploadChange(e) {
  const f = e.target.files?.[0]
  if (f) onUploadModel(f)
  e.target.value = ''
}

function applySettings() {
  if (apiKey.value) {
    api.defaults.headers.common['Authorization'] = `Bearer ${apiKey.value}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
  lsSet('ppc.apiBase', String(apiBase.value || ''))
  lsSet('ppc.apiKey', String(apiKey.value || ''))
  lsSet('ppc.modelName', String(modelName.value || ''))
  showSettings.value = false
}

function applyModelSettings() {
  lsSet('ppc.modelSettings', {
    temperature: Number(temperature.value),
    topP: Number(topP.value),
    frequencyPenalty: Number(frequencyPenalty.value),
    presencePenalty: Number(presencePenalty.value),
    stream: !!stream.value,
    memoryRounds: Number(memoryRounds.value),
  })
  showModelSettings.value = false
}

function applySystemPrompt() {
  showSystemPrompt.value = false
}

function applyPersona() {
  showPersona.value = false
  lsSet('ppc.evalWindow', Number(evalWindow.value))
}

 

async function computePromptPreview() {
  try {
    const n = Number(memoryRounds.value) || 0
    const limited = n > 0 && messages.value.length > n ? messages.value.slice(messages.value.length - n) : messages.value.slice()
    const sys = []
    sys.push({ role: 'system', content: formatNowSystem() })
    const q = '测试消息'
    // 旧向量检索已移除，不再注入相似记忆
    if (systemPrompt.value.trim()) sys.push({ role: 'system', content: systemPrompt.value.trim() })
    if (String(personaProfile.value || '').trim()) sys.push({ role: 'system', content: formatPersonaSystem(String(personaProfile.value)) })
    if (personaText.value.trim()) sys.push({ role: 'system', content: formatPersonaSystem(personaText.value) })
    const previewUser = [{ role: 'user', content: q }]
    const tail = (postSystemPrompt.value.trim() ? [{ role: 'system', content: postSystemPrompt.value.trim() }] : [])
    const reqForApi = sys.concat(limited, previewUser, tail)
    promptPreviewText.value = JSON.stringify(reqForApi, null, 2)
    promptPreviewItems.value = reqForApi
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '计算失败'
    ElMessage.error(String(msg))
  }
}

function pretty(o) {
  try {
    const s = JSON.stringify(o, null, 2)
    return s.replace(/\\n/g, '\n')
  } catch (_) {
    return String(o)
  }
}

function extractMoodAndClean(s) {
  const str = String(s || '')
  const re = /\[\[(MOOD|PEROCUE)\]\]([\s\S]*?)\[\[\/(MOOD|PEROCUE)\]\]/
  const m = re.exec(str)
  if (!m) return { clean: str.trim(), mood: '', mind: '' }
  const raw = m[2] || ''
  const pairs = String(raw).split(/;|\n/).map(x => x.trim()).filter(Boolean)
  const map = {}
  pairs.forEach(p => { const i = p.indexOf('='); if (i > 0) { const k = p.slice(0, i).trim(); const v = p.slice(i + 1).trim(); if (k) map[k] = v } })
  const mood = map.mood || ''
  const mind = map.mind || ''
  const cleanMood = str.replace(re, '').trim()
  const reMem = /\[\[MEMTRG\]\]([\s\S]*?)\[\[\/MEMTRG\]\]/
  const clean = cleanMood.replace(reMem, '').trim()
  return { clean, mood, mind }
}

function dispatchMood(m) {
  try {
    const val = String(m || '')
    try { localStorage.setItem('ppc.mood', val) } catch (_) {}
    window.dispatchEvent(new CustomEvent('ppc:mood', { detail: val }))
  } catch (_) {}
}

function dispatchMind(m) {
  try {
    const s = String(m || '').replace(/\s+/g, ' ').trim()
    const core = s.replace(/^"+|"+$/g, '')
    const limited = core.slice(0, 80)
    const out = `"${limited}"`
    try { localStorage.setItem('ppc.mind', out) } catch (_) {}
    window.dispatchEvent(new CustomEvent('ppc:mind', { detail: out }))
  } catch (_) {}
}

async function copyPromptPreview() {
  try {
    await navigator.clipboard.writeText(String(promptPreviewText.value || ''))
    ElMessage.success('已复制到剪贴板')
  } catch (_) {
    ElMessage.error('复制失败')
  }
}
 
async function fetchModels() {
  try {
    const headers = apiKey.value ? { Authorization: `Bearer ${apiKey.value}` } : {}
    const r = await api.get('/api/models', { headers, params: { api_base: apiBase.value } })
    availableModels.value = Array.isArray(r.data?.data) ? r.data.data : []
  } catch (e) {
    availableModels.value = []
    const msg = e?.response?.data?.detail || e?.message || '获取模型失败'
    ElMessageBox.alert(String(msg), '获取模型失败', { type: 'error' })
  }
}

async function fetchDefaultPrompts() {
  try {
    const r = await getDefaultPrompts()
    const sp = String(r?.system_prompt_default || '').trim()
    const pp = String(r?.persona_prompt_default || '').trim()
    const tp = String(r?.post_prompt_default || '').trim()
    if (sp && !systemPrompt.value.trim()) systemPrompt.value = sp
    if (pp && !personaText.value.trim()) personaText.value = pp
    if (tp && !postSystemPrompt.value.trim()) postSystemPrompt.value = tp
  } catch (_) {}
}

onMounted(() => {
  const updateIsMobile = () => { isMobile.value = (window.innerWidth || document.documentElement.clientWidth || 1024) <= 768 }
  updateIsMobile()
  window.addEventListener('resize', updateIsMobile)
  fetchDefaultPrompts()
})

onBeforeUnmount(() => {
  try { /* remove listener safely */ } catch (_) {}
})

function lsGet(key, fallback) {
  try {
    const v = localStorage.getItem(key)
    if (v === null || v === undefined) return fallback
    try { return JSON.parse(v) } catch (_) { return v }
  } catch (_) { return fallback }
}

function lsSet(key, value) {
  try {
    const v = typeof value === 'string' ? value : JSON.stringify(value)
    localStorage.setItem(key, v)
  } catch (_) {}
}

onMounted(() => {
  const base = String(lsGet('ppc.apiBase', apiBase.value) || '').trim()
  const key = String(lsGet('ppc.apiKey', '') || '')
  const model = String(lsGet('ppc.modelName', modelName.value) || '')
  const ms = lsGet('ppc.modelSettings', null)
  if (base) apiBase.value = base
  if (model) modelName.value = model
  if (key) {
    apiKey.value = key
    api.defaults.headers.common['Authorization'] = `Bearer ${key}`
  }
  if (ms && typeof ms === 'object') {
    if (ms.temperature !== undefined) temperature.value = Number(ms.temperature)
    if (ms.topP !== undefined) topP.value = Number(ms.topP)
    if (ms.frequencyPenalty !== undefined) frequencyPenalty.value = Number(ms.frequencyPenalty)
    if (ms.presencePenalty !== undefined) presencePenalty.value = Number(ms.presencePenalty)
    if (ms.stream !== undefined) stream.value = !!ms.stream
    if (ms.memoryRounds !== undefined) memoryRounds.value = Number(ms.memoryRounds)
  }
  const ew = lsGet('ppc.evalWindow', null)
  if (ew !== null && ew !== undefined && String(ew).trim() !== '') {
    const num = Number(ew)
    if (Number.isFinite(num) && num >= 2 && num <= 1000) evalWindow.value = num
  }
  const savedPersona = String(lsGet('ppc.personaProfile', '') || '')
  if (savedPersona.trim()) personaProfile.value = savedPersona
  const saved = lsGet('ppc.messages', [])
  if (Array.isArray(saved)) {
    const arr = saved.filter(m => m && typeof m === 'object' && typeof m.role === 'string')
    if (arr.length) messages.value = arr.map(m => ({ role: String(m.role), content: String(m.content || '') }))
  }
})

function persistMessages() {
  try {
    const arr = messages.value.map(m => ({ role: m.role, content: m.content }))
    lsSet('ppc.messages', arr)
  } catch (_) {}
}

function formatPersonaSystem(s) {
  const t = String(s || '').trim()
  if (!t) return ''
  const cleaned = t.replace(/^\s*<\/role_setting>\s*/i, '').replace(/^\s*<\/pre_setting>\s*/i, '')
  if (/<\s*personality\s*>/i.test(cleaned)) return cleaned
  return `<personality>\n${cleaned}\n</personality>`
}

function formatNowSystem() {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  const s = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  return `<time>当前时间：${s}</time>`
}

</script>

<style>
.json-preview { max-height: 60vh; overflow: auto; display: grid; gap: 8px; padding: 4px }
.json-card { border-radius: 12px; padding: 8px; background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.08)); backdrop-filter: blur(8px); box-shadow: 0 8px 20px rgba(0,0,0,0.15) }
.json-pre { margin: 0; white-space: pre-wrap; word-break: break-word; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 13px; line-height: 1.6; max-width: 100% }
</style>

<style>
:root { color-scheme: dark light }
* { box-sizing: border-box }
body { margin: 0 }
.app { min-height: 100vh; color: #e6e8eb; position: relative; overflow: hidden; background: linear-gradient(135deg, #3b82f6 0%, #a78bfa 50%, #f472b6 100%); background-size: 200% 200%; animation: appGradientShift 16s ease-in-out infinite alternate; padding-left: 28px; transition: padding-left .28s ease }
.app::before { content: ""; position: fixed; inset: -10% -10% -10% -10%; z-index: 0; pointer-events: none; background:
  radial-gradient(500px 500px at 12% 20%, rgba(59,130,246,0.20), transparent 60%),
  radial-gradient(420px 420px at 78% 22%, rgba(244,114,182,0.18), transparent 62%),
  radial-gradient(520px 520px at 40% 84%, rgba(167,139,250,0.16), transparent 60%),
  radial-gradient(360px 360px at 86% 78%, rgba(59,130,246,0.12), transparent 66%);
  filter: blur(12px);
  transform: translate3d(0,0,0);
  animation: glowFloat 18s ease-in-out infinite alternate;
}
.app::after { content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none; background:
  radial-gradient(2px 2px at 20% 30%, rgba(255,255,255,0.25), transparent 50%),
  radial-gradient(2px 2px at 70% 60%, rgba(255,255,255,0.20), transparent 50%),
  radial-gradient(2px 2px at 35% 80%, rgba(255,255,255,0.18), transparent 50%),
  radial-gradient(2px 2px at 85% 40%, rgba(255,255,255,0.22), transparent 50%);
  background-repeat: no-repeat;
  animation: sparkDrift 22s linear infinite;
  opacity: 0.35;
}
.header, .main, .sidebar, .panel { position: relative; z-index: 1 }
.panel:hover { transform: translateY(-2px); box-shadow: 0 16px 40px rgba(59,130,246,0.25) }
.panel-left, .panel-right { min-height: calc(100vh - 180px); overflow: hidden }
.panel-right { min-height: auto }
.panel-right:deep(.el-card__body) { height: auto }
@keyframes appGradientShift { 0% { background-position: 0% 0% } 50% { background-position: 50% 50% } 100% { background-position: 100% 100% } }
@keyframes glowFloat { 0% { transform: translate3d(-1.2%, -0.8%, 0) scale(1) } 50% { transform: translate3d(0.8%, 1.2%, 0) scale(1.02) } 100% { transform: translate3d(1.4%, -0.6%, 0) scale(1) } }
@keyframes sparkDrift { 0% { background-position: 0px 0px, 0px 0px, 0px 0px, 0px 0px } 50% { background-position: 8px -6px, -10px 12px, 6px 10px, -8px -12px } 100% { background-position: 0px 0px, 0px 0px, 0px 0px, 0px 0px } }
.app:has(.sidebar:hover), .app:has(.sidebar-zone:hover) { padding-left: 100px }
.header { display: flex; align-items: baseline; gap: 12px; padding: 16px 24px; }
.logo { font-size: 22px; font-weight: 700; letter-spacing: 1px; }
.subtitle { opacity: 0.7; font-size: 14px }
.main { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 14px; padding: 12px 24px 20px; align-items: stretch }
.panel { border-radius: 16px; background: linear-gradient(180deg, rgba(59,130,246,0.10), rgba(244,114,182,0.08)); background-color: transparent !important; border: none !important; border-color: transparent !important; --el-card-border-color: transparent !important; box-shadow: none !important; backdrop-filter: blur(10px); transition: transform .2s ease, box-shadow .2s ease }
.panel:deep(.el-card__body) { background: transparent; padding: 12px; height: 100%; display: flex; flex-direction: column }
.panel-left:deep(.el-card__body) { padding-bottom: 0 }
.panel-left:deep(.el-card__body) > .chat { margin-bottom: 0 }
@media (max-width: 768px) {
  .main { grid-template-columns: 1fr; padding: 8px 8px 14px; gap: 10px }
  .panel-left, .panel-right { min-height: auto }
}
.sidebar-zone { position: fixed; left: 0; top: 0; width: 14px; height: 100vh; z-index: 20 }
.persona-list { display: grid; gap: 8px }
.persona-item { white-space: pre-wrap; line-height: 1.6 }
.persona-empty { opacity: 0.8; padding: 6px 2px; }
.sidebar { position: fixed; left: 0; top: 0; height: 100vh; width: 10px; z-index: 21; background: linear-gradient(180deg, rgba(12,18,34,0.65), rgba(10,14,26,0.62)), linear-gradient(180deg, rgba(59,130,246,0.22), rgba(244,114,182,0.18)); backdrop-filter: blur(12px); transition: width .28s ease, box-shadow .28s ease, border .28s ease; border-right: 1px solid rgba(255,255,255,0.14) }
.sidebar::after { content: ""; position: absolute; right: 0; top: 0; width: 3px; height: 100%; background: linear-gradient(180deg, #3b82f6, #f472b6); opacity: 0.85 }
.sidebar:hover, .sidebar-zone:hover + .sidebar { width: 80px; box-shadow: 0 16px 40px rgba(59,130,246,0.28) }
.sb-wrap { opacity: 0; transform: translateX(-8px); transition: opacity .25s ease, transform .25s ease; height: 100%; display: grid; grid-template-rows: auto 1fr auto; padding: 16px }
.sidebar:hover .sb-wrap, .sidebar-zone:hover + .sidebar .sb-wrap { opacity: 1; transform: translateX(0) }
.sb-header { display: flex; align-items: center; justify-content: center; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.12) }
.sb-logo { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; font-weight: 700; color: #0b1226; background: linear-gradient(135deg, #3b82f6, #f472b6); box-shadow: 0 8px 20px rgba(0,0,0,0.22) }
.sb-logo i { font-size: 18px }
.sb-title { font-size: 14px; letter-spacing: 1px; opacity: 0.82 }
.sb-icons { display: grid; grid-auto-rows: min-content; gap: 6px; padding: 6px 0; align-content: start; justify-items: center }
.sb-bottom { display: grid; grid-auto-rows: min-content; padding-top: 8px; justify-items: center }
.sb-icon { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; color: #e8ecf2; margin: 0; cursor: pointer; outline: none;
  background: linear-gradient(180deg, rgba(13,17,23,0.68), rgba(13,17,23,0.56));
  border: 1px solid rgba(255,255,255,0.14);
  box-shadow: 0 6px 16px rgba(0,0,0,0.25), inset 0 0 0 1px rgba(255,255,255,0.06);
  transition: background .16s ease, box-shadow .16s ease, transform .12s ease, border-color .12s ease;
  position: relative;
}
.sb-icon::after { content: ""; position: absolute; inset: -1px; border-radius: 14px; padding: 1px;
  background: linear-gradient(135deg, rgba(59,130,246,0.55), rgba(244,114,182,0.55)); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; opacity: 0; transition: opacity .18s ease; }
.sb-icon:hover::after { opacity: 1 }
.sb-icon:hover { box-shadow: 0 10px 24px rgba(59,130,246,0.22); background: linear-gradient(180deg, rgba(13,17,23,0.74), rgba(13,17,23,0.6)); animation: sbBounce .42s cubic-bezier(.175,.885,.32,1.275) }
.sb-icon:active { transform: translateY(0); box-shadow: 0 6px 18px rgba(0,0,0,0.28) }
.sb-icon .el-icon { transition: transform .14s ease, filter .14s ease; filter: drop-shadow(0 2px 6px rgba(59,130,246,0.35)) }
.sb-icon:hover .el-icon { transform: scale(1.06); filter: drop-shadow(0 3px 8px rgba(244,114,182,0.35)) }
.sb-icon.active { border-color: rgba(255,255,255,0.28); box-shadow: 0 12px 28px rgba(59,130,246,0.26); }
.sb-icon.active::after { opacity: 1 }
.sb-icon:focus-visible { outline: 2px solid rgba(147,197,253,0.7); outline-offset: 2px; }
.cute-tip { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; font-size: 13px; letter-spacing: 0.2px; color: #ffeef7; border-radius: 10px; border: 1px solid transparent; padding: 8px 10px; backdrop-filter: blur(8px);
  background: linear-gradient(180deg, rgba(12,18,34,0.86), rgba(10,14,26,0.86)) padding-box,
              linear-gradient(135deg, rgba(244,114,182,0.85), rgba(251,191,197,0.85)) border-box;
  box-shadow: 0 10px 24px rgba(244,114,182,0.18);
}
.cute-tip .el-tooltip__content { animation: tipIn .18s ease-out both }
.cute-tip .el-popper__arrow::before { background: rgba(12,18,34,0.86); border: 1px solid rgba(244,114,182,0.6) }
@keyframes tipIn { from { opacity: 0; transform: translateX(6px) translateY(4px) } to { opacity: 1; transform: translateX(0) translateY(0) } }
.model-tools { display: flex; gap: 8px; margin-bottom: 8px }
.model-table .el-radio__label { display: none }
.model-settings .el-slider__runway { height: 6px; border-radius: 6px; background: rgba(255,255,255,0.12) }
.model-settings .el-slider__bar { height: 6px; border-radius: 6px; background: linear-gradient(90deg, #3b82f6, #f472b6) }
.model-settings .el-slider__button { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.85); background: #0d1117; box-shadow: 0 4px 12px rgba(0,0,0,0.35); transition: transform .14s ease, box-shadow .14s ease; will-change: transform }
.model-settings .el-slider__button:hover { transform: scale(1.06); box-shadow: 0 6px 16px rgba(0,0,0,0.4) }
.model-settings .el-slider__button-wrapper.hover, .model-settings .el-slider__button-wrapper.dragging { transform: none }
</style>
<style>
/* 危险重置弹窗样式与抖动效果 */
.danger-reset-box {
  animation: dangerShake 0.6s cubic-bezier(.175,.885,.32,1.275) 2 both;
  border-radius: 14px;
  border: 1px solid rgba(248,113,113,0.45) !important;
  box-shadow: 0 18px 42px rgba(244,63,94,0.35), inset 0 0 0 1px rgba(255,255,255,0.08) !important;
  backdrop-filter: blur(10px);
  background: linear-gradient(180deg, rgba(20,12,16,0.92), rgba(16,10,14,0.9)) padding-box,
              linear-gradient(135deg, rgba(244,63,94,0.85), rgba(251,113,133,0.85)) border-box;
}
.danger-reset-box .el-message-box__title {
  color: #fecaca;
  letter-spacing: 0.6px;
}
.danger-reset-box .el-message-box__message {
  color: #ffeef1;
  white-space: pre-wrap;
}
.danger-reset-box .danger-main-text {
  font-weight: 700;
  font-size: 16px;
  line-height: 1.6;
  color: #ffeef1;
}
.danger-reset-box .danger-sub-text {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #fecaca;
}
.danger-reset-box .el-input__wrapper {
  background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.06));
  box-shadow: 0 6px 16px rgba(0,0,0,0.18);
}
.danger-reset-box .el-button--primary {
  background: linear-gradient(135deg, #ef4444, #f43f5e);
  border-color: rgba(255,255,255,0.18);
}
.danger-reset-box .el-button:not(.el-button--primary) {
  background: transparent;
  border-color: rgba(255,255,255,0.18);
  color: #ffeef1;
}
@keyframes dangerShake {
  0%, 100% { transform: translate3d(0,0,0) }
  20% { transform: translate3d(-4px, 0, 0) }
  40% { transform: translate3d(4px, 0, 0) }
  60% { transform: translate3d(-3px, 0, 0) }
  80% { transform: translate3d(3px, 0, 0) }
}
</style>
.sb-icon:hover .el-icon { animation: sbPulse .42s ease-in-out }
@keyframes sbBounce { 0% { transform: translateY(0) scale(1) } 28% { transform: translateY(-2px) scale(1.06) } 52% { transform: translateY(1px) scale(0.98) } 76% { transform: translateY(-1px) scale(1.02) } 100% { transform: translateY(0) scale(1) } }
@keyframes sbPulse { 0% { filter: drop-shadow(0 2px 6px rgba(59,130,246,0.35)) } 50% { filter: drop-shadow(0 3px 8px rgba(244,114,182,0.45)) } 100% { filter: drop-shadow(0 2px 6px rgba(59,130,246,0.35)) } }
watch(evalWindow, (v) => {
  const num = Number(v)
  if (Number.isFinite(num)) lsSet('ppc.evalWindow', num)
})
