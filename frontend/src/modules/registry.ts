/**
 * 前端模块注册表
 *
 * 一个模块 = 一项可以被整体启用的能力. 前端从这里拿到三样东西:
 *   - frontNav / adminNav        导航入口(前台主导航与次级导航, 后台菜单)
 *   - frontRoutes / adminRoutes  页面路由(自动打上 meta.module 供路由守卫判断)
 *   - id                         与后端 app/modules/definitions/<id>.py 一致
 *
 * "加一个功能"因此只需要两处: 后端加一个模块定义, 这里加一条模块记录, 不必再改
 * router/index.ts, SiteLayout.vue, AdminLayout.vue
 *
 * 模块是否可用由后端决定(见 stores/modules.ts): 被禁用时它的导航项不渲染, 路由
 * 直接访问也会被守卫送回首页
 *
 * 只有真正属于"布局自身"的入口留在这里(首页, 登录, 管理后台, 个人资料),
 * 它们不属于任何模块
 */

import type { Component } from 'vue'
import type { RouteRecordRaw } from 'vue-router'
import {
  Avatar,
  ChatDotRound,
  Collection,
  DataAnalysis,
  Document,
  EditPen,
  Notebook,
  Picture,
  Setting,
  Tickets,
  User,
} from '@element-plus/icons-vue'

/** 导航项(前台侧栏与后台菜单共用一套结构) */
export interface ModuleNavItem {
  to: string
  label: string
  icon?: Component
  /** 前台: primary 进主导航, secondary 进次级导航 */
  group?: 'primary' | 'secondary'
  /** 需要登录才显示 */
  requiresAuth?: boolean
  /** 仅管理员可见 */
  adminOnly?: boolean
  /** 首页这类"父路由同名"的入口需要精确匹配才算激活 */
  exact?: boolean
  /** 是否受模块开关约束(默认 true; 布局自身的入口设为 false) */
  gated?: boolean
}

/** 一条模块记录 */
export interface FrontModule {
  id: string
  name: string
  description: string
  frontNav?: ModuleNavItem[]
  adminNav?: ModuleNavItem[]
  frontRoutes?: RouteRecordRaw[]
  adminRoutes?: RouteRecordRaw[]
}

/**
 * @brief 给路由统一打上模块标记
 *
 * 路由守卫靠 meta.module 判断"这个页面属不属于一个已启用的模块"
 *
 * @param moduleId 模块 id
 * @param routes 模块提供的路由
 * @returns 带上 meta.module 的路由
 */
function withModule(moduleId: string, routes: RouteRecordRaw[]): RouteRecordRaw[] {
  return routes.map((route) => ({ ...route, meta: { ...route.meta, module: moduleId } }))
}

/**
 * 全部前端模块
 *
 * 顺序即后台菜单的展示顺序; 与后端注册表一一对应, 后台"模块管理"页据此展示
 * 每个模块占用的前台入口与页面
 */
