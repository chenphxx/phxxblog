/** 前后端共享的数据类型定义 */

export interface User {
  id: number
  username: string
  email: string
  nickname: string
  avatar?: string | null
  bio?: string | null
  website?: string | null
  social?: Record<string, unknown> | null
  status: number
  role_codes: string[]
  last_login_at?: string | null
  created_at: string
}

export interface Role {
  id: number
  name: string
  code: string
  description?: string | null
  permission_codes: string[]
}

export interface Permission {
  id: number
  name: string
  code: string
  description?: string | null
}

export interface Category {
  id: number
  name: string
  slug: string
  parent_id?: number | null
  description?: string | null
  color?: string | null
  sort_order: number
  post_count: number
}

export interface Tag {
  id: number
  name: string
  slug: string
  color?: string | null
  post_count: number
}

export interface AuthorBrief {
  id: number
  username: string
  nickname: string
  avatar?: string | null
}

export interface PostItem {
  id: number
  title: string
  slug: string
  summary?: string | null
  cover_image?: string | null
  status: number
  views: number
  likes_count: number
  word_count: number
  reading_minutes: number
  published_at?: string | null
  created_at: string
  updated_at: string
  category?: Category | null
  tags: Tag[]
  author?: AuthorBrief | null
}

export interface PostDetail extends PostItem {
  content_md: string
  content_html?: string | null
}

/**
 * 后台可见的文章详情(创建/更新接口返回)。
 * 公开详情接口不再返回 ip / location —— 那是作者本人才可见的信息, 不应随文章公开。
 */
export interface PostDetailAdmin extends PostDetail {
  ip?: string | null
  location?: string | null
}

export interface CommentItem {
  id: number
  post_id: number
  parent_id?: number | null
  user_id?: number | null
  author_name?: string | null
  author_email?: string | null
  content: string
  ip?: string | null
  location?: string | null
  status: number
  can_edit?: boolean
  can_delete?: boolean
  created_at: string
  replies: CommentItem[]
}

export interface MediaItem {
  id: number
  uploader_id?: number | null
  original_name: string
  url: string
  mime_type?: string | null
  size: number
  type: string
  created_at: string
}

export interface ArchiveGroup {
  year: number
  month: number
  count: number
  posts: PostItem[]
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface PublicSettings {
  site_name: string
  site_title: string
  site_desc: string
  site_keywords: string
  site_icon: string
  site_avatar: string
  site_bio: string
  site_readme: string
  /** 首页是否展示 README 模块 */
  show_readme: boolean
  /** 首页是否展示文章发布记录(贡献热力图) */
  show_contributions: boolean
  /** 首页是否展示程序员历史上的今天 */
  show_history: boolean
  /** 首页是否展示 session 终端卡片 */
  show_session: boolean
  /** 页脚版权信息(支持 {year}/{site_name} 占位符, 留空不显示) */
  footer_text: string
  tech_tags: string[]
  social_links: { name: string; url: string }[]
  website_links: { name: string; url: string }[]
  beian_info: { name: string; url: string; icon?: string }[]
}

export interface LinkPreview {
  url: string
  title: string
  description: string
  image?: string | null
}

export interface StatPoint {
  date: string
  pv: number
  uv: number
  post_views: number
}

export interface OperationLog {
  id: number
  user_id?: number | null
  username?: string | null
  module: string
  action: string
  target_type?: string | null
  target_id?: number | null
  detail?: Record<string, unknown> | null
  ip?: string | null
  created_at: string
  location?: string | null
}

export interface VisitItem {
  id: number
  post_id?: number | null
  post_title?: string | null
  ip?: string | null
  location?: string | null
  browser?: string | null
  os?: string | null
  device?: string | null
  referer?: string | null
  url?: string | null
  visit_time?: string | null
}

export interface TrendPoint {
  label: string
  pv: number
  uv: number
  post_views: number
}

/**
 * 后台仪表盘聚合数据(GET /dashboard)。
 *
 * 注意 trend 字段: 后端返回的是 `{date, pv, uv}`(见 api/v1/dashboard.py),
 * 与 /stats/trend 的 TrendPoint 字段名不同, 所以这里单独定义, 不能复用 TrendPoint。
 * 以前 DashboardView 用 `as` 断言绕过类型, 字段改名不会报错, 只会运行时出问题。
 */
export interface DashboardTrendPoint {
  date: string
  pv: number
  uv: number
}

export interface DashboardData {
  overview: Record<string, number>
  trend: DashboardTrendPoint[]
  recent_posts: PostItem[]
  recent_comments: CommentItem[]
}

/** 导入查重结果(mode=check) */
export interface ImportCheckResult {
  total: number
  duplicates_count: number
  duplicates: string[]
}

/** 导入结果(mode=import) */
export interface ImportResult {
  imported: number
  skipped: number
  errors: string[]
  duplicates_count: number
}

export interface ContributionPoint {
  date: string
  count: number
}

export interface DiaryEntry {
  id: number
  user_id: number
  content_md: string
  content_html?: string | null
  entry_date: string
  created_at: string
  updated_at: string
}

/** 程序员历史上的今天-事件 */
export interface HistoryEvent {
  year: number
  month?: number
  day?: number
  title: string
  description: string
  category?: string
  tags?: string[]
  importance?: number
  relevance_score?: number
  source?: string
  url?: string
}
