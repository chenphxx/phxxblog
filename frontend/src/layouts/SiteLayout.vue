<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { settingsApi, statsApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { PublicSettings } from '@/types'

const auth = useAuthStore()
const hasToken = computed(() => !!auth.accessToken)
const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))
const settings = ref<PublicSettings | null>(null)

onMounted(async () => {
  // 页面访问埋点(PV/UV)
  statsApi.track({ url: location.hash || '/' }).catch(() => {})
  try {
    settings.value = await settingsApi.public()
    // 动态站点图标
    const icon = settings.value.site_icon || settings.value.site_avatar
    if (icon) {
      let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
      if (!link) {
        link = document.createElement('link')
        link.rel = 'icon'
        document.head.appendChild(link)
      }
      link.href = icon
    }
  } catch {
    // 设置加载失败不影响页面
  }
})
</script>

<template>
  <div class="site-layout">
    <header class="site-header">
      <div class="site-header-inner">
        <router-link to="/" class="site-brand">{{ settings?.site_name || "chenphxx's blog" }}</router-link>
        <nav class="site-nav">
          <router-link to="/">首页</router-link>
          <router-link to="/archive">归档</router-link>
          <router-link to="/search">搜索</router-link>
          <template v-if="hasToken">
            <router-link to="/write">写文章</router-link>
            <router-link to="/mine">我的文章</router-link>
            <template v-if="isAdmin">
              <router-link to="/changelog">更新日志</router-link>
              <router-link to="/diary">日记</router-link>
            </template>
            <router-link to="/admin">管理后台</router-link>
          </template>
          <router-link v-else to="/admin/login?redirect=/write">登录</router-link>
        </nav>
        <ThemeToggle />
      </div>
    </header>

    <div class="site-body">
      <main class="site-main">
        <router-view v-slot="{ Component }">
          <keep-alive include="HomeView,AllPostsView,ArchiveView,SearchView">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>

    </div>

    <footer class="site-footer">
      <div class="footer-icp">
        <a href="https://beian.mps.gov.cn/#/query/webSearch?code=51150002000777" target="_blank" rel="noopener noreferrer">
          <span class="beian-icon">🛡️</span> 川公安网备51150002000777
        </a>
        <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">蜀ICP备2024103895号-1</a>
      </div>
      <div class="muted">
        © {{ new Date().getFullYear() }} {{ settings?.site_name || "chenphxx's blog" }} · Powered by Vue &amp; FastAPI
      </div>
    </footer>
  </div>
</template>

<style scoped>
.site-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.site-body {
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  align-items: start;
}
.site-main {
  min-width: 0;
}
.site-footer {
  margin-top: auto;
  text-align: center;
  padding: 28px 16px 24px;
}
.footer-icp {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.footer-icp a {
  color: var(--muted);
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.beian-icon {
  font-size: 14px;
}
</style>
