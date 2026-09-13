import axios, { type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  saveTokens,
} from '@/utils/tokenStorage'
import type { TokenPair } from '@/types'

/** 解包后的请求接口: get/post/put/delete 直接返回后端 data 字段 */
interface Http {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  patch<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
}

const rawAxios = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

/** 已重放过一次的请求标记, 防止刷新后仍 401 时无限循环 */
interface RetriableConfig extends AxiosRequestConfig {
  _retried?: boolean
}

/**
 * 独立的 axios 实例, 只用于刷新令牌。
 * 不能复用 rawAxios: 它的响应拦截器会在刷新失败时递归触发登录跳转。
 */
const refreshClient = axios.create({ baseURL: '/api/v1', timeout: 20000 })

rawAxios.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * 需要登录的前台路由前缀。
 * 这些页面在令牌过期时也要跳登录页, 不能只判断 /admin ——
 * 否则用户在 /write、/diary、/changelog 上会看到错误提示却停在空白页。
 */
const PROTECTED_PREFIXES = ['/admin', '/write', '/diary', '/changelog']

/** 当前是否为受保护页面(基于 hash 路由) */
function isProtectedRoute(hash: string): boolean {
  return PROTECTED_PREFIXES.some(
    (prefix) => hash.startsWith(`#${prefix}`) || hash.includes(`#${prefix}/`),
  )
}

/** 清空登录态, 并在受保护页面上跳登录页 */
function handleUnauthorized() {
  clearSession()
  const hash = location.hash || ''
  if (isProtectedRoute(hash) && !hash.includes('/admin/login')) {
    location.hash = '#/admin/login'
  }
}

/** 用 refresh token 换一对新令牌(后端为一次性轮换, 每次都会换发新的 refresh token) */
async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('没有可用的 refresh token')
  }
  const response = await refreshClient.post('/auth/refresh', { refresh_token: refreshToken })
  const tokens = response.data?.data as TokenPair | undefined
  if (!tokens?.access_token) {
    throw new Error('刷新令牌失败')
  }
  saveTokens(tokens.access_token, tokens.refresh_token)
  return tokens.access_token
}

/**
 * 单飞(single-flight): 页面同时发出多个请求时, 它们几乎必然同时 401。
 * refresh token 是一次性的, 并发刷新会让后到的那次拿到已失效的令牌而整页掉线,
 * 因此这里让所有并发 401 共用同一个刷新 Promise。
 */
let refreshing: Promise<string> | null = null

function refreshOnce(): Promise<string> {
  if (!refreshing) {
    refreshing = refreshAccessToken().finally(() => {
      refreshing = null
    })
  }
  return refreshing
}

/** 登录/刷新接口自身的 401 不应触发静默刷新 */
function isAuthEndpoint(url: string): boolean {
  return url.includes('/auth/refresh') || url.includes('/auth/login')
}

rawAxios.interceptors.response.use(
  // 后端统一返回 { code, message, data }, 这里解出 data 供调用方直接使用
  // blob 响应(文件下载)不拆包, 直接返回完整响应
  (response) =>
    response.config.responseType === 'blob'
      ? (response as never)
      : (response.data.data as never),
  (error) => {
    const status = error.response?.status
    const method = (error.config?.method || 'get').toUpperCase()
    const url = error.config?.url || ''
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      '请求失败'

    if (status === 401) {
      const config = error.config as RetriableConfig | undefined
      const canRetry =
        config && !config._retried && !isAuthEndpoint(url) && Boolean(getRefreshToken())
      if (canRetry) {
        config._retried = true
        return (async () => {
          try {
            await refreshOnce()
          } catch (refreshError) {
            // 只有"刷新令牌本身失败"才算真正掉线; 重放失败会走下面正常的错误处理
            console.warn(`[api] 令牌刷新失败, 已退出登录 (${method} ${url})`)
            handleUnauthorized()
            ElMessage.error('登录已过期, 请重新登录')
            throw refreshError
          }
          // 请求拦截器会用刚写入的新令牌重写 Authorization 头
          return rawAxios.request(config)
        })()
      }
    }

    // 统一打一条带上下文的警告: 各页面普遍用 try/finally 或空 catch,
    // 没有这行日志时只会在控制台留下未处理的 rejection, 无法判断是哪个请求失败。
    console.warn(`[api] ${method} ${url} -> ${status ?? 'network'} ${message}`)

    if (status === 401) {
      handleUnauthorized()
    }
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

// 导出同一实例, 但带解包类型
const request: Http = {
  get: (url, config) => rawAxios.get(url, config) as never,
  post: (url, data, config) => rawAxios.post(url, data, config) as never,
  put: (url, data, config) => rawAxios.put(url, data, config) as never,
  patch: (url, data, config) => rawAxios.patch(url, data, config) as never,
  delete: (url, config) => rawAxios.delete(url, config) as never,
}

export default request
// refreshClient 只在测试里用于注入假 adapter(验证静默刷新的单飞与失败分支)
export { rawAxios, refreshClient }
