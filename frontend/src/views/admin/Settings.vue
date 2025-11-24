<template>
  <div class="settings-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>系統設定</span>
          <div>
            <el-button @click="fetchSettings" :loading="loading">
              <el-icon><Refresh /></el-icon>
              重新載入
            </el-button>
            <el-button type="primary" @click="saveAllSettings" :loading="saving" :disabled="!hasChanges">
              <el-icon><Check /></el-icon>
              儲存變更
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" tab-position="left" class="settings-tabs" v-loading="loading">
        <el-tab-pane
          v-for="(category, key) in settings"
          :key="key"
          :label="category.name"
          :name="key"
        >
          <div class="category-content">
            <div class="category-header">
              <h3>
                <el-icon><component :is="category.icon" /></el-icon>
                {{ category.name }}
              </h3>
              <el-button size="small" text type="warning" @click="resetCategory(key)">
                <el-icon><RefreshLeft /></el-icon>
                重設為預設值
              </el-button>
            </div>

            <el-form label-width="200px" class="settings-form">
              <el-form-item
                v-for="setting in category.settings"
                :key="setting.key"
                :label="setting.description"
              >
                <template v-if="setting.type === 'bool'">
                  <el-switch
                    v-model="editedValues[setting.key]"
                    @change="markChanged(setting.key)"
                  />
                </template>
                <template v-else-if="setting.type === 'int'">
                  <el-input-number
                    v-model="editedValues[setting.key]"
                    :min="0"
                    @change="markChanged(setting.key)"
                    style="width: 200px"
                  />
                </template>
                <template v-else-if="setting.is_secret">
                  <el-input
                    v-model="editedValues[setting.key]"
                    type="password"
                    show-password
                    @input="markChanged(setting.key)"
                    style="width: 300px"
                    placeholder="********"
                  />
                </template>
                <template v-else>
                  <el-input
                    v-model="editedValues[setting.key]"
                    @input="markChanged(setting.key)"
                    style="width: 300px"
                  />
                </template>
                <div class="setting-key">{{ setting.key }}</div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 變更預覽 Dialog -->
    <el-dialog v-model="showChangesDialog" title="確認變更" width="500px">
      <p>您即將修改以下設定：</p>
      <el-table :data="changedList" size="small">
        <el-table-column prop="key" label="設定項目" width="200" />
        <el-table-column prop="oldValue" label="原始值" width="120" />
        <el-table-column prop="newValue" label="新值" width="120" />
      </el-table>
      <template #footer>
        <el-button @click="showChangesDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSave" :loading="saving">
          確認儲存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const activeTab = ref('dicom')
const settings = ref({})
const editedValues = reactive({})
const changedKeys = ref(new Set())
const showChangesDialog = ref(false)

onMounted(() => {
  fetchSettings()
})

const hasChanges = computed(() => changedKeys.value.size > 0)

const changedList = computed(() => {
  const list = []
  for (const key of changedKeys.value) {
    const original = findOriginalValue(key)
    list.push({
      key,
      oldValue: String(original),
      newValue: String(editedValues[key])
    })
  }
  return list
})

const findOriginalValue = (key) => {
  for (const category of Object.values(settings.value)) {
    const setting = category.settings?.find(s => s.key === key)
    if (setting) return setting.value
  }
  return null
}

const fetchSettings = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/settings')
    settings.value = response.data.categories

    // Initialize edited values
    for (const category of Object.values(settings.value)) {
      for (const setting of category.settings || []) {
        editedValues[setting.key] = setting.value
      }
    }

    // Clear changes
    changedKeys.value.clear()

    // Set first tab if current is not valid
    const keys = Object.keys(settings.value)
    if (keys.length > 0 && !keys.includes(activeTab.value)) {
      activeTab.value = keys[0]
    }
  } catch (error) {
    ElMessage.error('載入設定失敗')
  } finally {
    loading.value = false
  }
}

const markChanged = (key) => {
  const original = findOriginalValue(key)
  if (original !== editedValues[key]) {
    changedKeys.value.add(key)
  } else {
    changedKeys.value.delete(key)
  }
}

const saveAllSettings = () => {
  if (changedKeys.value.size === 0) {
    ElMessage.info('沒有需要儲存的變更')
    return
  }
  showChangesDialog.value = true
}

const confirmSave = async () => {
  saving.value = true
  try {
    const settingsToUpdate = {}
    for (const key of changedKeys.value) {
      settingsToUpdate[key] = editedValues[key]
    }

    await api.put('/api/settings', { settings: settingsToUpdate })

    ElMessage.success(`已成功更新 ${changedKeys.value.size} 項設定`)
    showChangesDialog.value = false
    await fetchSettings()
  } catch (error) {
    ElMessage.error('儲存設定失敗')
  } finally {
    saving.value = false
  }
}

const resetCategory = async (category) => {
  try {
    await ElMessageBox.confirm(
      `確定要將「${settings.value[category]?.name}」的所有設定重設為預設值嗎？`,
      '確認重設',
      { type: 'warning' }
    )

    loading.value = true
    await api.post('/api/settings/reset', { category })
    ElMessage.success('已重設為預設值')
    await fetchSettings()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重設失敗')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.settings-page {
  .settings-tabs {
    min-height: 500px;

    :deep(.el-tabs__header) {
      margin-right: 30px;
    }

    :deep(.el-tabs__item) {
      height: 50px;
      line-height: 50px;
      padding: 0 30px;
      font-size: 14px;
    }
  }

  .category-content {
    padding: 0 20px;
  }

  .category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;

    h3 {
      display: flex;
      align-items: center;
      margin: 0;
      font-size: 18px;
      color: #303133;

      .el-icon {
        margin-right: 8px;
        color: #409EFF;
      }
    }
  }

  .settings-form {
    .el-form-item {
      margin-bottom: 22px;
      padding: 12px 16px;
      background: #f9fafc;
      border-radius: 8px;
      transition: background 0.3s;

      &:hover {
        background: #f0f7ff;
      }
    }

    .setting-key {
      margin-top: 6px;
      font-size: 12px;
      color: #909399;
      font-family: 'Monaco', 'Consolas', monospace;
    }
  }
}
</style>
