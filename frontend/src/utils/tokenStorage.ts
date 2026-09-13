/**
 * 令牌与会话信息的本地存储读写。
 *
 * 这三个 key 原本散落在 stores/auth.ts、api/http.ts、api/index.ts(导出下载)、
 * router/index.ts(路由守卫)、VditorEditor.vue(上传鉴权)共 6 处, 任何一处改名都会
 * 静默地让其它几处失效(症状是"登录成功但立刻 401")。集中到这里, 只保留一份定义。
 */
import { ref } from 'vue'
import type { User } from '@/types'
import { clearDocTokenCookie, setDocTokenCookie } from '@/utils/docToken'

export const ACCESS_TOKEN_KEY = 'blog_access_token'
export const REFRESH_TOKEN_KEY = 'blog_refresh_token'
export const USER_KEY = 'blog_user'

/**
 * 令牌版本号: 每次写入/清空令牌时自增。
 *
 * 静默刷新(api/http.ts)会绕过 Pinia 直接改写 localStorage, 而登录态指示器、登出按钮
 * 又需要读最新的令牌。让读函数依赖这个版本号, store 里的 computed 就能在刷新后自动失效,
 * 不必再为"谁先写谁后读"引入额外的事件总线。
 */
const tokenRevision = ref(0)

/** 当前 access token(未登录时为空字符串) */
export function getAccessToken(): string {
  void tokenRevision.value
  return localStorage.getItem(ACCESS_TOKEN_KEY) || ''
}

/** 当前 refresh token(未登录时为空字符串) */
export function getRefreshToken(): string {
  void tokenRevision.value
  return localStorage.getItem(REFRESH_TOKEN_KEY) || ''
}

/** 写入令牌对, 并同步 API 文档鉴权 cookie */
export function saveTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  setDocTokenCookie(accessToken)
  tokenRevision.value++
}

/** 读取缓存的用户信息; JSON 损坏时返回 null 而不是抛错 */
export function readStoredUser(): User | null {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

/** 缓存用户信息 */
export function saveStoredUser(user: User) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/** 清空全部登录态(令牌、用户信息与文档 cookie) */
export function clearSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  clearDocTokenCookie()
  tokenRevision.value++
}
