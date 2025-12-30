<template>
  <div class="settings">
    <div class="settings-header">
      <div class="header-content">
        <h2 class="title">设置中心</h2>
        <p class="subtitle">在这里调整 Pero 的大脑与偏好</p>
      </div>
      <button class="exit-btn" @click="goHome">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <div class="settings-card">
    <el-tabs v-model="tab">
      <el-tab-pane label="API设置" name="api">
        <div class="api-box">
        <el-form label-width="100px">
          <el-form-item label="模型名称"><el-input v-model="modelName" placeholder="请先获取模型" /></el-form-item>
          <el-form-item label="API地址"><el-input v-model="apiBase" placeholder="https://api.openai.com" /></el-form-item>
          <el-form-item label="API秘钥"><el-input v-model="apiKey" type="password" placeholder="sk-..." show-password /></el-form-item>
          <el-form-item>
            <el-button @click="fetchModels">获取模型</el-button>
            <el-input v-model="modelSearch" placeholder="搜索模型ID" clearable style="width:220px;margin-left:8px" />
          </el-form-item>
          <el-table :data="filteredModels" height="260" @row-click="row => modelName = row.id">
            <el-table-column width="50">
              <template #default="{ row }"><el-radio v-model="modelName" :label="row.id"><i></i></el-radio></template>
            </el-table-column>
            <el-table-column prop="id" label="模型ID" />
          </el-table>
        </el-form>
        <div class="api-actions"><el-button type="primary" @click="applySettings">确定</el-button></div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="远程连接" name="remote">
        <div class="api-box">
          <div class="tip-box">
            <el-icon><Connection /></el-icon>
            <p>连接到 PC 集成版或私有云服务器，实现多端记忆共享和更强大的 AI 能力。</p>
          </div>
          <el-form label-width="120px" style="margin-top: 20px">
            <el-form-item label="启用远程模式">
              <el-switch v-model="remoteEnabled" active-text="开启" inactive-text="关闭" />
            </el-form-item>
            <el-form-item label="服务器地址">
              <el-input v-model="remoteUrl" placeholder="例如: http://192.168.1.5:3000" :disabled="!remoteEnabled" />
              <div class="sub-tip">请输入 PeroDesktop 或 PeroServer 的地址</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="applyRemoteSettings" :disabled="!remoteEnabled">保存并连接</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
      <el-tab-pane label="模型设置" name="model">
        <el-form label-width="160px">
          <el-form-item label="Temperature"><el-input-number v-model="temperature" :min="0" :max="2" :step="0.01" /></el-form-item>
          <el-form-item label="Top P"><el-input-number v-model="topP" :min="0" :max="1" :step="0.01" /></el-form-item>
          <el-form-item label="FP"><el-input-number v-model="frequencyPenalty" :min="-2" :max="2" :step="0.01" /></el-form-item>
          <el-form-item label="PP"><el-input-number v-model="presencePenalty" :min="-2" :max="2" :step="0.01" /></el-form-item>
          <el-form-item label="流式传输"><el-switch v-model="stream" /></el-form-item>
          <el-form-item label="记忆轮次">
            <el-input-number v-model="memoryRounds" :min="1" :max="500" :step="1" />
            <div class="tip" style="font-size: 12px; color: #666; margin-top: 4px;">设置发送给 AI 的历史对话轮数（1轮=1提问+1回答）</div>
          </el-form-item>
          <el-form-item><el-button type="primary" @click="applyModelSettings">确定</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="用户设定" name="user">
        <el-form label-width="120px">
          <el-form-item label="我的名字"><el-input v-model="userName" placeholder="填写你的名字" /></el-form-item>
          <el-form-item label="我的人设"><el-input v-model="userPersonaText" type="textarea" :rows="6" placeholder="个人设定" /></el-form-item>
          <el-form-item><el-button type="primary" @click="applyUserSettings">确定</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="系统提示词" name="prompt">
        <el-form label-width="120px">
          <div class="readonly-tip">
            <el-icon style="margin-right: 4px;"><InfoFilled /></el-icon>
            系统提示词是 Pero 的核心逻辑，目前仅供查阅。
          </div>
          <el-form-item label="前置提示词">
            <el-input v-model="systemPrompt" type="textarea" :rows="6" readonly placeholder="核心系统逻辑..." />
          </el-form-item>
          <el-form-item label="人设提示词">
            <el-input v-model="personaText" type="textarea" :rows="6" readonly placeholder="核心性格设定..." />
          </el-form-item>
          <el-form-item label="后置提示词">
            <el-input v-model="postSystemPrompt" type="textarea" :rows="4" readonly placeholder="核心行为规范..." />
          </el-form-item>
          <el-form-item>
            <el-button @click="resetPromptsToDefault">查看默认配置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="记忆管理" name="memory">
        <div class="memory-management">
          <div class="memory-header">
            <el-input v-model="memorySearch" placeholder="搜索记忆内容或标签..." clearable style="width: 300px; margin-bottom: 16px;">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="loadMemories" style="margin-left: 8px;">刷新</el-button>
          </div>
          
          <el-table :data="filteredMemories" style="width: 100%" height="450">
            <el-table-column type="expand">
              <template #default="props">
                <div style="padding: 12px; background: #f8fafc; border-radius: 8px;">
                  <p><strong>完整内容:</strong> {{ props.row.content }}</p>
                  <p><strong>标签:</strong> 
                    <el-tag v-for="tag in props.row.tags" :key="tag" size="small" style="margin-right: 4px;">{{ tag }}</el-tag>
                  </p>
                  <p><strong>记录时间:</strong> {{ props.row.realTime }} ({{ new Date(props.row.timestamp).toLocaleString() }})</p>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="记忆片段" show-overflow-tooltip />
            <el-table-column prop="importance" label="重要性" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.importance > 7 ? 'danger' : row.importance > 4 ? 'warning' : 'info'">
                  {{ row.importance }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button type="danger" size="small" circle @click="deleteMemory(row.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
      <el-tab-pane label="危险区域" name="danger">
        <div class="danger-zone">
          <h3>数据重置</h3>
          <p>此操作将永久删除以下内容：</p>
          <ul>
            <li>所有对话历史记录</li>
            <li>所有存储的记忆条目</li>
            <li>所有 API 设置和用户人设</li>
            <li>所有模型偏好设置</li>
          </ul>
          <p class="warning-text">警告：此操作不可撤销，请谨慎操作！</p>
          <el-button type="danger" @click="handleResetAll">重置所有数据</el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getDefaultPrompts, resetAll } from '../api'
