<template>
  <div class="query-page">
    <!-- Server Selection -->
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>選擇DICOM伺服器</span>
        </div>
      </template>
      <el-select
        v-model="selectedServerId"
        placeholder="選擇伺服器"
        style="width: 300px"
        @change="handleServerChange"
      >
        <el-option
          v-for="server in serversStore.activeServers"
          :key="server.id"
          :label="`${server.name} (${server.host}:${server.port})`"
          :value="server.id"
        />
      </el-select>
    </el-card>

    <!-- Search Form -->
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>查詢條件</span>
          <el-button type="primary" @click="handleSearch" :loading="searching">
            <el-icon><Search /></el-icon>
            查詢
          </el-button>
        </div>
      </template>
      <el-form :model="searchForm" label-width="100px" class="search-form">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="病人姓名">
              <el-input v-model="searchForm.patient_name" placeholder="支援萬用字元 *" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="病人ID">
              <el-input v-model="searchForm.patient_id" placeholder="病人ID" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="檢驗單號">
              <el-input v-model="searchForm.accession_number" placeholder="Accession Number" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="檢查日期">
              <el-date-picker
                v-model="searchForm.study_date_range"
                type="daterange"
                range-separator="至"
                start-placeholder="開始日期"
                end-placeholder="結束日期"
                format="YYYY-MM-DD"
                value-format="YYYYMMDD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="檢查類型">
              <el-select v-model="searchForm.modality" placeholder="全部" clearable style="width: 100%">
                <el-option label="CT" value="CT" />
                <el-option label="MR" value="MR" />
                <el-option label="CR" value="CR" />
                <el-option label="DR" value="DR" />
                <el-option label="DX" value="DX" />
                <el-option label="US" value="US" />
                <el-option label="XA" value="XA" />
                <el-option label="NM" value="NM" />
                <el-option label="PT" value="PT" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="檢查描述">
              <el-input v-model="searchForm.study_description" placeholder="檢查描述" clearable />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- Search Results -->
    <el-card class="page-card" v-if="studies.length > 0">
      <template #header>
        <div class="card-header">
          <span>查詢結果 ({{ studies.length }} 筆)</span>
          <el-button
            type="success"
            :disabled="selectedStudies.length === 0"
            @click="showAnonymizeDialog"
          >
            <el-icon><Download /></el-icon>
            匿名化選取項目 ({{ selectedStudies.length }})
          </el-button>
        </div>
      </template>
      <el-table
        :data="studies"
        @selection-change="handleSelectionChange"
        row-key="StudyInstanceUID"
        v-loading="searching"
      >
        <el-table-column type="selection" width="55" reserve-selection />
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="series-list" style="padding: 10px 20px;">
              <h4 style="margin-bottom: 10px;">Series 列表</h4>
              <el-table :data="row.series" size="small" v-if="row.series?.length">
                <el-table-column prop="SeriesNumber" label="#" width="60" />
                <el-table-column prop="SeriesDescription" label="描述" min-width="150" />
                <el-table-column prop="Modality" label="類型" width="80" />
                <el-table-column prop="NumberOfSeriesRelatedInstances" label="影像數" width="80" />
                <el-table-column prop="BodyPartExamined" label="部位" width="100" />
                <el-table-column label="操作" width="100">
                  <template #default="{ row: series }">
                    <el-button
                      type="primary"
                      size="small"
                      link
                      @click="handleAnonymizeSeries(row, series)"
                    >
                      單獨匿名化
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-else description="無 Series 資訊" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="PatientName" label="病人姓名" min-width="120" />
        <el-table-column prop="PatientID" label="病人ID" width="120" />
        <el-table-column prop="StudyDate" label="檢查日期" width="100">
          <template #default="{ row }">
            {{ formatDate(row.StudyDate) }}
          </template>
        </el-table-column>
        <el-table-column prop="ModalitiesInStudy" label="類型" width="80" />
        <el-table-column prop="StudyDescription" label="檢查描述" min-width="150" />
        <el-table-column prop="AccessionNumber" label="檢驗單號" width="120" />
        <el-table-column prop="NumberOfStudyRelatedSeries" label="Series" width="70" />
        <el-table-column prop="NumberOfStudyRelatedInstances" label="影像" width="70" />
      </el-table>
    </el-card>

    <!-- Anonymization Dialog -->
    <el-dialog
      v-model="anonymizeDialogVisible"
      title="匿名化設定"
      width="600px"
    >
      <el-form :model="anonymizeForm" label-width="140px">
        <el-divider content-position="left">新病人資訊</el-divider>
        <el-form-item label="新病人ID">
          <el-input v-model="anonymizeForm.new_patient_id" placeholder="留空自動產生" />
        </el-form-item>
        <el-form-item label="新病人姓名">
          <el-input v-model="anonymizeForm.new_patient_name" placeholder="預設: ANONYMOUS" />
        </el-form-item>

        <el-divider content-position="left">匿名化選項</el-divider>
        <div class="anon-options">
          <el-checkbox-group v-model="anonymizeForm.options">
            <el-checkbox label="remove_patient_name">移除病人姓名</el-checkbox>
            <el-checkbox label="remove_patient_id">移除病人ID</el-checkbox>
            <el-checkbox label="remove_birth_date">移除出生日期</el-checkbox>
            <el-checkbox label="remove_address">移除地址資訊</el-checkbox>
            <el-checkbox label="remove_phone">移除電話號碼</el-checkbox>
            <el-checkbox label="remove_institution">移除機構資訊</el-checkbox>
            <el-checkbox label="remove_physician">移除醫師資訊</el-checkbox>
            <el-checkbox label="remove_private_tags">移除私有標籤</el-checkbox>
            <el-checkbox label="keep_study_date">保留檢查日期</el-checkbox>
            <el-checkbox label="keep_modality">保留檢查類型</el-checkbox>
            <el-checkbox label="keep_study_description">保留檢查描述</el-checkbox>
            <el-checkbox label="keep_series_description">保留系列描述</el-checkbox>
            <el-checkbox label="hash_uids">雜湊UID</el-checkbox>
            <el-checkbox label="hash_accession">雜湊檢驗單號</el-checkbox>
          </el-checkbox-group>
        </div>
      </el-form>

      <div style="margin-top: 20px; padding: 10px; background: #f5f7fa; border-radius: 4px;">
        <strong>將處理 {{ selectedStudies.length }} 個檢查</strong>
      </div>

      <template #footer>
        <el-button @click="anonymizeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAnonymize" :loading="submitting">
          開始匿名化
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useServersStore } from '@/stores/servers'
import { useJobsStore } from '@/stores/jobs'
import api from '@/utils/api'
import dayjs from 'dayjs'

