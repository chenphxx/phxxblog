import http from './http'
import { getAccessToken } from '@/utils/tokenStorage'
import type {
  ArchiveGroup,
  Category,
  CommentItem,
  ContributionPoint,
  DashboardData,
  DiaryEntry,
  HistoryEvent,
  ImportCheckResult,
  ImportResult,
  LinkPreview,
  MediaItem,
  OperationLog,
  Page,
  PostDetail,
  PostDetailAdmin,
  PostItem,
  PublicSettings,
  Role,
  Tag,
  TokenPair,
  TrendPoint,
  User,
  VisitItem,
} from '@/types'

/** 导入文件打包为 FormData */
function importForm(files: File[]) {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  return form
}

/** 认证 */
export const authApi = {
  login: (data: { username: string; password: string }) =>
    http.post<AuthResult>('/auth/login', data),
  register: (data: { username: string; email: string; password: string; nickname?: string }) =>
    http.post<AuthResult>('/auth/register', data),
  me: () => http.get<User>('/auth/me'),
  refresh: (refresh_token: string) => http.post<TokenPair>('/auth/refresh', { refresh_token }),
  logout: (refresh_token: string) => http.post<null>('/auth/logout', { refresh_token }),
  changePassword: (data: { old_password: string; new_password: string }) =>
    http.put('/auth/password', data),
  changeEmail: (data: { email: string }) => http.put('/auth/email', data),
  updateProfile: (data: { username?: string; nickname?: string }) =>
    http.put<User>('/auth/profile', data),
}

