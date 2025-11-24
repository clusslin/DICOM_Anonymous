<template>
  <div class="audit-logs-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>稽核記錄</span>
          <el-button type="primary" @click="fetchLogs" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- Filters -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="操作類型">
          <el-select v-model="filters.action" placeholder="全部" clearable style="width: 150px">
            <el-option label="建立任務" value="job_created" />
            <el-option label="下載檔案" value="job_downloaded" />
            <el-option label="刪除任務" value="job_deleted" />
            <el-option label="取消任務" value="job_cancelled" />
            <el-option label="登入成功" value="login_success" />
            <el-option label="登入失敗" value="login_failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="使用者">
          <el-input v-model="filters.username" placeholder="使用者名稱" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="日期範圍">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="開始日期"
            end-placeholder="結束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查詢</el-button>
          <el-button @click="resetFilters">重設</el-button>
        </el-form-item>
      </el-form>

      <!-- Logs Table -->
      <el-table :data="logs" v-loading="loading" style="width: 100%">
        <el-table-column prop="created_at" label="時間" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作" width="120">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)" size="small">
              {{ getActionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="使用者" width="120" />
        <el-table-column prop="client_ip" label="IP 位址" width="140" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="request_reason" label="申請理由" min-width="200">
          <template #default="{ row }">
            <el-tooltip v-if="row.request_reason" :content="row.request_reason" placement="top">
              <span class="reason-text">{{ row.request_reason }}</span>
            </el-tooltip>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="entity_id" label="任務ID" width="150">
          <template #default="{ row }">
            <span v-if="row.entity_id" class="entity-id">{{ row.entity_id.substring(0, 8) }}...</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)

const filters = reactive({
  action: '',
  username: '',
  dateRange: null
})

const actionLabels = {
  'job_created': '建立任務',
  'job_downloaded': '下載檔案',
  'job_deleted': '刪除任務',
  'job_cancelled': '取消任務',
  'login_success': '登入成功',
  'login_failed': '登入失敗',
  'logout': '登出',
  'settings_changed': '設定變更',
  'server_created': '新增伺服器',
  'server_deleted': '刪除伺服器',
  'user_created': '新增使用者',
  'user_deleted': '刪除使用者'
}

const actionTypes = {
  'job_created': 'success',
  'job_downloaded': 'primary',
  'job_deleted': 'danger',
  'job_cancelled': 'warning',
  'login_success': 'success',
  'login_failed': 'danger',
  'logout': 'info',
  'settings_changed': 'warning'
}

onMounted(() => {
  fetchLogs()
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }

    if (filters.action) params.action = filters.action
    if (filters.username) params.username = filters.username
    if (filters.dateRange) {
      params.start_date = filters.dateRange[0] + 'T00:00:00'
      params.end_date = filters.dateRange[1] + 'T23:59:59'
    }

    const response = await api.get('/api/audit', { params })
    logs.value = response.data.logs
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('載入稽核記錄失敗')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchLogs()
}

const resetFilters = () => {
  filters.action = ''
  filters.username = ''
  filters.dateRange = null
  currentPage.value = 1
  fetchLogs()
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchLogs()
}

const handlePageChange = () => {
  fetchLogs()
}

const formatDateTime = (dateStr) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

const getActionLabel = (action) => {
  return actionLabels[action] || action
}

const getActionType = (action) => {
  return actionTypes[action] || 'info'
}
</script>

<style lang="scss" scoped>
.audit-logs-page {
  .filter-form {
    margin-bottom: 20px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;
  }

  .reason-text {
    display: inline-block;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .entity-id {
    font-family: monospace;
    font-size: 12px;
    color: #606266;
  }

  .text-muted {
    color: #c0c4cc;
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
