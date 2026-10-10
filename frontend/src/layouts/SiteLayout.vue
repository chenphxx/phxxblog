<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Menu, Setting, User } from '@element-plus/icons-vue'
import Kanbanniang from '@/components/Kanbanniang.vue'
import KanbanniangSwitcher from '@/components/KanbanniangSwitcher.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { settingsApi, statsApi } from '@/api'
import { FRONT_NAV_ITEMS } from '@/modules/registry'
import { useAuthStore } from '@/stores/auth'
import { useKanbanniangStore } from '@/stores/kanbanniang'
import { useModulesStore } from '@/stores/modules'
import type { PublicSettings } from '@/types'
import { rowsOf, textOf } from '@/utils/moduleConfig'

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
const modules = useModulesStore()
const route = useRoute()
const hasToken = computed(() => !!auth.accessToken)
const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))
const settings = ref<PublicSettings | null>(null)
/** 移动端抽屉是否展开 */
const drawerOpen = ref(false)

/** 页脚配置(footer 模块): 版权文案, 网站链接与备案信息都在这里 */
const footerConfig = computed(() => modules.moduleConfig('footer'))

/** 页脚版权信息(支持 {year}/{site_name} 占位符; 留空则不显示) */
const DEFAULT_FOOTER_TEXT = '© {year} {site_name} · Vue3 + FastAPI'
const footerText = computed(() => {
  // 配置项缺失(模块状态还没加载)时用默认文案, 模块里显式留空则不显示
  const raw = textOf(footerConfig.value.footer_text, DEFAULT_FOOTER_TEXT).trim()
  if (!raw) return ''
  return raw
    .replaceAll('{year}', String(new Date().getFullYear()))
    .replaceAll('{site_name}', settings.value?.site_name || 'phxxblog')
})
const beianList = computed(() => rowsOf(footerConfig.value.beian_info).filter((b) => b.name))
/** 模块被禁用, 或页脚确实没有任何内容时, 页脚整体不渲染 */
const hasFooter = computed(() => modules.isEnabled('footer') && (beianList.value.length > 0 || !!footerText.value))

/**
 * 侧栏导航: 由模块注册表生成, 再按登录状态与模块开关过滤
 *
 * 这样"某个模块被禁用后导航里不再出现它的入口"是自动的, 布局本身不需要知道有哪些模块
 *
 * @param group primary 主导航 / secondary 次级导航
 * @returns 需要渲染的导航项
 */
function visibleNav(group: 'primary' | 'secondary') {
  return FRONT_NAV_ITEMS.filter((item) => {
    if ((item.group ?? 'primary') !== group) return false
    if (item.requiresAuth && !hasToken.value) return false
    if (item.adminOnly && !isAdmin.value) return false
    if (item.gated !== false && item.moduleId && !modules.isEnabled(item.moduleId)) return false
    return true
  })
}

const primaryNav = computed(() => visibleNav('primary'))
const secondaryNav = computed(() => visibleNav('secondary'))

/**
 * 写一个 head 里的 meta 标签
 *
 * @param name meta 的 name
 * @param content 内容; 为空时移除已有标签(模块被禁用时不留残迹)
 */
function setMeta(name: string, content: string) {
  const existing = document.head.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)
  if (!content) {
    existing?.remove()
    return
  }
  const meta = existing ?? document.createElement('meta')
  meta.name = name
  meta.content = content
  if (!existing) document.head.appendChild(meta)
}

/**
 * @brief 按 SEO 模块的开关注入 meta 标签
 *
 * 关键词取自 seo 模块配置, 描述取自站点设置里的 site_desc(它同时是 RSS 的订阅摘要,
 * 属于各模块共享的站点身份信息); 模块被禁用时两处都不输出
 */
function applySeoMeta() {
  const enabled = modules.isEnabled('seo')
  setMeta('keywords', enabled ? textOf(modules.moduleConfig('seo').keywords).trim() : '')
  setMeta('description', enabled ? (settings.value?.site_desc || '').trim() : '')
}

/** 切换路由后收起抽屉(窄屏点完导航就该看到内容) */
watch(
  () => route.fullPath,
  () => {
    drawerOpen.value = false
  },
)

onMounted(async () => {
  // 站点设置与模块开关一起取: 首页各模块的展示条件要用到两者
  await modules.load()
  // 看板娘的总开关现在就是模块开关: 模块被禁用时连运行时与模型都不下载
  kanbanniang.setAllowed(modules.isEnabled('kanbanniang'))
  // 页面访问埋点(PV/UV): 统计模块被禁用时不再产生请求
  if (modules.isEnabled('stats')) {
    statsApi.track({ url: location.hash || '/' }).catch(() => {})
  }
  try {
    settings.value = await settingsApi.public()
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
    applySeoMeta()
  } catch {
    // 设置加载失败不影响页面: 看板娘的总开关已按模块状态决定
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
        <!-- 导航项来自模块注册表: 首页是父路由的默认子路由, 记录路径与父路由相同,
             Vue Router 会把它当作任意子路由的 active 记录, 因此对 exact 的入口关掉
             默认的前缀匹配, 只在精确命中时才套用激活样式 -->
        <router-link
          v-for="item in primaryNav"
          :key="item.to"
          :to="item.to"
          :active-class="item.exact ? '' : 'router-link-active'"
          exact-active-class="router-link-active"
        >
          <el-icon v-if="item.icon" class="nav-icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="app-nav-divider" />

      <nav class="app-nav app-nav-secondary" aria-label="创作与后台">
        <router-link v-for="item in secondaryNav" :key="item.to" :to="item.to">
          <el-icon v-if="item.icon" class="nav-icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
        <!-- 这两条与模块无关, 由布局自己渲染: 未登录只给登录入口, 登录后再给后台入口 -->
        <router-link v-if="hasToken" to="/admin">
          <el-icon class="nav-icon"><Setting /></el-icon>
          <span>管理后台</span>
        </router-link>
        <router-link v-else to="/admin/login">
          <el-icon class="nav-icon"><User /></el-icon>
          <span>登录</span>
        </router-link>
      </nav>

      <div class="app-sidebar-foot">
        <KanbanniangSwitcher v-if="modules.isEnabled('kanbanniang')" />
        <ThemeSwitcher />
      </div>
    </aside>

    <button v-if="drawerOpen" class="app-drawer-mask" type="button" aria-label="关闭导航" @click="drawerOpen = false" />

    <div class="app-main">
      <main class="site-main">
        <router-view v-slot="{ Component }">
          <keep-alive include="HomeView,ArchiveView,SearchView">
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

    <!-- 看板娘: 固定浮层, 只在后台之外的前台布局里挂载; 模块禁用时连运行时都不加载 -->
    <Kanbanniang v-if="modules.isEnabled('kanbanniang')" />
  </div>
</template>
