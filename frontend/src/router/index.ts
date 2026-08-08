import { createRouter, createWebHashHistory } from 'vue-router'

// 记录离开页面时的滚动位置, 返回时恢复
const savedScrollPositions = new Map<string, number>()

const router = createRouter({
  history: createWebHashHistory(),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    if (from.fullPath && from.fullPath !== to.fullPath) {
      savedScrollPositions.set(from.fullPath, window.scrollY || 0)
    }
    const top = savedScrollPositions.get(to.fullPath) ?? 0
    if (top > 0) {
      return { top, behavior: 'smooth' }
    }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/SiteLayout.vue'),
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
        { path: 'post/:id', name: 'post-detail', component: () => import('@/views/PostDetailView.vue') },
        { path: 'archive', name: 'archive', component: () => import('@/views/ArchiveView.vue') },
        { path: 'posts', name: 'all-posts', component: () => import('@/views/AllPostsView.vue') },
        { path: 'search', name: 'search', component: () => import('@/views/SearchView.vue') },
        { path: 'write', name: 'write', component: () => import('@/views/WriteView.vue'), meta: { requiresAuth: true } },
        { path: 'write/:id', name: 'write-edit', component: () => import('@/views/WriteView.vue'), meta: { requiresAuth: true } },
        { path: 'mine', name: 'mine', component: () => import('@/views/MyPostsView.vue'), meta: { requiresAuth: true } },
        { path: 'changelog', name: 'changelog', component: () => import('@/views/ChangelogView.vue'), meta: { requiresAuth: true } },
        { path: 'diary', name: 'diary', component: () => import('@/views/DiaryView.vue'), meta: { requiresAuth: true } },
      ],
    },
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('@/views/admin/LoginView.vue'),
    },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/admin/dashboard' },
        { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/views/admin/DashboardView.vue') },
        { path: 'posts', name: 'admin-posts', component: () => import('@/views/admin/PostManageView.vue') },
        { path: 'posts/new', name: 'admin-post-new', component: () => import('@/views/admin/PostEditView.vue') },
        { path: 'posts/:id/edit', name: 'admin-post-edit', component: () => import('@/views/admin/PostEditView.vue') },
        { path: 'categories', name: 'admin-categories', component: () => import('@/views/admin/CategoryTagView.vue') },
        { path: 'comments', name: 'admin-comments', component: () => import('@/views/admin/CommentManageView.vue') },
        { path: 'media', name: 'admin-media', component: () => import('@/views/admin/MediaManageView.vue') },
        { path: 'users', name: 'admin-users', component: () => import('@/views/admin/UserManageView.vue') },
        { path: 'settings', name: 'admin-settings', component: () => import('@/views/admin/SettingsView.vue') },
        { path: 'logs', name: 'admin-logs', component: () => import('@/views/admin/LogsView.vue') },
        { path: 'profile', name: 'admin-profile', component: () => import('@/views/admin/ProfileView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('blog_access_token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
