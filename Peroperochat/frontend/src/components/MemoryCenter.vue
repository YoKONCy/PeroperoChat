<template>
  <div class="memory-center">
    <div class="tools">
      <el-select v-model="type" placeholder="类型" clearable style="width: 160px">
        <el-option label="全部" value="" />
        <el-option label="事件" value="event" />
        <el-option label="用户爱好" value="user_hobby" />
        <el-option label="助手爱好" value="assistant_hobby" />
      </el-select>
      <el-input v-model="search" placeholder="搜索文本" clearable style="width: 240px" />
      <el-button type="primary" @click="reload">刷新</el-button>
      <el-button type="warning" @click="maintain">事件合并</el-button>
      <el-button @click="onOpenAssistSettings">副模型API设置</el-button>
    </div>
    <el-table :data="filtered" height="420" stripe border class="mem-table">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="type" label="类型" width="120" />
      <el-table-column prop="text" label="内容" />
      
      <el-table-column prop="created_at" label="时间" width="200" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="insert">
      <el-select v-model="insType" placeholder="类型" style="width: 160px">
        <el-option label="事件" value="event" />
        <el-option label="用户爱好" value="user_hobby" />
        <el-option label="助手爱好" value="assistant_hobby" />
      </el-select>
      <el-input v-model="insText" placeholder="文本" style="flex: 1" />
      
      <el-button type="success" @click="insert">插入</el-button>
    </div>
  </div>
  <el-dialog v-model="showAssistSettings" title="副模型API设置" width="520px">
    <el-form label-width="100px">
      <el-form-item label="模型名称">
        <el-input v-model="assistModelName" placeholder="请先获取模型" />
      </el-form-item>
      <el-form-item label="API地址">
        <el-input v-model="assistApiBase" placeholder="https://api.openai.com" />
      </el-form-item>
      <el-form-item label="API秘钥">
        <el-input v-model="assistApiKey" type="password" placeholder="sk-..." show-password />
      </el-form-item>
      <el-form-item label="获取模型">
        <el-button @click="assistFetchModels">获取模型</el-button>
      </el-form-item>
      <el-form-item v-if="assistModels.length" label="模型选择">
        <div class="model-tools">
          <el-input v-model="assistModelSearch" placeholder="搜索模型ID" clearable style="width:220px" />
          <el-select v-model="assistOwnerFilter" placeholder="所属" clearable style="width:180px">
            <el-option v-for="o in assistOwners" :key="o" :label="o" :value="o" />
          </el-select>
        </div>
        <el-table class="model-table" :data="assistFilteredModels" height="260" highlight-current-row @row-click="row => assistModelName = row.id">
          <el-table-column label="选择" width="90">
            <template #default="{ row }">
              <el-radio v-model="assistModelName" :label="row.id"></el-radio>
            </template>
          </el-table-column>
          <el-table-column prop="id" label="模型ID" />
          <el-table-column prop="owned_by" label="所属" />
        </el-table>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="applyAssistSettings">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, memoryList, memoryInsert, memoryDelete, memoryMaintain } from '../api'

const type = ref('')
const search = ref('')
const items = ref([])
const insType = ref('event')
const insText = ref('')
 
const showAssistSettings = ref(false)
const assistApiBase = ref('')
const assistApiKey = ref('')
const assistModelName = ref('')
const assistModels = ref([])
const assistModelSearch = ref('')
const assistOwnerFilter = ref('')
const assistOwners = computed(() => Array.from(new Set((assistModels.value || []).map(m => m.owned_by).filter(Boolean))))
const assistFilteredModels = computed(() => {
  const kw = assistModelSearch.value.trim().toLowerCase()
  const owner = assistOwnerFilter.value
  return (assistModels.value || []).filter(m => {
    const okKw = kw ? String(m.id).toLowerCase().includes(kw) : true
    const okOwner = owner ? m.owned_by === owner : true
    return okKw && okOwner
  })
})

const filtered = computed(() => {
  const kw = search.value.trim().toLowerCase()
  return (items.value || []).filter(i => {
    const okType = type.value ? i.type === type.value : true
    const okKw = kw ? String(i.text || '').toLowerCase().includes(kw) : true
    return okType && okKw
  })
})

