<template>
  <el-config-provider :locale="locale">
    <div class="app-container">
      <template v-if="authStore.isAuthenticated">
        <el-container class="main-container">
          <el-aside width="240px" class="sidebar">
            <div class="logo">
              <div class="logo-icon">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="logo-text">
                <span class="title">DICOM 匿名化</span>
                <span class="subtitle">Medical Image Platform</span>
              </div>
            </div>
            <el-menu
              :router="true"
              :default-active="$route.path"
              background-color="#001529"
              text-color="rgba(255, 255, 255, 0.65)"
              active-text-color="#fff"
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
                <el-menu-item index="/admin/settings">
                  <el-icon><Tools /></el-icon>
                  <span>系統設定</span>
                </el-menu-item>
              </el-sub-menu>
            </el-menu>
            <div class="sidebar-footer">
              <span>v1.0.0</span>
            </div>
          </el-aside>
          <el-container>
            <el-header class="header">
              <div class="header-left">
                <el-breadcrumb separator="/">
                  <el-breadcrumb-item :to="{ path: '/' }">
                    <el-icon><HomeFilled /></el-icon>
                  </el-breadcrumb-item>
                  <el-breadcrumb-item v-if="$route.meta.title">
                    {{ $route.meta.title }}
                  </el-breadcrumb-item>
                </el-breadcrumb>
              </div>
              <div class="header-right">
                <el-dropdown trigger="click">
                  <div class="user-info">
                    <el-avatar :size="32" class="user-avatar">
                      {{ authStore.user?.username?.charAt(0).toUpperCase() }}
                    </el-avatar>
                    <span class="user-name">{{ authStore.user?.username }}</span>
                    <el-tag v-if="authStore.isAdmin" type="danger" size="small" class="admin-tag">
                      管理員
                    </el-tag>
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </div>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="handleLogout">
                        <el-icon><SwitchButton /></el-icon>
                        登出系統
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </el-header>
            <el-main class="main-content">
              <transition name="fade" mode="out-in">
                <router-view />
              </transition>
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
  overflow: hidden;
}

.main-container {
  height: 100%;
}

.sidebar {
  background: linear-gradient(180deg, #001529 0%, #002140 100%);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);

  .logo {
    height: 64px;
    display: flex;
    align-items: center;
    padding: 0 20px;
    background: rgba(255, 255, 255, 0.05);

    .logo-icon {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 12px;

      .el-icon {
        color: #fff;
        font-size: 22px;
      }
    }

    .logo-text {
      display: flex;
      flex-direction: column;

      .title {
        color: #fff;
        font-size: 16px;
        font-weight: 600;
        line-height: 1.2;
      }

      .subtitle {
        color: rgba(255, 255, 255, 0.45);
        font-size: 11px;
        margin-top: 2px;
      }
    }
  }

  .el-menu {
    border-right: none;
    flex: 1;
    overflow-y: auto;

    .el-menu-item {
      margin: 4px 8px;
      border-radius: 6px;
      transition: all 0.3s ease;

      &:hover {
        background: rgba(255, 255, 255, 0.08) !important;
      }

      &.is-active {
        background: linear-gradient(90deg, #409EFF, #337ecc) !important;
        color: #fff !important;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
      }
    }

    .el-sub-menu {
      .el-sub-menu__title {
        margin: 4px 8px;
        border-radius: 6px;

        &:hover {
          background: rgba(255, 255, 255, 0.08) !important;
        }
      }

      .el-menu-item {
        padding-left: 52px !important;
        min-width: auto;
      }
    }
  }

  .sidebar-footer {
    padding: 16px;
    text-align: center;
    color: rgba(255, 255, 255, 0.3);
    font-size: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
  }
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  z-index: 10;

  .header-left {
    .el-breadcrumb {
      font-size: 14px;
    }
  }

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      cursor: pointer;
      padding: 8px 12px;
      border-radius: 8px;
      transition: background 0.3s ease;

      &:hover {
        background: #f5f7fa;
      }

      .user-avatar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
        font-weight: 600;
      }

      .user-name {
        margin-left: 10px;
        font-weight: 500;
        color: #303133;
      }

      .admin-tag {
        margin-left: 8px;
      }

      .el-icon--right {
        margin-left: 6px;
        color: #909399;
      }
    }
  }
}

.main-content {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
  padding: 24px;
  overflow: auto;
}

// Page transition
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
