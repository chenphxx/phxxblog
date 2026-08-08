import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const THEME_KEY = 'blog_theme'

/** 深色/浅色主题: 默认浅色, 持久化到 localStorage */
export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(localStorage.getItem(THEME_KEY) === 'dark')

  function apply() {
    const html = document.documentElement
    html.classList.toggle('dark', isDark.value)
    html.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
    localStorage.setItem(THEME_KEY, isDark.value ? 'dark' : 'light')
  }

  function toggle() {
    isDark.value = !isDark.value
  }

  watch(isDark, apply, { immediate: true })

  return { isDark, toggle }
})
