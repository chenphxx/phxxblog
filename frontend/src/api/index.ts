import http from './http'
import type {
  ArchiveGroup,
  Category,
  CommentItem,
  ContributionPoint,
  DiaryEntry,
  HistoryEvent,
  LinkPreview,
  MediaItem,
  OperationLog,
  Page,
  PostDetail,
  PostItem,
  PublicSettings,
  Role,
  Tag,
  TokenPair,
  TrackingResult,
  TrendPoint,
  User,
  VisitItem,
} from '@/types'

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
  create: (data: Record<string, unknown>) => http.post<PostDetail>('/posts', data),
  update: (id: number, data: Record<string, unknown>) => http.put<PostDetail>(`/posts/${id}`, data),
  trash: (id: number) => http.delete<null>(`/posts/${id}`),
  forceDelete: (id: number) => http.delete<null>(`/posts/${id}/force`),
  restore: (id: number) => http.post<null>(`/posts/${id}/restore`),
  changeStatus: (id: number, status: number) =>
    http.post(`/posts/${id}/publish`, { status }),
  like: (id: number) => http.post<{ liked: boolean; likes_count: number }>(`/posts/${id}/like`),
  exportPosts: async (ids: number[], fmt = 'markdown') => {
    const token = localStorage.getItem('blog_access_token') || ''
    const response = await fetch(`/api/v1/posts/export?ids=${ids.join(',')}&fmt=${fmt}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) {
      throw new Error(`导出失败(${response.status})`)
    }
    return response.blob()
  },
  importPosts: (files: File[]) => {
    const form = new FormData()
    files.forEach((file) => form.append('files', file))
    return http.post<{ imported: number; skipped: number; errors: string[] }>('/posts/import', form)
  },
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
  dashboard: () => http.get<Record<string, unknown>>('/dashboard'),
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
}

/** 杂项 */
export const miscApi = {
  changelog: () => http.get<{ content: string }>('/misc/changelog'),
  updateChangelog: (content: string) => http.put<null>('/misc/changelog', { content }),
  saying: () => http.get<{ text: string }>('/misc/saying'),
  historyToday: () => http.get<{ date: string; events: HistoryEvent[] }>('/misc/history/programmer-today'),
  trackingQuery: (params: Record<string, unknown>) =>
    http.get<TrackingResult>('/misc/tracking/query', { params }),
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
