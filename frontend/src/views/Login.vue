<template>
  <div class="login-container">
    <div class="login-bg-animation">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
    <div class="login-box">
      <div class="login-header">
        <div class="logo-wrapper">
          <el-icon :size="36"><Monitor /></el-icon>
        </div>
        <h1>DICOM 匿名化平台</h1>
        <p class="subtitle">Medical Image Anonymization System</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleLogin"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="使用者名稱"
            prefix-icon="User"
            size="large"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密碼"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-btn"
          >
            <el-icon v-if="!loading"><Right /></el-icon>
            {{ loading ? '登入中...' : '登入系統' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <el-divider>
          <span>測試帳號</span>
        </el-divider>
        <div class="demo-account">
          <el-tag type="info" effect="plain">admin / admin123</el-tag>
        </div>
      </div>
    </div>
    <div class="login-copyright">
      DICOM Anonymization Platform v1.0.0
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '請輸入使用者名稱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登入成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登入失敗')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1c2c 0%, #2d3561 50%, #1a1c2c 100%);
  position: relative;
  overflow: hidden;
}

.login-bg-animation {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;

  .circle {
    position: absolute;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
    animation: float 20s infinite ease-in-out;

    &.circle-1 {
      width: 600px;
      height: 600px;
      top: -200px;
      right: -100px;
      animation-delay: 0s;
    }

    &.circle-2 {
      width: 400px;
      height: 400px;
      bottom: -100px;
      left: -100px;
      animation-delay: -5s;
    }

    &.circle-3 {
      width: 300px;
      height: 300px;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      animation-delay: -10s;
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  25% {
    transform: translateY(-20px) rotate(5deg);
  }
  50% {
    transform: translateY(0) rotate(0deg);
  }
  75% {
    transform: translateY(20px) rotate(-5deg);
  }
}

.login-box {
  width: 420px;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;

  .logo-wrapper {
    width: 72px;
    height: 72px;
    margin: 0 auto 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);

    .el-icon {
      color: #fff;
    }
  }

  h1 {
    font-size: 26px;
    font-weight: 700;
    color: #1a1c2c;
    margin: 0 0 8px 0;
    letter-spacing: 1px;
  }

  .subtitle {
    font-size: 13px;
    color: #909399;
    margin: 0;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }

  :deep(.el-input__wrapper) {
    border-radius: 10px;
    padding: 4px 16px;
    box-shadow: 0 0 0 1px #e4e7ed inset;
    transition: all 0.3s ease;

    &:hover {
      box-shadow: 0 0 0 1px #c0c4cc inset;
    }

    &.is-focus {
      box-shadow: 0 0 0 1px #667eea inset, 0 0 12px rgba(102, 126, 234, 0.2);
    }
  }

  :deep(.el-input__inner) {
    height: 44px;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  letter-spacing: 2px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  }

  &:active {
    transform: translateY(0);
  }

  .el-icon {
    margin-right: 8px;
  }
}

.login-footer {
  margin-top: 24px;

  :deep(.el-divider__text) {
    background: rgba(255, 255, 255, 0.95);
    color: #909399;
    font-size: 12px;
  }

  .demo-account {
    text-align: center;
    margin-top: 12px;

    .el-tag {
      font-family: 'Monaco', 'Consolas', monospace;
      font-size: 13px;
      padding: 8px 16px;
      border-radius: 6px;
    }
  }
}

.login-copyright {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}
</style>
