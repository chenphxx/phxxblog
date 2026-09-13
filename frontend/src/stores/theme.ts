import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { DEFAULT_THEME, THEME_IDS, type ThemeId } from '@/styles/themes/registry'

const MODE_KEY = 'blog_theme'
const STYLE_KEY = 'blog_theme_style'

/**
 * 主题切换时加一层颜色过渡, 避免生硬跳变。
 *
 * 用单一 timer 句柄而不是每次 new 一个 setTimeout: 快速连点主题按钮时,
 * 以前会叠加多个未清理的定时器(且可能在组件早已卸载后才摘掉 class)。
 * 新一次切换会取消上一次的清理任务。
 */
let transitionTimer: number | undefined

function withTransition(apply: () => void) {
  const root = document.documentElement
  root.classList.add('theme-transition')
  apply()
  if (transitionTimer !== undefined) window.clearTimeout(transitionTimer)
  transitionTimer = window.setTimeout(() => {
    transitionTimer = undefined
    root.classList.remove('theme-transition')
  }, 400)
}

function readStoredTheme(): ThemeId {
  const saved = localStorage.getItem(STYLE_KEY)
  return THEME_IDS.includes(saved as ThemeId) ? (saved as ThemeId) : DEFAULT_THEME
}

/**
 * 外观设置:
 *   - isDark   深色 / 浅色
 *   - themeId  配色主题(12 套, 见 styles/themes/registry.ts)
 * 两者独立, 共同决定 <html> 上的 .dark 类与 data-theme 属性,
 * CSS 里用 html[data-theme='<id>'].dark 选中对应令牌。
 */
export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(localStorage.getItem(MODE_KEY) === 'dark')
  const themeId = ref<ThemeId>(readStoredTheme())

  function apply() {
    const html = document.documentElement
    html.classList.toggle('dark', isDark.value)
    html.setAttribute('data-theme', themeId.value)
    localStorage.setItem(MODE_KEY, isDark.value ? 'dark' : 'light')
    localStorage.setItem(STYLE_KEY, themeId.value)
  }

  function toggle() {
    withTransition(() => {
      isDark.value = !isDark.value
    })
  }

  function setTheme(id: ThemeId) {
    if (id === themeId.value) return
    withTransition(() => {
      themeId.value = id
    })
  }

  /** 深浅色与主题任一变化都重新写入 DOM */
  watch([isDark, themeId], apply, { immediate: true })

  const currentTheme = computed(() => THEME_IDS.indexOf(themeId.value))

  return { isDark, themeId, currentTheme, toggle, setTheme }
})
