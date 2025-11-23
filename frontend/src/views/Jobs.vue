<template>
  <div class="jobs-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>匿名化任務列表</span>
          <div>
            <el-button @click="fetchJobs" :loading="jobsStore.loading">
              <el-icon><Refresh /></el-icon>
              重新整理
            </el-button>
          </div>
        </div>
      </template>

      <!-- Filters -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="狀態">
          <el-select v-model="statusFilter" placeholder="全部" clearable @change="fetchJobs">
            <el-option label="等待中" value="pending" />
            <el-option label="下載中" value="downloading" />
            <el-option label="處理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失敗" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="myJobsOnly" @change="fetchJobs">只顯示我的任務</el-checkbox>
        </el-form-item>
      </el-form>

      <!-- Jobs Table -->
      <el-table :data="jobsStore.jobs" v-loading="jobsStore.loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="patient_name" label="原病人姓名" min-width="120" />
        <el-table-column prop="study_date" label="檢查日期" width="100">
          <template #default="{ row }">
            {{ formatDate(row.study_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="modality" label="類型" width="80" />
        <el-table-column prop="study_description" label="檢查描述" min-width="150" />
        <el-table-column prop="new_patient_id" label="新病人ID" width="150" />
        <el-table-column prop="status" label="狀態" width="100">
          <template #default="{ row }">
            <el-tag :class="['status-tag', row.status]" size="small">
              {{ statusText[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="進度" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress"
              :status="getProgressStatus(row.status)"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="建立時間" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              type="primary"
              size="small"
              @click="handleDownload(row)"
            >
              <el-icon><Download /></el-icon>
              下載
            </el-button>
            <el-button
              v-if="['pending', 'downloading', 'processing'].includes(row.status)"
              type="warning"
              size="small"
              @click="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button
              v-if="row.status === 'failed'"
              type="info"
              size="small"
              @click="showError(row)"
            >
              查看錯誤
            </el-button>
            <el-popconfirm
              title="確定要刪除此任務嗎？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small" link>
                  刪除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="jobsStore.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchJobs"
          @current-change="fetchJobs"
        />
      </div>
    </el-card>

    <!-- Error Dialog -->
    <el-dialog v-model="errorDialogVisible" title="錯誤訊息" width="500px">
      <el-alert type="error" :closable="false">
        {{ currentError }}
      </el-alert>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useJobsStore } from '@/stores/jobs'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import dayjs from 'dayjs'

const jobsStore = useJobsStore()
const authStore = useAuthStore()

const statusFilter = ref('')
const myJobsOnly = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const errorDialogVisible = ref(false)
const currentError = ref('')

let refreshInterval = null

const statusText = {
  pending: '等待中',
  queued: '排隊中',
  downloading: '下載中',
  processing: '處理中',
  completed: '已完成',
  failed: '失敗',
  cancelled: '已取消'
}

onMounted(() => {
  fetchJobs()
  // Auto refresh every 5 seconds
  refreshInterval = setInterval(fetchJobs, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

const fetchJobs = async () => {
  try {
    await jobsStore.fetchJobs({
      status_filter: statusFilter.value || undefined,
      my_jobs_only: myJobsOnly.value,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    })
  } catch (error) {
    // Error handled by interceptor
  }
}

const formatDate = (dateStr) => {
  if (!dateStr || dateStr.length !== 8) return dateStr
  return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
}

const formatDateTime = (dateStr) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}

const handleDownload = async (job) => {
  try {
    const response = await api.get(`/api/jobs/${job.job_uuid}/download`, {
      responseType: 'blob'
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', job.output_filename || 'dicom_anonymized.zip')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('下載開始')
  } catch (error) {
    ElMessage.error('下載失敗')
  }
}

const handleCancel = async (job) => {
  try {
    await jobsStore.cancelJob(job.job_uuid)
    ElMessage.success('任務已取消')
  } catch (error) {
    ElMessage.error('取消任務失敗')
  }
}

const handleDelete = async (job) => {
  try {
    await jobsStore.deleteJob(job.job_uuid)
    ElMessage.success('任務已刪除')
  } catch (error) {
    ElMessage.error('刪除任務失敗')
  }
}

const showError = (job) => {
  currentError.value = job.error_message || '未知錯誤'
  errorDialogVisible.value = true
}
</script>

<style lang="scss" scoped>
.jobs-page {
  .filter-form {
    margin-bottom: 20px;
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
