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
  /** 评论数, 仅后台文章列表返回(用于彻底删除前的提示) */
  comment_count?: number | null
  word_count: number
  reading_minutes: number
  published_at?: string | null
  created_at: string
  updated_at: string
  categories: Category[]
  tags: Tag[]
  author?: AuthorBrief | null
}

export interface PostDetail extends PostItem {
  content_md: string
  content_html?: string | null
  /** 同一发布序列中更早的一篇(没有则为 null) */
  prev_post?: PostItem | null
  /** 同一发布序列中更晚的一篇(没有则为 null) */
  next_post?: PostItem | null
}

/** Markdown 正文标题(文章详情页的目录用) */
export interface MarkdownHeading {
  /** 生成的锚点 id(Vditor 渲染出来的标题本身没有 id) */
  id: string
  /** 标题纯文本 */
  text: string
  /** 标题层级 1-6 */
  level: number
}

/**
 * 后台可见的文章详情(创建/更新接口返回)
 * 公开详情接口不再返回 ip / location - 那是作者本人才可见的信息, 不应随文章公开
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
  site_icon: string
  site_avatar: string
  site_bio: string
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
 * 后台仪表盘聚合数据(GET /dashboard)
 *
 * 注意 trend 字段: 后端返回的是 `{date, pv, uv}`(见 api/v1/dashboard.py),
 * 与 /stats/trend 的 TrendPoint 字段名不同, 所以这里单独定义, 不能复用 TrendPoint
 * 以前 DashboardView 用 `as` 断言绕过类型, 字段改名不会报错, 只会运行时出问题
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

/** 模块配置项的类型(决定后台用什么控件渲染), 与后端 base.py 的 SettingKind 一一对应 */
export type ModuleSettingKind = 'bool' | 'int' | 'text' | 'long_text' | 'json' | 'rows'

/**
 * 模块配置的值
 *
 * bool 是布尔, int 是数字, text/long_text/json 是字符串; rows 是行列表, 后端已经
 * 解析成对象数组下发, 前台不必再 JSON.parse
 */
export type ModuleSettingValue = boolean | number | string | ConfigRow[]

/** 行列表配置的一行: 列名 -> 值 */
export type ConfigRow = Record<string, string>

/** 模块的一项配置(后端 app/modules 里的 ModuleSetting) */
export interface ModuleSettingSpec {
  key: string
  name: string
  description: string
  kind: ModuleSettingKind
  minimum: number | null
  maximum: number | null
  /** 是否随公开接口下发(前台可见) */
  public: boolean
  /** 行列表类型的列名(按顺序渲染); 其它类型为空数组 */
  columns: string[]
  value: ModuleSettingValue
}

/** 单个模块的完整信息(后台"模块管理"用) */
export interface ModuleInfo {
  id: string
  name: string
  description: string
  category: string
  /** 核心模块不能在后台禁用 */
  locked: boolean
  default_enabled: boolean
  /** 是否被显式打开 */
  enabled: boolean
  /** 是否真正可用(启用且依赖链上的模块都启用) */
  available: boolean
  /** 当前被禁用的依赖 */
  disabled_dependencies: string[]
  depends_on: string[]
  permissions: string[]
  api_prefix: string
  has_backend: boolean
  frontend_only: boolean
  settings: ModuleSettingSpec[]
}

/** 模块清单响应(后台) */
export interface ModuleAdminData {
  modules: ModuleInfo[]
  /** 分类键 -> 展示名 */
  categories: Record<string, string>
}

/** 前台公开的模块状态 */
export interface PublicModuleState {
  /** 当前可用的模块 id */
  ids: string[]
  /** 模块 id -> 公开配置 */
  config: Record<string, Record<string, ModuleSettingValue>>
}
