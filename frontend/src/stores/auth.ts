import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { User } from '@/types'
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  readStoredUser,
  saveStoredUser,
  saveTokens,
} from '@/utils/tokenStorage'

/**
 * 登录状态: 令牌与用户信息, 与 localStorage 同步(key 与读写见 utils/tokenStorage)。
 *
 * accessToken / refreshToken 是 computed 而不是 ref: 静默刷新会直接改写 localStorage,
 * 只有从存储读取才能保证 UI 看到的是最新令牌(见 tokenStorage 的 tokenRevision)。
 */
export const useAuthStore = defineStore('auth', () => {
  const accessToken = computed(() => getAccessToken())
  const refreshToken = computed(() => getRefreshToken())
  const user = ref<User | null>(readStoredUser())

  // 会话恢复: 用本地已有的 access token 同步 API 文档鉴权 cookie
  if (accessToken.value) {
    saveTokens(accessToken.value, refreshToken.value)
  }

  function setSession(access: string, refresh: string, userData: User) {
    user.value = userData
    saveTokens(access, refresh)
    saveStoredUser(userData)
  }

  function setUser(userData: User) {
    user.value = userData
    saveStoredUser(userData)
  }

  function logout() {
    user.value = null
    clearSession()
    // 退出登录后回前台首页(不再停在登录页): 后台页面在退出后本来也访问不了
    if (location.hash.includes('/admin')) {
      location.hash = '#/'
    }
  }

  async function fetchMe() {
    const { authApi } = await import('@/api')
    const data = await authApi.me()
    setUser(data as User)
    if (accessToken.value) {
      saveTokens(accessToken.value, refreshToken.value)
    }
    return data as User
  }

  return { accessToken, refreshToken, user, setSession, setUser, logout, fetchMe }
})