import { db } from '../db'
import { Search, Delete, InfoFilled, Connection } from '@element-plus/icons-vue'

const tab = ref('api')
const modelName = ref('请先获取模型')
const apiBase = ref('https://api.openai.com')
const apiKey = ref('')
const availableModels = ref([])
const modelSearch = ref('')
const ownerFilter = ref('')
const systemPrompt = ref('')
const personaText = ref('')
const userPersonaText = ref('')
const userName = ref('')
const postSystemPrompt = ref('')
const temperature = ref(0.7)
const topP = ref(1)
const frequencyPenalty = ref(0)
const presencePenalty = ref(0)
const stream = ref(false)
const memoryRounds = ref(40)
const memorySearch = ref('')
const allMemories = ref([])

const remoteEnabled = ref(false)
const remoteUrl = ref('')

const router = useRouter()
function goHome() { router.push('/') }

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

const filteredMemories = computed(() => {
  const kw = memorySearch.value.trim().toLowerCase()
  if (!kw) return allMemories.value
  return allMemories.value.filter(m => 
    String(m.content).toLowerCase().includes(kw) || 
    (m.tags || []).some(t => String(t).toLowerCase().includes(kw))
  )
})

async function loadMemories() {
  try {
    allMemories.value = await db.memories.orderBy('timestamp').reverse().toArray()
  } catch (e) {
    console.error('Failed to load memories:', e)
    ElMessage.error('加载记忆失败')
  }
}

async function deleteMemory(id) {
  try {
    await ElMessageBox.confirm('确定要删除这条记忆吗？', '提示', { type: 'warning' })
    await db.memories.delete(id)
    await loadMemories()
    ElMessage.success('已删除')
  } catch (_) {}
}

watch(tab, (newTab) => {
  if (newTab === 'memory') {
    loadMemories()
  }
})

// localStorage 辅助函数
function lsGet(k, def) {
  const v = localStorage.getItem(k)
  return v === null ? def : v
}
function lsSet(k, v) {
  if (typeof v === 'object') v = JSON.stringify(v)
  localStorage.setItem(k, v)
}

function applySettings() {
  lsSet('ppc.modelName', modelName.value)
  lsSet('ppc.apiBase', apiBase.value)
  lsSet('ppc.apiKey', apiKey.value)
  ElMessage.success('API配置已保存')
}