const serversStore = useServersStore()
const jobsStore = useJobsStore()

const selectedServerId = ref(null)
const searching = ref(false)
const submitting = ref(false)
const studies = ref([])
const selectedStudies = ref([])
const anonymizeDialogVisible = ref(false)

const searchForm = reactive({
  patient_name: '',
  patient_id: '',
  accession_number: '',
  study_date_range: null,
  modality: '',
  study_description: ''
})

const anonymizeForm = reactive({
  new_patient_id: '',
  new_patient_name: '',
  options: [
    'remove_patient_name',
    'remove_patient_id',
    'remove_birth_date',
    'remove_address',
    'remove_phone',
    'remove_institution',
    'remove_physician',
    'remove_private_tags',
    'keep_study_date',
    'keep_modality',
    'keep_study_description',
    'keep_series_description',
    'hash_uids',
    'hash_accession'
  ]
})

onMounted(async () => {
  await serversStore.fetchActiveServers()
  if (serversStore.currentServer) {
    selectedServerId.value = serversStore.currentServer.id
  }
})

const handleServerChange = (serverId) => {
  const server = serversStore.activeServers.find(s => s.id === serverId)
  serversStore.setCurrentServer(server)
}

const handleSearch = async () => {
  if (!selectedServerId.value) {
    ElMessage.warning('請先選擇DICOM伺服器')
    return
  }

  searching.value = true
  try {
    const params = {
      server_id: selectedServerId.value,
      patient_name: searchForm.patient_name || undefined,
      patient_id: searchForm.patient_id || undefined,
      accession_number: searchForm.accession_number || undefined,
      modality: searchForm.modality || undefined,
      study_description: searchForm.study_description || undefined
    }

    if (searchForm.study_date_range) {
      params.study_date_from = searchForm.study_date_range[0]
      params.study_date_to = searchForm.study_date_range[1]
    }

    const response = await api.get('/api/query/study-with-series', { params })

    if (response.data.success) {
      studies.value = response.data.results
      if (studies.value.length === 0) {
        ElMessage.info('查無資料')
      }
    } else {
      ElMessage.error(response.data.message || '查詢失敗')
    }
  } catch (error) {
    ElMessage.error('查詢失敗')
  } finally {
    searching.value = false
  }
}

const handleSelectionChange = (selection) => {
  selectedStudies.value = selection
}

const showAnonymizeDialog = () => {
  anonymizeDialogVisible.value = true
}

const handleAnonymizeSeries = (study, series) => {
  selectedStudies.value = [{
    ...study,
    series_instance_uid: series.SeriesInstanceUID
  }]
  showAnonymizeDialog()
}

const formatDate = (dateStr) => {
  if (!dateStr || dateStr.length !== 8) return dateStr
  return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
}

const handleAnonymize = async () => {
  if (selectedStudies.value.length === 0) {
    ElMessage.warning('請選擇要匿名化的檢查')
    return
  }

  submitting.value = true
  try {
    // Build anonymization options
    const options = {}
    anonymizeForm.options.forEach(opt => {
      options[opt] = true
    })
    // Set options that are not selected to false
    const allOptions = [
      'remove_patient_name', 'remove_patient_id', 'remove_birth_date',
      'remove_address', 'remove_phone', 'remove_institution', 'remove_physician',
      'remove_private_tags', 'keep_study_date', 'keep_modality',
      'keep_study_description', 'keep_series_description', 'hash_uids', 'hash_accession'
    ]
    allOptions.forEach(opt => {
      if (!options[opt]) options[opt] = false
    })

    // Prepare batch data
    const items = selectedStudies.value.map(study => ({
      study_instance_uid: study.StudyInstanceUID,
      series_instance_uid: study.series_instance_uid || null,
      patient_id: study.PatientID,
      patient_name: study.PatientName,
      study_date: study.StudyDate,
      study_description: study.StudyDescription,
      modality: study.ModalitiesInStudy,
      accession_number: study.AccessionNumber
    }))

    const batchData = {
      server_id: selectedServerId.value,
      items: items,
      anonymization_options: options,
      new_patient_id: anonymizeForm.new_patient_id || null,
      new_patient_name: anonymizeForm.new_patient_name || null
    }

    await jobsStore.createBatchJobs(batchData)

    ElMessage.success('匿名化任務已建立，請至任務列表查看進度')
    anonymizeDialogVisible.value = false
    selectedStudies.value = []

  } catch (error) {
    ElMessage.error('建立匿名化任務失敗')
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.query-page {
  .anon-options {
    .el-checkbox-group {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }
  }
}
</style>
