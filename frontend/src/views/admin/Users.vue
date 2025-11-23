<template>
  <div class="users-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>使用者管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            新增使用者
          </el-button>
        </div>
      </template>

      <el-table :data="users" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="使用者名稱" min-width="120" />
        <el-table-column prop="full_name" label="姓名" min-width="120" />
        <el-table-column prop="email" label="Email" min-width="180" />
        <el-table-column prop="is_admin" label="管理員" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">
              {{ row.is_admin ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="啟用" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="建立時間" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditDialog(row)">
              編輯
            </el-button>
            <el-popconfirm
              title="確定要刪除此使用者嗎？"
              @confirm="handleDelete(row)"
              :disabled="row.username === authStore.user?.username"
            >
              <template #reference>
                <el-button
                  type="danger"
                  size="small"
                  :disabled="row.username === authStore.user?.username"
                >
                  刪除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- User Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '編輯使用者' : '新增使用者'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="使用者名稱" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="使用者名稱" />
        </el-form-item>
        <el-form-item label="密碼" :prop="isEdit ? '' : 'password'">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="isEdit ? '留空表示不修改' : '密碼'"
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.full_name" placeholder="姓名（選填）" />
        </el-form-item>
        <el-form-item label="Email">
          <el-input v-model="form.email" type="email" placeholder="Email（選填）" />
        </el-form-item>
        <el-form-item label="管理員">
          <el-switch v-model="form.is_admin" />
        </el-form-item>
        <el-form-item label="啟用">
          <el-switch v-model="form.is_active" />
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
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import dayjs from 'dayjs'

const authStore = useAuthStore()

const users = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const defaultForm = {
  username: '',
  password: '',
  full_name: '',
  email: '',
  is_admin: false,
  is_active: true
}

const form = reactive({ ...defaultForm })

const rules = {
  username: [{ required: true, message: '請輸入使用者名稱', trigger: 'blur' }],
  password: [{ required: true, message: '請輸入密碼', trigger: 'blur' }]
}

onMounted(() => {
  fetchUsers()
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/auth/users')
    users.value = response.data
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

const formatDateTime = (dateStr) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const showAddDialog = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, defaultForm)
  dialogVisible.value = true
}

const showEditDialog = (user) => {
  isEdit.value = true
  editingId.value = user.id
  Object.assign(form, {
    username: user.username,
    password: '',
    full_name: user.full_name || '',
    email: user.email || '',
    is_admin: user.is_admin,
    is_active: user.is_active
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      const updateData = {
        full_name: form.full_name || null,
        email: form.email || null,
        is_admin: form.is_admin,
        is_active: form.is_active
      }
      if (form.password) {
        updateData.password = form.password
      }
      await api.put(`/api/auth/users/${editingId.value}`, updateData)
      ElMessage.success('使用者已更新')
    } else {
      await api.post('/api/auth/users', form)
      ElMessage.success('使用者已新增')
    }
    dialogVisible.value = false
    await fetchUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失敗')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (user) => {
  try {
    await api.delete(`/api/auth/users/${user.id}`)
    ElMessage.success('使用者已刪除')
    await fetchUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '刪除失敗')
  }
}
</script>
