<template>
  <el-config-provider :locale="locale">
    <div class="app-container">
      <template v-if="authStore.isAuthenticated">
        <el-container class="main-container">
          <el-aside width="220px" class="sidebar">
            <div class="logo">
              <el-icon><Monitor /></el-icon>
              <span>DICOM 匿名化平台</span>
            </div>
            <el-menu
              :router="true"
              :default-active="$route.path"
              background-color="#001529"
              text-color="#fff"
              active-text-color="#409EFF"
            >
              <el-menu-item index="/query">
                <el-icon><Search /></el-icon>
                <span>查詢病人</span>
              </el-menu-item>
              <el-menu-item index="/jobs">
                <el-icon><List /></el-icon>
                <span>匿名化任務</span>
              </el-menu-item>
              <el-sub-menu index="/admin" v-if="authStore.isAdmin">
                <template #title>
                  <el-icon><Setting /></el-icon>
                  <span>管理設定</span>
                </template>
                <el-menu-item index="/admin/servers">
                  <el-icon><Connection /></el-icon>
                  <span>DICOM伺服器</span>
                </el-menu-item>
                <el-menu-item index="/admin/users">
                  <el-icon><User /></el-icon>
                  <span>使用者管理</span>
                </el-menu-item>
              </el-sub-menu>
            </el-menu>
          </el-aside>
          <el-container>
            <el-header class="header">
              <div class="header-left">
                <el-breadcrumb separator="/">
                  <el-breadcrumb-item :to="{ path: '/' }">首頁</el-breadcrumb-item>
                  <el-breadcrumb-item v-if="$route.meta.title">{{ $route.meta.title }}</el-breadcrumb-item>
                </el-breadcrumb>
              </div>
              <div class="header-right">
                <el-dropdown>
                  <span class="user-info">
                    <el-icon><UserFilled /></el-icon>
                    {{ authStore.user?.username }}
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="handleLogout">
                        <el-icon><SwitchButton /></el-icon>
                        登出
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </el-header>
            <el-main class="main-content">
              <router-view />
            </el-main>
          </el-container>
        </el-container>
      </template>
      <template v-else>
        <router-view />
      </template>
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import zhTw from 'element-plus/dist/locale/zh-tw.mjs'
import { useAuthStore } from '@/stores/auth'

const locale = zhTw
const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style lang="scss">
.app-container {
  height: 100vh;
}

.main-container {
  height: 100%;
}

.sidebar {
  background-color: #001529;

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 16px;
    font-weight: bold;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    .el-icon {
      margin-right: 8px;
      font-size: 24px;
    }
  }

  .el-menu {
    border-right: none;
  }
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);

  .user-info {
    display: flex;
    align-items: center;
    cursor: pointer;

    .el-icon {
      margin-right: 5px;
    }
  }
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  overflow: auto;
}
</style>