async function reload() {
  try {
    const r = await memoryList(type.value || '', 200, 0)
    items.value = Array.isArray(r?.results) ? r.results : []
  } catch (e) {
    const m = e?.response?.data?.detail || e?.message || '加载失败'
    ElMessage.error(String(m))
  }
}

async function del(id) {
  try {
    await memoryDelete(id)
    await reload()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function insert() {
  try {
    if (!insText.value.trim()) {
      ElMessage.error('请输入文本')
      return
    }
    await memoryInsert({ type: insType.value, text: insText.value })
    insText.value = ''
    await reload()
  } catch (e) {
    // no popup for DB write failure
  }
}

async function maintain() {
  try {
    const aKey = String(localStorage.getItem('ppc.assist.apiKey') || '')
    if (!aKey.trim()) {
      ElMessageBox.alert('未配置副模型API，长记忆功能已关闭', '提示', { type: 'warning' })
      return
    }
    const modelName = localStorage.getItem('ppc.assist.modelName') || ''
    if (!modelName) {
      ElMessageBox.alert('请先选择副模型的模型名称', '提示', { type: 'warning' })
      return
    }
    const r = await memoryMaintain(modelName)
    if (r?.ok) {
      ElMessage.success(`已合并${r.merged || 0}组事件`)
      await reload()
    } else {
      ElMessage.error('维护失败')
    }
  } catch (e) {
    ElMessage.error('维护失败')
  }
}

onMounted(() => { reload() })

function onOpenAssistSettings() {
  showAssistSettings.value = true
}

async function assistFetchModels() {
  try {
    const headers = assistApiKey.value ? { Authorization: `Bearer ${assistApiKey.value}` } : {}
    const r = await api.get('/api/models', { headers, params: { api_base: assistApiBase.value } })
    assistModels.value = Array.isArray(r.data?.data) ? r.data.data : []
  } catch (e) {
    assistModels.value = []
    const msg = e?.response?.data?.detail || e?.message || '获取模型失败'
    ElMessageBox.alert(String(msg), '获取模型失败', { type: 'error' })
  }
}

function applyAssistSettings() {
  try {
    localStorage.setItem('ppc.assist.apiBase', String(assistApiBase.value || ''))
    localStorage.setItem('ppc.assist.apiKey', String(assistApiKey.value || ''))
    localStorage.setItem('ppc.assist.modelName', String(assistModelName.value || ''))
    showAssistSettings.value = false
    ElMessage.success('已保存副模型配置')
  } catch (_) {}
}

onMounted(() => {
  const aBase = String(localStorage.getItem('ppc.assist.apiBase') || '')
  const aKey = String(localStorage.getItem('ppc.assist.apiKey') || '')
  const aModel = String(localStorage.getItem('ppc.assist.modelName') || '')
  if (aBase) assistApiBase.value = aBase
  if (aKey) assistApiKey.value = aKey
  if (aModel) assistModelName.value = aModel
})
</script>

<style>
.memory-center { display: grid; gap: 12px; padding: 8px; border-radius: 16px; background: linear-gradient(180deg, rgba(59,130,246,0.10), rgba(244,114,182,0.08)); backdrop-filter: blur(10px) }
.tools { display: flex; gap: 8px; align-items: center; padding: 6px 8px; border-radius: 12px; background: linear-gradient(180deg, rgba(12,18,34,0.25), rgba(10,14,26,0.22)); border: 1px solid rgba(255,255,255,0.14) }
.tools .el-button { border-radius: 10px }
.mem-table .el-table__header-wrapper th { background: linear-gradient(180deg, rgba(59,130,246,0.12), rgba(244,114,182,0.10)); color: #e6e8eb }
.mem-table .el-table__border-left-patch, .mem-table .el-table__border-right-patch { background: transparent }
.mem-table .el-table__inner-wrapper::before { background: rgba(255,255,255,0.12) }
.mem-table .el-table__body-wrapper td { border-color: rgba(255,255,255,0.12) }
.mem-table .el-table__body-wrapper tr:hover > td { background: rgba(59,130,246,0.10) }
.insert { display: flex; gap: 8px; align-items: center; padding: 6px 8px; border-radius: 12px; background: linear-gradient(180deg, rgba(12,18,34,0.25), rgba(10,14,26,0.22)); border: 1px solid rgba(255,255,255,0.14) }
.insert .el-input__wrapper, .tools .el-input__wrapper { background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.08)) }
</style>
