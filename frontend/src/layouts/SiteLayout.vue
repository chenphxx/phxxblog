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
const beianList = computed(() => (settings.value?.beian_info ?? []).filter((b) => b.name))

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
        <router-link to="/" class="site-brand">
          <span class="brand-user">{{ settings?.site_name || 'chenphxx' }}</span>
          <span class="brand-host">@blog</span><span class="brand-path">:~$</span>
        </router-link>
        <nav class="site-nav">
          <router-link to="/">首页</router-link>
          <router-link to="/archive">归档</router-link>
          <router-link to="/search">搜索</router-link>
          <template v-if="hasToken">
            <router-link to="/write">写文章</router-link>
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
      <div v-if="beianList.length" class="footer-icp">
        <a v-for="(item, index) in beianList" :key="index" :href="item.url" target="_blank" rel="noopener noreferrer">
          <span v-if="item.icon" class="beian-icon">{{ item.icon }}</span>
          {{ item.name }}
        </a>
      </div>
      <div class="footer-meta">
        © {{ new Date().getFullYear() }} {{ settings?.site_name || 'chenphxx' }} · Vue3 + FastAPI
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
  padding: 22px 16px 26px;
  border-top: 1px solid var(--border);
  background: var(--card-bg);
}
.footer-icp {
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.footer-icp a {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.footer-meta {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
}
.beian-icon {
  font-size: 12px;
}
</style>