function applyRemoteSettings() {
  localStorage.setItem('ppc.remoteEnabled', String(remoteEnabled.value))
  localStorage.setItem('ppc.remoteUrl', remoteUrl.value.trim())
  ElMessage.success('远程连接设置已保存')
}

function applyModelSettings() {
  lsSet('ppc.modelSettings', { 
    temperature: Number(temperature.value), 
    topP: Number(topP.value), 
    frequencyPenalty: Number(frequencyPenalty.value), 
    presencePenalty: Number(presencePenalty.value), 
    stream: !!stream.value,
    memoryRounds: Number(memoryRounds.value)
  })
  ElMessage.success('已保存')
}

function applySystemPrompt() { 
  lsSet('ppc.systemPrompt', String(systemPrompt.value || ''))
  lsSet('ppc.personaText', String(personaText.value || ''))
  lsSet('ppc.postSystemPrompt', String(postSystemPrompt.value || ''))
  ElMessage.success('已保存')
}
function applyUserSettings() { lsSet('ppc.userPersonaText', String(userPersonaText.value || '')); lsSet('ppc.userName', String(userName.value || '')); ElMessage.success('已保存') }

async function resetPromptsToDefault() {
  try {
    const r = await getDefaultPrompts()
    systemPrompt.value = String(r?.system_prompt_default || '').trim()
    personaText.value = String(r?.persona_prompt_default || '').trim()
    postSystemPrompt.value = String(r?.post_prompt_default || '').trim()
    ElMessage.info('已显示默认配置内容')
  } catch (_) {}
}

