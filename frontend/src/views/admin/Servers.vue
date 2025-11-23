<template>
  <div class="servers-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>DICOM 伺服器管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            新增伺服器
          </el-button>
        </div>
      </template>

      <el-table :data="serversStore.servers" v-loading="serversStore.loading">
        <el-table-column prop="name" label="名稱" min-width="120" />
        <el-table-column prop="host" label="主機" min-width="150">
          <template #default="{ row }">
            {{ row.host }}:{{ row.port }}
          </template>
        </el-table-column>
        <el-table-column prop="ae_title" label="AE Title" width="120" />
        <el-table-column prop="local_ae_title" label="本地 AE" width="120" />
        <el-table-column prop="is_active" label="啟用" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_default" label="預設" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="warning" size="small">預設</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="supports_get" label="支援 C-GET" width="100">
          <template #default="{ row }">
            {{ row.supports_get ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column prop="last_verified_at" label="最後測試" width="160">
          <template #default="{ row }">
            {{ row.last_verified_at ? formatDateTime(row.last_verified_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="testConnection(row)" :loading="testingId === row.id">
              測試連線
            </el-button>
            <el-button type="primary" size="small" @click="showEditDialog(row)">
              編輯
            </el-button>
            <el-popconfirm
              title="確定要刪除此伺服器嗎？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small">刪除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Server Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '編輯伺服器' : '新增伺服器'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="名稱" prop="name">
          <el-input v-model="form.name" placeholder="伺服器名稱" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="描述（選填）" />
        </el-form-item>
        <el-divider content-position="left">連線設定</el-divider>
        <el-form-item label="主機位址" prop="host">
          <el-input v-model="form.host" placeholder="IP 或 域名" />
        </el-form-item>
        <el-form-item label="Port" prop="port">
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="AE Title" prop="ae_title">
          <el-input v-model="form.ae_title" placeholder="遠端 AE Title" maxlength="16" />
        </el-form-item>
        <el-form-item label="本地 AE Title" prop="local_ae_title">
          <el-input v-model="form.local_ae_title" placeholder="本地 AE Title" maxlength="16" />
        </el-form-item>
        <el-divider content-position="left">選項</el-divider>
        <el-form-item label="狀態">
          <el-switch v-model="form.is_active" active-text="啟用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="設為預設">
          <el-switch v-model="form.is_default" />
        </el-form-item>
        <el-form-item label="支援 C-GET">
          <el-switch v-model="form.supports_get" />
          <span class="form-tip">若支援 C-GET 則使用 C-GET，否則使用 C-MOVE</span>
        </el-form-item>
        <el-form-item label="C-MOVE 目標 AE" v-if="!form.supports_get">
          <el-input v-model="form.move_destination_ae" placeholder="C-MOVE 目標 AE Title（選填）" maxlength="16" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '更新' : '新增' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useServersStore } from '@/stores/servers'
import dayjs from 'dayjs'

const serversStore = useServersStore()

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const testingId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const defaultForm = {
  name: '',
  description: '',
  host: '',
  port: 104,
  ae_title: '',
  local_ae_title: 'DICOM_ANON',
  is_active: true,
  is_default: false,
  supports_find: true,
  supports_move: true,
  supports_get: false,
  move_destination_ae: ''
}

const form = reactive({ ...defaultForm })

const rules = {
  name: [{ required: true, message: '請輸入名稱', trigger: 'blur' }],
  host: [{ required: true, message: '請輸入主機位址', trigger: 'blur' }],
  port: [{ required: true, message: '請輸入 Port', trigger: 'blur' }],
  ae_title: [{ required: true, message: '請輸入 AE Title', trigger: 'blur' }],
  local_ae_title: [{ required: true, message: '請輸入本地 AE Title', trigger: 'blur' }]
}

onMounted(() => {
  serversStore.fetchServers()
})

const formatDateTime = (dateStr) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const showAddDialog = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, defaultForm)
  dialogVisible.value = true
}

const showEditDialog = (server) => {
  isEdit.value = true
  editingId.value = server.id
  Object.assign(form, {
    name: server.name,
    description: server.description || '',
    host: server.host,
    port: server.port,
    ae_title: server.ae_title,
    local_ae_title: server.local_ae_title,
    is_active: server.is_active,
    is_default: server.is_default,
    supports_find: server.supports_find,
    supports_move: server.supports_move,
    supports_get: server.supports_get,
    move_destination_ae: server.move_destination_ae || ''
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await serversStore.updateServer(editingId.value, form)
      ElMessage.success('伺服器已更新')
    } else {
      await serversStore.createServer(form)
      ElMessage.success('伺服器已新增')
    }
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失敗')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (server) => {
  try {
    await serversStore.deleteServer(server.id)
    ElMessage.success('伺服器已刪除')
  } catch (error) {
    ElMessage.error('刪除失敗')
  }
}

const testConnection = async (server) => {
  testingId.value = server.id
  try {
    const result = await serversStore.testConnection(server.id)
    if (result.success) {
      ElMessage.success('連線測試成功')
      await serversStore.fetchServers()
    } else {
      ElMessage.error(`連線測試失敗: ${result.message}`)
    }
  } catch (error) {
    ElMessage.error('連線測試失敗')
  } finally {
    testingId.value = null
  }
}
</script>

<style lang="scss" scoped>
.servers-page {
  .form-tip {
    margin-left: 10px;
    color: #909399;
    font-size: 12px;
  }
}
</style>
