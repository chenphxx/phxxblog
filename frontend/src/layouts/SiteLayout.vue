<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { settingsApi, statsApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { PublicSettings } from '@/types'

const auth = useAuthStore()
const hasToken = computed(() => !!auth.accessToken)
const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))
const settings = ref<PublicSettings | null>(null)
/** 页脚版权信息(后台可配置, 支持 {year}/{site_name} 占位符; 留空则不显示) */
const DEFAULT_FOOTER_TEXT = '© {year} {site_name} · Vue3 + FastAPI'
const footerText = computed(() => {
  // 配置项缺失(未初始化)时用默认文案, 后台显式留空则不显示
  const raw = (settings.value ? settings.value.footer_text ?? DEFAULT_FOOTER_TEXT : DEFAULT_FOOTER_TEXT).trim()
  if (!raw) return ''
  return raw
    .replaceAll('{year}', String(new Date().getFullYear()))
    .replaceAll('{site_name}', settings.value?.site_name || 'chenphxx')
})
const beianList = computed(() => (settings.value?.beian_info ?? []).filter((b) => b.name))
/** 页脚无任何内容时整体不渲染 */
const hasFooter = computed(() => beianList.value.length > 0 || !!footerText.value)

onMounted(async () => {
  // 页面访问埋点(PV/UV)
  statsApi.track({ url: location.hash || '/' }).catch(() => {})
  try {
    settings.value = await settingsApi.public()
    // 浏览器标签页名称(留空回退到站点名称)
    document.title = settings.value.site_title || settings.value.site_name || "chenphxx's blog"
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
          <router-link to="/search">全部文章</router-link>
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
        <ThemeSwitcher />
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

    <footer v-if="hasFooter" class="site-footer">
      <div v-if="beianList.length" class="footer-icp">
        <a v-for="(item, index) in beianList" :key="index" :href="item.url" target="_blank" rel="noopener noreferrer">
          <span v-if="item.icon" class="beian-icon">{{ item.icon }}</span>
          {{ item.name }}
        </a>
      </div>
      <div v-if="footerText" class="footer-meta">{{ footerText }}</div>
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
  /* 高度自适应内容: 仅由内容 + 内边距决定 */
  padding: 16px;
  border-top: 1px solid var(--border);
  background: var(--card-bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.footer-icp {
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
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