/** 文章 */
export const postApi = {
  list: (params?: Record<string, unknown>) => http.get<Page<PostItem>>('/posts', { params }),
  archive: () => http.get<ArchiveGroup[]>('/posts/archive'),
  detail: (id: number) => http.get<PostDetail>(`/posts/${id}`),
  adminList: (params?: Record<string, unknown>) => http.get<Page<PostItem>>('/posts/admin', { params }),
  create: (data: Record<string, unknown>) => http.post<PostDetailAdmin>('/posts', data),
  update: (id: number, data: Record<string, unknown>) => http.put<PostDetailAdmin>(`/posts/${id}`, data),
  trash: (id: number) => http.delete<null>(`/posts/${id}`),
  forceDelete: (id: number) => http.delete<null>(`/posts/${id}/force`),
  restore: (id: number) => http.post<null>(`/posts/${id}/restore`),
  changeStatus: (id: number, status: number) =>
    http.post(`/posts/${id}/publish`, { status }),
  like: (id: number) => http.post<{ liked: boolean; likes_count: number }>(`/posts/${id}/like`),
  exportPosts: async (ids: number[], fmt = 'markdown') => {
    const token = getAccessToken()
    const response = await fetch(`/api/v1/posts/export?ids=${ids.join(',')}&fmt=${fmt}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) {
      throw new Error(`导出失败(${response.status})`)
    }
    return response.blob()
  },
  // 先查重(不写入), 由用户选择"仅导入不重复"或"导入全部"后再真正导入
  checkImportPosts: (files: File[]) =>
    http.post<ImportCheckResult>('/posts/import', importForm(files), { params: { mode: 'check' } }),
  importPosts: (files: File[], onDuplicate: 'skip' | 'all' = 'skip') =>
    http.post<ImportResult>('/posts/import', importForm(files), {
      params: { mode: 'import', on_duplicate: onDuplicate },
    }),
}

/** 分类与标签 */
export const categoryApi = {
  list: () => http.get<Category[]>('/categories'),
  create: (data: Record<string, unknown>) => http.post<Category>('/categories', data),
  update: (id: number, data: Record<string, unknown>) => http.put<Category>(`/categories/${id}`, data),
  remove: (id: number) => http.delete(`/categories/${id}`),
}

export const tagApi = {
  list: () => http.get<Tag[]>('/tags'),
  create: (data: Record<string, unknown>) => http.post<Tag>('/tags', data),
  update: (id: number, data: Record<string, unknown>) => http.put<Tag>(`/tags/${id}`, data),
  remove: (id: number) => http.delete(`/tags/${id}`),
}

/** 评论 */
export const commentApi = {
  list: (postId: number) => http.get<CommentItem[]>(`/posts/${postId}/comments`),
  create: (postId: number, data: Record<string, unknown>) =>
    http.post<CommentItem>(`/posts/${postId}/comments`, data),
  adminList: (params?: Record<string, unknown>) => http.get<Page<CommentItem>>('/comments/admin', { params }),
  update: (id: number, data: Record<string, unknown>) => http.put<CommentItem>(`/comments/${id}`, data),
  updateStatus: (id: number, status: number) => http.patch<null>(`/comments/${id}/status`, null, { params: { status } }),
  remove: (id: number) => http.delete<null>(`/comments/${id}`),
}

/** 媒体 */
export const mediaApi = {
  upload: (file: File, relatedType?: string, relatedId?: number) => {
    const form = new FormData()
    form.append('file', file)
    if (relatedType) form.append('related_type', relatedType)
    if (relatedId) form.append('related_id', String(relatedId))
    return http.post<MediaItem>('/media/upload', form)
  },
  list: (params?: Record<string, unknown>) => http.get<Page<MediaItem>>('/media', { params }),
  remove: (id: number) => http.delete<null>(`/media/${id}`),
}

/** 统计与看板 */
export const statsApi = {
  track: (data?: { url?: string; post_id?: number }) => http.post('/stats/track', data ?? {}),
  overview: () => http.get<Record<string, number>>('/stats/overview'),
  trend: (params?: Record<string, unknown>) => http.get<TrendPoint[]>('/stats/trend', { params }),
  sources: () => http.get<Record<string, { name: string; count: number }[]>>('/stats/sources'),
  dashboard: () => http.get<DashboardData>('/dashboard'),
  visits: (params?: Record<string, unknown>) => http.get<Page<VisitItem>>('/stats/visits', { params }),
  contributions: (params?: Record<string, unknown>) =>
    http.get<ContributionPoint[]>('/stats/contributions', { params }),
}

/** 日记(仅管理员) */
export const diaryApi = {
  list: (params?: Record<string, unknown>) => http.get<Page<DiaryEntry>>('/diaries', { params }),
  create: (data: Record<string, unknown>) => http.post<DiaryEntry>('/diaries', data),
  update: (id: number, data: Record<string, unknown>) => http.put<DiaryEntry>(`/diaries/${id}`, data),
  remove: (id: number) => http.delete<null>(`/diaries/${id}`),
  exportDiaries: async (ids: number[] = [], fmt = 'markdown') => {
    const token = getAccessToken()
    const query = new URLSearchParams({ fmt })
    if (ids.length) query.set('ids', ids.join(','))
    const response = await fetch(`/api/v1/diaries/export?${query.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) {
      throw new Error(`导出失败(${response.status})`)
    }
    return response.blob()
  },
  checkImportDiaries: (files: File[]) =>
    http.post<ImportCheckResult>('/diaries/import', importForm(files), { params: { mode: 'check' } }),
  importDiaries: (files: File[], onDuplicate: 'skip' | 'all' = 'skip') =>
    http.post<ImportResult>('/diaries/import', importForm(files), {
      params: { mode: 'import', on_duplicate: onDuplicate },
    }),
}

/** 杂项 */
export const miscApi = {
  changelog: () => http.get<{ content: string }>('/misc/changelog'),
  updateChangelog: (content: string) => http.put<null>('/misc/changelog', { content }),
  // force=true 用于手动"换一句", 否则服务端每天只取一次
  saying: (force = false) =>
    http.get<{ text: string }>('/misc/saying', { params: force ? { force: true } : undefined }),
  historyToday: () => http.get<{ date: string; events: HistoryEvent[] }>('/misc/history/programmer-today'),
}

/** 操作日志 */
export const logApi = {
  list: (params?: Record<string, unknown>) => http.get<Page<OperationLog>>('/logs', { params }),
}

/** 设置 */
export const settingsApi = {
  public: () => http.get<PublicSettings>('/settings/public'),
  all: () => http.get<Record<string, string>>('/settings'),
  update: (data: Record<string, unknown>) => http.put<null>('/settings', data),
}

/** 搜索 */
export const searchApi = {
  search: (q: string, params?: Record<string, unknown>) =>
    http.get<Page<PostItem>>('/search', { params: { q, ...params } }),
}

/** 链接预览 */
export const linkApi = {
  preview: (url: string) => http.get<LinkPreview>('/links/preview', { params: { url } }),
}

/** 用户管理 */
export const userApi = {
  list: (params?: Record<string, unknown>) => http.get<Page<User>>('/users', { params }),
  create: (data: Record<string, unknown>) => http.post<User>('/users', data),
  update: (id: number, data: Record<string, unknown>) => http.put<User>(`/users/${id}`, data),
  resetPassword: (id: number, password: string) =>
    http.put<null>(`/users/${id}/password`, { password }),
  remove: (id: number) => http.delete<null>(`/users/${id}`),
  roles: () => http.get<Role[]>('/users/roles'),
  createRole: (data: Record<string, unknown>) => http.post<null>('/users/roles', data),
  updateRole: (id: number, data: Record<string, unknown>) => http.put<null>(`/users/roles/${id}`, data),
  removeRole: (id: number) => http.delete<null>(`/users/roles/${id}`),
}

/** 认证响应(登录/注册返回 data.user + data.tokens) */
export interface AuthResult {
  user: User
  tokens: TokenPair
}
