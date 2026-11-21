<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Close, HomeFilled, Menu as MenuIcon, Notebook } from '@element-plus/icons-vue'
import { ADMIN_NAV_ITEMS } from '@/modules/registry'
import { useAuthStore } from '@/stores/auth'
import { useModulesStore } from '@/stores/modules'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'

const auth = useAuthStore()
const modules = useModulesStore()
const router = useRouter()
const route = useRoute()
const siteIcon = ref('')
const siteName = ref('博客管理')
const navOpen = ref(false)

const activeMenu = computed(() =>
{
    if (route.path.startsWith('/admin/posts/')) return '/admin/posts'
    if (route.path.startsWith('/admin/chronicles/')) return '/admin/chronicles'
    return route.path
})

const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))

/**
 * 后台菜单: 由模块注册表生成, 再按模块开关与管理员身份过滤
 *
 * 模块被禁用时对应菜单项直接消失, 布局不需要知道系统里有哪些模块
 */
const menuItems = computed(() =>
    ADMIN_NAV_ITEMS.filter((item) =>
    {
        if (item.adminOnly && !isAdmin.value) return false
        if (item.gated !== false && item.moduleId && !modules.isEnabled(item.moduleId)) return false
        return true
    }),
)

/**
 * 后台侧栏分组
 *
 * 分组只负责信息架构, 菜单项仍来自模块注册表并按模块开关过滤; 未归类的模块
 * 会在后续新增时落入"系统", 避免模块入口因新增而消失
 */
const ADMIN_MENU_GROUPS =
[
    { id: 'overview', label: '概览', moduleIds: ['dashboard'] },
    {
        id: 'content',
        label: '内容',
        moduleIds: ['posts', 'chronicles', 'taxonomy', 'comments', 'media'],
    },
    {
        id: 'system',
        label: '系统',
        moduleIds: ['users', 'settings', 'modules', 'logs'],
    },
    { id: 'account', label: '账户', moduleIds: ['admin'] },
] as const

const groupedModuleIds = new Set<string>(ADMIN_MENU_GROUPS.flatMap((group) => group.moduleIds))

/** 系统设置固定在侧栏底部, 不参与其余菜单滚动 */
const PINNED_ADMIN_MODULE_ID = 'settings'
const scrollableMenuItems = computed(() => menuItems.value.filter((item) => item.moduleId !== PINNED_ADMIN_MODULE_ID))
const pinnedMenuItem = computed(() => menuItems.value.find((item) => item.moduleId === PINNED_ADMIN_MODULE_ID))

const menuGroups = computed(() =>
    ADMIN_MENU_GROUPS.map((group) => ({
        ...group,
        items: scrollableMenuItems.value.filter((item) =>
        {
            if (group.id === 'system')
            {
                return (
                    group.moduleIds.some((moduleId) => moduleId === item.moduleId) ||
                    !item.moduleId ||
                    !groupedModuleIds.has(item.moduleId)
                )
            }
            return group.moduleIds.some((moduleId) => moduleId === item.moduleId)
        }),
    })).filter((group) => group.items.length > 0),
)

const pageTitle = computed(() => menuItems.value.find((item) => item.to === activeMenu.value)?.label ?? '博客管理')

/** 新窗口打开后端 API 文档(仅 admin 可访问) */
function openDocs()
{
    window.open('/docs', '_blank', 'noopener,noreferrer')
}

async function logout()
{
    await ElMessageBox.confirm('确定退出登录吗?', '提示', { type: 'warning' })
    const { authApi } = await import('@/api')
    if (auth.refreshToken)
    {
        authApi.logout(auth.refreshToken).catch(() =>
        {})
    }
    auth.logout()
    router.push('/')
}

function handleUserCommand(command: string)
{
    navOpen.value = false
    if (command === 'profile') router.push('/admin/profile')
    if (command === 'logout') logout()
}

function closeNavOnEscape(event: KeyboardEvent)
{
    if (event.key === 'Escape') navOpen.value = false
}

watch(
    () => route.fullPath,
    () =>
    {
        navOpen.value = false
    },
)

