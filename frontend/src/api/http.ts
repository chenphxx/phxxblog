import axios, { type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

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

rawAxios.interceptors.request.use((config) => {
  const token = localStorage.getItem('blog_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

rawAxios.interceptors.response.use(
  // 后端统一返回 { code, message, data }, 这里解出 data 供调用方直接使用
  (response) => response.data.data as never,
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || error.message || '请求失败'
    if (status === 401) {
      localStorage.removeItem('blog_access_token')
      localStorage.removeItem('blog_refresh_token')
      localStorage.removeItem('blog_user')
      if (location.hash.includes('/admin') && !location.hash.includes('/admin/login')) {
        location.hash = '#/admin/login'
      }
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
export { rawAxios }