export const MODULES: FrontModule[] = [
  {
    id: 'auth',
    name: '认证与会话',
    description: '登录与会话(页面在 /admin/login, 属布局自身)',
  },
  {
    id: 'users',
    name: '用户与角色',
    description: '账号与权限维护',
    adminNav: [{ to: '/admin/users', label: '用户管理', icon: User, adminOnly: true }],
    adminRoutes: [{ path: 'users', name: 'admin-users', component: () => import('@/views/admin/UserManageView.vue') }],
  },
  {
    id: 'settings',
    name: '系统设置',
    description: '站点级配置',
    adminNav: [{ to: '/admin/settings', label: '系统设置', icon: Setting, adminOnly: true }],
    adminRoutes: [
      { path: 'settings', name: 'admin-settings', component: () => import('@/views/admin/SettingsView.vue') },
    ],
  },
  {
    id: 'taxonomy',
    name: '分类与标签',
    description: '分类与标签的维护',
    adminNav: [{ to: '/admin/categories', label: '分类标签', icon: Collection }],
    adminRoutes: [
      { path: 'categories', name: 'admin-categories', component: () => import('@/views/admin/CategoryTagView.vue') },
    ],
  },
  {
    id: 'posts',
    name: '文章',
    description: '文章详情, 列表, 归档与写作',
    frontNav: [
      { to: '/archive', label: '归档', group: 'primary' },
      { to: '/write', label: '写文章', icon: EditPen, group: 'secondary', requiresAuth: true },
    ],
    adminNav: [{ to: '/admin/posts', label: '文章管理', icon: Document }],
    frontRoutes: [
      { path: 'post/:id', name: 'post-detail', component: () => import('@/views/PostDetailView.vue') },
      { path: 'archive', name: 'archive', component: () => import('@/views/ArchiveView.vue') },
      { path: 'posts', name: 'all-posts', component: () => import('@/views/AllPostsView.vue') },
      {
        path: 'write',
        name: 'write',
        component: () => import('@/views/WriteView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'write/:id',
        name: 'write-edit',
        component: () => import('@/views/WriteView.vue'),
        meta: { requiresAuth: true },
      },
    ],
    adminRoutes: [
      { path: 'posts', name: 'admin-posts', component: () => import('@/views/admin/PostManageView.vue') },
      { path: 'posts/new', name: 'admin-post-new', component: () => import('@/views/admin/PostEditView.vue') },
      {
        path: 'posts/:id/edit',
        name: 'admin-post-edit',
        component: () => import('@/views/admin/PostEditView.vue'),
      },
    ],
  },
  {
    id: 'comments',
    name: '评论',
    description: '评论与回复的审核与管理',
    adminNav: [{ to: '/admin/comments', label: '评论管理', icon: ChatDotRound }],
    adminRoutes: [
      { path: 'comments', name: 'admin-comments', component: () => import('@/views/admin/CommentManageView.vue') },
    ],
  },
  {
    id: 'media',
    name: '媒体库',
    description: '上传文件的检索与预览',
    adminNav: [{ to: '/admin/media', label: '媒体库', icon: Picture }],
    adminRoutes: [{ path: 'media', name: 'admin-media', component: () => import('@/views/admin/MediaManageView.vue') }],
  },
  {
    id: 'search',
    name: '站内搜索',
    description: '关键词搜索与分类/标签/时间筛选',
    frontNav: [{ to: '/search', label: '全部文章', group: 'primary' }],
    frontRoutes: [{ path: 'search', name: 'search', component: () => import('@/views/SearchView.vue') }],
  },
  {
    id: 'stats',
    name: '访问统计',
    description: '访问埋点, 概览与趋势(首页发布记录与后台看板的数据来源)',
  },
  {
    id: 'dashboard',
    name: '后台看板',
    description: '后台首页的数据概览',
    adminNav: [{ to: '/admin/dashboard', label: '仪表盘', icon: DataAnalysis }],
    adminRoutes: [
      { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/views/admin/DashboardView.vue') },
    ],
  },
  {
    id: 'logs',
    name: '操作日志',
    description: '后台写操作的审计记录',
    adminNav: [{ to: '/admin/logs', label: '操作日志', icon: Tickets, adminOnly: true }],
    adminRoutes: [{ path: 'logs', name: 'admin-logs', component: () => import('@/views/admin/LogsView.vue') }],
  },
  {
    id: 'diary',
    name: '日记',
    description: '私人日记(仅管理员)',
    frontNav: [
      { to: '/diary', label: '日记', icon: Notebook, group: 'secondary', requiresAuth: true, adminOnly: true },
    ],
    frontRoutes: [
      {
        path: 'diary',
        name: 'diary',
        component: () => import('@/views/DiaryView.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
  {
    id: 'changelog',
    name: '更新日志',
    description: '站点更新日志的展示与编辑',
    frontNav: [
      { to: '/changelog', label: '更新日志', icon: Tickets, group: 'secondary', requiresAuth: true, adminOnly: true },
    ],
    frontRoutes: [
      {
        path: 'changelog',
        name: 'changelog',
        component: () => import('@/views/ChangelogView.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
  {
    id: 'saying',
    name: '一言',
    description: '首页终端卡片里的随机语录',
  },
  {
    id: 'history',
    name: '历史上的今天',
    description: '首页的"程序员历史上的今天"卡片',
  },
  {
    id: 'links',
    name: '外链预览',
    description: '外链卡片的抓取能力(正文与评论里使用)',
  },
  {
    id: 'rss',
    name: 'RSS 与站点地图',
    description: '/rss.xml 与 /sitemap.xml',
  },
  {
    id: 'kanbanniang',
    name: '看板娘',
    description: '前台左下角的 Live2D 看板娘浮层与形象切换',
  },
]

/**
 * 与模块无关的前台导航(布局自身)
 *
 * gated=false: 入口本身不因为模块禁用而消失
 */
export const CORE_FRONT_NAV: ModuleNavItem[] = [{ to: '/', label: '首页', group: 'primary', exact: true, gated: false }]

/** 与模块无关的后台菜单项 */
export const CORE_ADMIN_NAV: ModuleNavItem[] = [{ to: '/admin/profile', label: '个人资料', icon: Avatar, gated: false }]

/** 与模块无关的后台路由 */
export const CORE_ADMIN_ROUTES: RouteRecordRaw[] = [
  { path: 'profile', name: 'admin-profile', component: () => import('@/views/admin/ProfileView.vue') },
]

/** 前台全部模块路由(已带 meta.module) */
export const FRONT_MODULE_ROUTES: RouteRecordRaw[] = MODULES.flatMap((module) =>
  withModule(module.id, module.frontRoutes ?? []),
)

/** 后台全部模块路由(已带 meta.module) */
export const ADMIN_MODULE_ROUTES: RouteRecordRaw[] = MODULES.flatMap((module) =>
  withModule(module.id, module.adminRoutes ?? []),
)

/** 模块 id -> 模块记录 */
export const MODULE_BY_ID = new Map(MODULES.map((module) => [module.id, module]))

/** 带上所属模块 id 的导航项(布局用它过滤模块开关, 后台模块管理页用它展示占用入口) */
export interface ResolvedNavItem extends ModuleNavItem {
  moduleId?: string
}

/**
 * 后台菜单的展示顺序
 *
 * 与模块注册顺序解耦: 模块按"核心/内容/数据/扩展"登记, 而后台菜单按使用频率排,
 * 这里显式列出顺序, 未列出的模块按登记顺序追加在后面
 */
const ADMIN_NAV_ORDER = ['dashboard', 'posts', 'taxonomy', 'comments', 'media', 'users', 'settings', 'modules', 'logs']

function orderedModules(): FrontModule[] {
  const byId = new Map(MODULES.map((module) => [module.id, module]))
  const ordered = ADMIN_NAV_ORDER.map((id) => byId.get(id)).filter((item): item is FrontModule => !!item)
  const rest = MODULES.filter((module) => !ADMIN_NAV_ORDER.includes(module.id))
  return [...ordered, ...rest]
}

/** 前台导航项(核心入口在前, 模块入口按注册顺序) */
export const FRONT_NAV_ITEMS: ResolvedNavItem[] = [
  ...CORE_FRONT_NAV,
  ...MODULES.flatMap((module) => (module.frontNav ?? []).map((item) => ({ ...item, moduleId: module.id }))),
]

/** 后台菜单项(模块入口按 ADMIN_NAV_ORDER, 布局自身的入口在最后) */
export const ADMIN_NAV_ITEMS: ResolvedNavItem[] = [
  ...orderedModules().flatMap((module) => (module.adminNav ?? []).map((item) => ({ ...item, moduleId: module.id }))),
  ...CORE_ADMIN_NAV,
]
