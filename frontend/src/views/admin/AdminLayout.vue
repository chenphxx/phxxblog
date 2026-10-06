<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { HomeFilled, Notebook } from '@element-plus/icons-vue'
import { ADMIN_NAV_ITEMS } from '@/modules/registry'
import { useAuthStore } from '@/stores/auth'
import { useModulesStore } from '@/stores/modules'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'

const auth = useAuthStore()
const modules = useModulesStore()
const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/posts/')) return '/admin/posts'
  return route.path
})

const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))

/**
 * 后台菜单: 由模块注册表生成, 再按模块开关与管理员身份过滤
 *
 * 模块被禁用时对应菜单项直接消失, 布局不需要知道系统里有哪些模块
 */
const menuItems = computed(() =>
  ADMIN_NAV_ITEMS.filter((item) => {
    if (item.adminOnly && !isAdmin.value) return false
    if (item.gated !== false && item.moduleId && !modules.isEnabled(item.moduleId)) return false
    return true
  }),
)

/** 新窗口打开后端 API 文档(仅 admin 可访问) */
function openDocs() {
  window.open('/docs', '_blank', 'noopener,noreferrer')
}

async function logout() {
  await ElMessageBox.confirm('确定退出登录吗?', '提示', { type: 'warning' })
  const { authApi } = await import('@/api')
  if (auth.refreshToken) {
    authApi.logout(auth.refreshToken).catch(() => {})
  }
  auth.logout()
  router.push('/')
}

onMounted(() => {
  // 先拿模块开关, 菜单才能正确过滤(拿不到时按"全部可用"处理)
  modules.load()
  // 已有令牌但本地无用户信息时, 从后端拉取
  if (!auth.user && auth.accessToken) {
    auth.fetchMe().catch(() => {})
  }
  // 浏览器标签页名称(与前台保持一致)
  import('@/api').then(({ settingsApi }) =>
    settingsApi
      .public()
      .then((data) => {
        document.title = data.site_title || data.site_name || 'phxxblog'
      })
      .catch(() => {}),
  )
})
</script>

<template>
  <el-container class="admin-layout">
    <el-aside width="240px" class="admin-aside">
      <div class="admin-brand">博客管理</div>
      <el-menu :default-active="activeMenu" router background-color="transparent">
        <el-menu-item v-for="item in menuItems" :key="item.to" :index="item.to">
          <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <router-link to="/" class="back-home">
          <el-icon><HomeFilled /></el-icon> 返回前台
        </router-link>
        <div class="header-right">
          <el-button v-if="isAdmin" text class="docs-btn" @click="openDocs">
            <el-icon><Notebook /></el-icon>
            <span>API 文档</span>
          </el-button>
          <ThemeSwitcher />
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
  background: var(--bg);
  /* 与前台侧栏一致: 不画分割线, 靠留白与选中态分层 */
  overflow-y: auto;
  overflow-x: hidden;
}
/* 品牌区其余样式(主题色方块, 字重, 间距)在全局 admin.css 里, 便于与前台统一 */
.admin-brand {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  font-weight: 700;
  font-size: 16px;
  color: var(--text);
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border: 1px solid var(--border);
  border-radius: 999px;
  cursor: pointer;
  font-size: 13px;
  color: var(--muted);
  transition:
    border-color var(--dur) var(--ease),
    color var(--dur) var(--ease);
}
.user-chip:hover {
  border-color: var(--primary);
  color: var(--text);
}
.docs-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.admin-main {
  background: var(--bg);
  overflow-y: auto;
}
</style>