async function handleResetAll() {
  try {
    await ElMessageBox.confirm(
      '此操作将永久删除所有对话记录、记忆条目及个人设置。您确定要继续吗？',
      '极其危险的操作',
      {
        confirmButtonText: '确定重置',
        cancelButtonText: '点错了',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await resetAll()
    ElMessage.success('所有数据已清除，正在重新加载...')
    setTimeout(() => {
      window.location.href = '/'
    }, 1500)
  } catch (_) {}
}

async function fetchModels() {
  try {
    const base = (apiBase.value || 'https://api.openai.com').trim().replace(/\/$/, '')
    const headers = apiKey.value ? { Authorization: `Bearer ${apiKey.value}` } : {}
    const url = base.endsWith('/v1') ? `${base}/models` : `${base}/v1/models`
    const r = await axios.get(url, { headers })
    availableModels.value = Array.isArray(r.data?.data) ? r.data.data : []
  } catch (e) {
    availableModels.value = []
    const msg = e?.response?.data?.error?.message || e?.message || '获取模型失败'
    ElMessageBox.alert(String(msg), '获取模型失败', { type: 'error' })
  }
}

onMounted(async () => {
  const base = String(lsGet('ppc.apiBase', apiBase.value) || '').trim()
  const key = String(lsGet('ppc.apiKey', '') || '')

  remoteEnabled.value = !!lsGet('ppc.remoteEnabled', false)
  remoteUrl.value = String(lsGet('ppc.remoteUrl', '') || '')
  const model = String(lsGet('ppc.modelName', modelName.value) || '')
  const ms = lsGet('ppc.modelSettings', null)
  if (base) apiBase.value = base
  if (model) modelName.value = model
  if (key) { apiKey.value = key }
  if (ms && typeof ms === 'object') {
    if (ms.temperature !== undefined) temperature.value = Number(ms.temperature)
    if (ms.topP !== undefined) topP.value = Number(ms.topP)
    if (ms.frequencyPenalty !== undefined) frequencyPenalty.value = Number(ms.frequencyPenalty)
    if (ms.presencePenalty !== undefined) presencePenalty.value = Number(ms.presencePenalty)
    if (ms.stream !== undefined) stream.value = !!ms.stream
    if (ms.memoryRounds !== undefined) memoryRounds.value = Number(ms.memoryRounds)
  }
  const r = await getDefaultPrompts()
  const sp = String(r?.system_prompt_default || '').trim()
  const pp = String(r?.persona_prompt_default || '').trim()
  const tp = String(r?.post_prompt_default || '').trim()
  
  // 从localStorage加载已保存的提示词，如果没有则使用默认值
  const savedSystemPrompt = String(lsGet('ppc.systemPrompt', '') || '').trim()
  const savedPersonaText = String(lsGet('ppc.personaText', '') || '').trim()
  const savedPostSystemPrompt = String(lsGet('ppc.postSystemPrompt', '') || '').trim()
  
  if (savedSystemPrompt) systemPrompt.value = savedSystemPrompt
  else if (sp) systemPrompt.value = sp
  
  if (savedPersonaText) personaText.value = savedPersonaText
  else if (pp) personaText.value = pp
  
  if (savedPostSystemPrompt) postSystemPrompt.value = savedPostSystemPrompt
  else if (tp) postSystemPrompt.value = tp
})
</script>

<style>
.settings { 
  min-height: 100vh; 
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
  color: #111; 
  padding: 20px; 
  --el-color-primary: #3b82f6;
  --el-text-color-primary: #1e293b; 
  --el-text-color-regular: #334155; 
  --el-text-color-secondary: #64748b; 
  --el-text-color-placeholder: #94a3b8;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  max-width: 880px;
  margin-left: auto;
  margin-right: auto;
}

.settings-header .title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.settings-header .subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 4px 0 0 0;
}

.exit-btn {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  border: none;
  background: white;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: all 0.2s ease;
}

.exit-btn:hover {
  background: #f1f5f9;
  color: #1e293b;
  transform: scale(1.05);
}

.settings-card { 
  max-width: 880px; 
  margin: 0 auto; 
  padding: 24px; 
  border-radius: 24px; 
  border: 1px solid rgba(255, 255, 255, 0.5); 
  background: rgba(255, 255, 255, 0.7); 
  backdrop-filter: blur(20px); 
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.06); 
  height: calc(100vh - 120px); 
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.settings-card .el-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.settings-card .el-tabs__content {
  flex: 1;
  overflow-y: auto;
  padding: 10px 4px;
}

/* 隐藏 Tab 底部边框 */
.settings .el-tabs__nav-wrap::after {
  display: none;
}

.settings .el-tabs__item {
  font-size: 15px;
  font-weight: 500;
  padding: 0 20px;
  transition: all 0.3s ease;
}

.settings .el-tabs__item.is-active {
  font-weight: 700;
  color: #3b82f6;
}

.settings .el-tabs__active-bar {
  height: 3px;
  border-radius: 3px;
  background-color: #3b82f6;
}

/* 表单美化 */
.settings .el-form-item {
  margin-bottom: 24px;
}

.settings .el-form-item__label {
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.settings .el-input__wrapper, 
.settings .el-textarea__inner {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: none !important;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.settings .el-input__wrapper:hover,
.settings .el-textarea__inner:hover {
  border-color: rgba(59, 130, 246, 0.3);
}

.settings .el-input__wrapper.is-focus,
.settings .el-textarea__inner:focus {
  background: white;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important;
}

.readonly-tip {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(59, 130, 246, 0.05);
  border-radius: 12px;
  color: #3b82f6;
  font-size: 13px;
  margin-bottom: 20px;
  border: 1px solid rgba(59, 130, 246, 0.1);
}

.settings .el-textarea__inner[readonly] {
  background: rgba(0, 0, 0, 0.02);
  cursor: default;
  color: #64748b;
}

.settings .el-textarea__inner[readonly]:hover {
  border-color: rgba(0, 0, 0, 0.05);
}

.settings .el-button--primary {
  background: #3b82f6;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.settings .el-button--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3);
}

/* 记忆管理表格美化 */
.settings .el-table {
  background: transparent !important;
  --el-table-border-color: rgba(0, 0, 0, 0.05);
}

.settings .el-table tr {
  background: transparent !important;
}

.settings .el-table th.el-table__cell {
  background: rgba(0, 0, 0, 0.02) !important;
  color: #64748b;
  font-weight: 600;
}

.settings .el-table__row:hover td {
  background: rgba(255, 255, 255, 0.5) !important;
}

/* 危险区域美化 */
.danger-zone { 
  padding: 24px; 
  background: rgba(239, 68, 68, 0.03);
  border: 1px solid rgba(239, 68, 68, 0.15); 
  border-radius: 16px; 
  margin-top: 10px; 
}

.danger-zone h3 { color: #ef4444; font-weight: 700; }
.warning-text { color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 8px; }

@media (max-width: 768px) { 
  .settings { padding: 16px } 
  .settings-card { padding: 16px; border-radius: 20px; height: calc(100vh - 100px); }
  .settings-header .title { font-size: 20px; }
}
</style>
