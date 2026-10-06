import { createRouter, createWebHashHistory } from 'vue-router'
import { ADMIN_MODULE_ROUTES, CORE_ADMIN_ROUTES, FRONT_MODULE_ROUTES } from '@/modules/registry'
import { useModulesStore } from '@/stores/modules'
import { getAccessToken } from '@/utils/tokenStorage'

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
        // 首页属于布局自身: 即使模块全被禁用, 站点也要有一个可访问的落地页
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
        // 其余页面由模块注册表提供(见 modules/registry.ts)
        ...FRONT_MODULE_ROUTES,
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
      children: [{ path: '', redirect: '/admin/dashboard' }, ...ADMIN_MODULE_ROUTES, ...CORE_ADMIN_ROUTES],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth && !getAccessToken()) {
    return { name: 'admin-login', query: { redirect: to.fullPath } }
  }

  // 模块开关: 页面属于某个模块时, 先确认该模块当前可用
  const moduleId = to.meta.module as string | undefined
  if (!moduleId) {
    return true
  }
  const modules = useModulesStore()
  await modules.load()
  if (modules.isEnabled(moduleId)) {
    return true
  }
  // 模块被禁用: 后台页面回落到"个人资料"(它不属于任何模块), 前台回首页
  return { path: to.path.startsWith('/admin') ? '/admin/profile' : '/' }
})

export default router
