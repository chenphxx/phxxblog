<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Clock,
  Collection,
  Document,
  EditPen,
  HomeFilled,
  Menu,
  Notebook,
  Setting,
  User,
} from '@element-plus/icons-vue'
import Kanbanniang from '@/components/Kanbanniang.vue'
import KanbanniangSwitcher from '@/components/KanbanniangSwitcher.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { settingsApi, statsApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useKanbanniangStore } from '@/stores/kanbanniang'
import type { PublicSettings } from '@/types'

/**
 * @brief 前台外壳(桌面侧栏 + 移动端抽屉)
 *
 * 布局只负责: 品牌区, 主导航, 次级导航(写文章/后台/登录), 主题与看板娘开关, 站脚
 * 页面内容全部由 views/ 里的页面自己渲染, 布局层不关心页面内部结构
 *
 * 移动端(<1024px)侧栏收成抽屉, 由 .app-topbar 的按钮打开, 点遮罩或切换路由后自动关闭
 */

const auth = useAuthStore()
const kanbanniang = useKanbanniangStore()
const route = useRoute()
const hasToken = computed(() => !!auth.accessToken)
const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))
const settings = ref<PublicSettings | null>(null)
/** 移动端抽屉是否展开 */
const drawerOpen = ref(false)

/** 页脚版权信息(后台可配置, 支持 {year}/{site_name} 占位符; 留空则不显示) */
const DEFAULT_FOOTER_TEXT = '© {year} {site_name} · Vue3 + FastAPI'
const footerText = computed(() => {
  // 配置项缺失(未初始化)时用默认文案, 后台显式留空则不显示
  const raw = (settings.value ? (settings.value.footer_text ?? DEFAULT_FOOTER_TEXT) : DEFAULT_FOOTER_TEXT).trim()
  if (!raw) return ''
  return raw
    .replaceAll('{year}', String(new Date().getFullYear()))
    .replaceAll('{site_name}', settings.value?.site_name || 'phxxblog')
})
const beianList = computed(() => (settings.value?.beian_info ?? []).filter((b) => b.name))
/** 页脚无任何内容时整体不渲染 */
const hasFooter = computed(() => beianList.value.length > 0 || !!footerText.value)

/** 切换路由后收起抽屉(窄屏点完导航就该看到内容) */
watch(
  () => route.fullPath,
  () => {
    drawerOpen.value = false
  },
)

onMounted(async () => {
  // 页面访问埋点(PV/UV)
  statsApi.track({ url: location.hash || '/' }).catch(() => {})
  try {
    settings.value = await settingsApi.public()
    // 后台的看板娘总开关(系统设置 - 前台展示), 关掉后前台不加载也不展示
    kanbanniang.setAllowed(settings.value.show_kanbanniang !== false)
    // 浏览器标签页名称(留空回退到站点名称)
    document.title = settings.value.site_title || settings.value.site_name || 'phxxblog'
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
    // 设置加载失败不影响页面, 看板娘按默认(展示)处理
    kanbanniang.setAllowed(true)
  }
})
</script>

<template>
  <div class="app-shell">
    <!-- 窄屏顶部细条: 打开抽屉 + 站名 -->
    <header class="app-topbar">
      <button class="app-menu-btn" type="button" aria-label="打开导航" @click="drawerOpen = true">
        <el-icon><Menu /></el-icon>
      </button>
      <router-link to="/" class="app-topbar-brand">{{ settings?.site_name || 'phxxblog' }}</router-link>
    </header>

    <aside class="app-sidebar" :class="{ 'is-open': drawerOpen }">
      <router-link to="/" class="app-brand">
        <span class="app-brand-mark" aria-hidden="true" />
        <span class="app-brand-name">{{ settings?.site_name || 'phxxblog' }}</span>
      </router-link>
      <p v-if="settings?.site_bio" class="app-brand-bio">{{ settings.site_bio }}</p>

      <nav class="app-nav" aria-label="主导航">
        <!-- 首页是父路由的默认子路由, 记录路径与父路由相同, Vue Router 会把它当作任意子路由的
             active 记录, 因此这里关掉默认的前缀匹配, 只在精确命中首页时套用激活样式 -->
        <router-link to="/" active-class="" exact-active-class="router-link-active">
          <el-icon class="nav-icon"><HomeFilled /></el-icon>
          <span>首页</span>
        </router-link>
        <router-link to="/search">
          <el-icon class="nav-icon"><Document /></el-icon>
          <span>全部文章</span>
        </router-link>
        <router-link to="/archive">
          <el-icon class="nav-icon"><Collection /></el-icon>
          <span>归档</span>
        </router-link>
      </nav>

      <div class="app-nav-divider" />

      <nav v-if="hasToken" class="app-nav app-nav-secondary" aria-label="创作与后台">
        <router-link to="/write">
          <el-icon class="nav-icon"><EditPen /></el-icon>
          <span>写文章</span>
        </router-link>
        <template v-if="isAdmin">
          <router-link to="/changelog">
            <el-icon class="nav-icon"><Clock /></el-icon>
            <span>更新日志</span>
          </router-link>
          <router-link to="/diary">
            <el-icon class="nav-icon"><Notebook /></el-icon>
            <span>日记</span>
          </router-link>
        </template>
        <router-link to="/admin">
          <el-icon class="nav-icon"><Setting /></el-icon>
          <span>管理后台</span>
        </router-link>
      </nav>
      <nav v-else class="app-nav app-nav-secondary" aria-label="登录">
        <router-link to="/admin/login">
          <el-icon class="nav-icon"><User /></el-icon>
          <span>登录</span>
        </router-link>
      </nav>

      <div class="app-sidebar-foot">
        <KanbanniangSwitcher />
        <ThemeSwitcher />
      </div>
    </aside>

    <button v-if="drawerOpen" class="app-drawer-mask" type="button" aria-label="关闭导航" @click="drawerOpen = false" />

    <div class="app-main">
      <main class="site-main">
        <router-view v-slot="{ Component }">
          <keep-alive include="HomeView,AllPostsView,ArchiveView,SearchView">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>

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

    <!-- 看板娘: 固定浮层, 只在后台之外的前台布局里挂载 -->
    <Kanbanniang />
  </div>
</template>
