<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  Avatar,
  ChatDotRound,
  DataAnalysis,
  Document,
  Folder,
  HomeFilled,
  Operation,
  Picture,
  Setting,
  User,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/posts/')) return '/admin/posts'
  return route.path
})

const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))

async function logout() {
  await ElMessageBox.confirm('确定退出登录吗?', '提示', { type: 'warning' })
  const { authApi } = await import('@/api')
  if (auth.refreshToken) {
    authApi.logout(auth.refreshToken).catch(() => {})
  }
  auth.logout()
  router.push('/admin/login')
}

onMounted(() => {
  // 已有令牌但本地无用户信息时, 从后端拉取
  if (!auth.user && auth.accessToken) {
    auth.fetchMe().catch(() => {})
  }
})
</script>

<template>
  <el-container class="admin-layout">
    <el-aside width="220px" class="admin-aside">
      <div class="admin-brand">博客管理</div>
      <el-menu :default-active="activeMenu" router background-color="transparent">
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon><span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/admin/posts">
          <el-icon><Document /></el-icon><span>文章管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/categories">
          <el-icon><Folder /></el-icon><span>分类标签</span>
        </el-menu-item>
        <el-menu-item index="/admin/comments">
          <el-icon><ChatDotRound /></el-icon><span>评论管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/media">
          <el-icon><Picture /></el-icon><span>媒体库</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/admin/users">
          <el-icon><User /></el-icon><span>用户管理</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/admin/settings">
          <el-icon><Setting /></el-icon><span>系统设置</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/admin/logs">
          <el-icon><Operation /></el-icon><span>操作日志</span>
        </el-menu-item>
        <el-menu-item index="/admin/profile">
          <el-icon><Avatar /></el-icon><span>个人资料</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <router-link to="/" class="back-home">
          <el-icon><HomeFilled /></el-icon> 返回前台
        </router-link>
        <div class="header-right">
          <ThemeToggle />
          <el-dropdown @command="(cmd: string) => cmd === 'logout' && logout()">
            <span class="user-chip">
              <el-avatar :size="28">{{ (auth.user?.nickname || '管')[0] }}</el-avatar>
              <span>{{ auth.user?.nickname || auth.user?.username || '未登录' }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" @click="router.push('/admin/profile')">个人资料</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-layout {
  height: 100vh;
  overflow: hidden;
}
.admin-aside {
  background: var(--card-bg);
  border-right: 1px solid var(--border);
  overflow-y: auto;
}
.admin-brand {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-weight: 700;
  font-size: 18px;
  border-bottom: 1px solid var(--border);
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.admin-main {
  background: var(--bg);
  overflow-y: auto;
}
</style>