onMounted(() =>
{
    // 先拿模块开关, 菜单才能正确过滤(拿不到时按"全部可用"处理)
    modules.load()
    // 每次进入后台都用当前令牌重新确认用户与权限, 同时触发过期令牌的静默刷新
    if (auth.accessToken)
    {
        auth.fetchMe().catch(() =>
        {})
    }
    // 浏览器标签页名称(与前台保持一致)
    import('@/api').then(({ settingsApi }) =>
        settingsApi
            .public()
            .then((data) =>
            {
                document.title = data.site_title || data.site_name || 'phxxblog'
                siteIcon.value = data.site_icon
                siteName.value = data.site_name || '博客管理'
            })
            .catch(() =>
            {}),
    )
    window.addEventListener('keydown', closeNavOnEscape)
})

onBeforeUnmount(() =>
{
    window.removeEventListener('keydown', closeNavOnEscape)
})
</script>

<template>
    <div class="admin-shell">
        <button
            v-if="navOpen"
            class="admin-sidebar-backdrop"
            type="button"
            aria-label="关闭导航"
            @click="navOpen = false"
        />

        <aside id="admin-sidebar" class="admin-sidebar" :class="{ 'is-open': navOpen }">
            <div class="admin-sidebar-head">
                <router-link to="/admin/dashboard" class="admin-brand">
                    <span class="admin-brand-mark" :class="{ 'has-site-icon': siteIcon }" aria-hidden="true">
                        <img v-if="siteIcon" :src="siteIcon" alt="" />
                        <template v-else>PX</template>
                    </span>
                    <span class="admin-brand-copy">
                        <strong>{{ siteName }}</strong>
                        <span>Admin console</span>
                    </span>
                </router-link>
                <button class="admin-sidebar-close" type="button" aria-label="关闭导航" @click="navOpen = false">
                    <el-icon><Close /></el-icon>
                </button>
            </div>

            <nav class="admin-nav" aria-label="后台功能导航">
                <section v-for="group in menuGroups" :key="group.id" class="admin-nav-group">
                    <p class="admin-nav-group-label">{{ group.label }}</p>
                    <router-link
                        v-for="item in group.items"
                        :key="item.to"
                        :to="item.to"
                        class="admin-nav-link"
                        :class="{ 'is-active': activeMenu === item.to }"
                        @click="navOpen = false"
                    >
                        <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
                        <span>{{ item.label }}</span>
                    </router-link>
                </section>
            </nav>

            <div v-if="pinnedMenuItem" class="admin-sidebar-footer">
                <nav aria-label="固定菜单">
                    <router-link
                        :to="pinnedMenuItem.to"
                        class="admin-nav-link"
                        :class="{ 'is-active': activeMenu === pinnedMenuItem.to }"
                        @click="navOpen = false"
                    >
                        <el-icon v-if="pinnedMenuItem.icon"><component :is="pinnedMenuItem.icon" /></el-icon>
                        <span>{{ pinnedMenuItem.label }}</span>
                    </router-link>
                </nav>
            </div>
        </aside>

        <div class="admin-workspace">
            <header class="admin-header">
                <div class="admin-header-left">
                    <button
                        class="admin-mobile-trigger"
                        type="button"
                        aria-controls="admin-sidebar"
                        :aria-expanded="navOpen"
                        aria-label="打开导航"
                        @click="navOpen = true"
                    >
                        <el-icon><MenuIcon /></el-icon>
                    </button>
                    <div class="admin-header-context">
                        <span>管理后台</span>
                        <strong>{{ pageTitle }}</strong>
                    </div>
                </div>
                <div class="admin-header-right">
                    <router-link to="/" class="back-home" aria-label="返回前台">
                        <el-icon><HomeFilled /></el-icon>
                        <span>返回前台</span>
                    </router-link>
                    <el-button v-if="isAdmin" class="docs-btn" aria-label="API 文档" @click="openDocs">
                        <el-icon><Notebook /></el-icon>
                        <span>API 文档</span>
                    </el-button>
                    <ThemeSwitcher />
                    <el-dropdown @command="handleUserCommand">
                        <span class="user-chip">
                            <el-avatar :size="28">{{ (auth.user?.nickname || '管')[0] }}</el-avatar>
                            <span>{{ auth.user?.nickname || auth.user?.username || '未登录' }}</span>
                        </span>
                        <template #dropdown>
                            <el-dropdown-menu>
                                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                            </el-dropdown-menu>
                        </template>
                    </el-dropdown>
                </div>
            </header>

            <main class="admin-main">
                <div class="admin-main-inner">
                    <router-view />
                </div>
            </main>
        </div>
    </div>
</template>
