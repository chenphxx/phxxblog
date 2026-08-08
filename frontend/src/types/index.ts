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
  sort_order: number
  post_count: number
}

export interface Tag {
  id: number
  name: string
  slug: string
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
  site_desc: string
  site_keywords: string
  site_icon: string
  site_avatar: string
  site_bio: string
  site_readme: string
  tech_tags: string[]
  social_links: { name: string; url: string }[]
  website_links: { name: string; url: string }[]
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
