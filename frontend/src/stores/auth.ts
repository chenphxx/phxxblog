import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types'

const ACCESS_KEY = 'blog_access_token'
const REFRESH_KEY = 'blog_refresh_token'
const USER_KEY = 'blog_user'

/** 登录状态: 令牌与用户信息, 与 localStorage 同步 */
export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem(ACCESS_KEY) || '')
  const refreshToken = ref(localStorage.getItem(REFRESH_KEY) || '')
  const user = ref<User | null>(readUser())

  function readUser(): User | null {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
    } catch {
      return null
    }
  }

  function setSession(access: string, refresh: string, userData: User) {
    accessToken.value = access
    refreshToken.value = refresh
    user.value = userData
    localStorage.setItem(ACCESS_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
    localStorage.setItem(USER_KEY, JSON.stringify(userData))
  }

  function setUser(userData: User) {
    user.value = userData
    localStorage.setItem(USER_KEY, JSON.stringify(userData))
  }

  function logout() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
    if (location.hash.includes('/admin')) {
      location.hash = '#/admin/login'
    }
  }

  async function fetchMe() {
    const { authApi } = await import('@/api')
    const data = await authApi.me()
    setUser(data as User)
    return data as User
  }

  return { accessToken, refreshToken, user, setSession, setUser, logout, fetchMe }
})
