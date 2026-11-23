<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { statsApi } from '@/api'
import type { CommentItem, PostItem } from '@/types'
import MetaIcon, { type IconName } from '@/components/MetaIcon.vue'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import { POST_STATUS_TEXT } from '@/utils/postStatus'
import DashboardTrendPanel from './DashboardTrendPanel.vue'
import DashboardVisitsTable from './DashboardVisitsTable.vue'

const overview = ref<Record<string, number>>({})
const recentPosts = ref<PostItem[]>([])
const recentComments = ref<CommentItem[]>([])
const loading = ref(true)
const router = useRouter()

/**
 * 两个辅助区块的实例引用
 *
 * 趋势与访问记录各自持有状态与分页, 但首屏统一加载仍由页面触发,
 * 这样外层的 v-loading 能一直遮到全部首屏数据就绪(与 HomeView 里辅助模块的做法一致)
 */
const trendPanelRef = ref<InstanceType<typeof DashboardTrendPanel> | null>(null)
const visitsTableRef = ref<InstanceType<typeof DashboardVisitsTable> | null>(null)

const todayLabel = computed(() =>
    new Intl.DateTimeFormat
    (
        'zh-CN',
        {
            month: 'long',
            day: 'numeric',
            weekday: 'long',
        },
    ).format(new Date()),
)

/** 概览数字按当前语言添加千位分隔符, 避免长数字难以扫读 */
function formatNumber(value: number | undefined): string
{
    return (value ?? 0).toLocaleString('zh-CN')
}

const cards = computed(() =>
[
    {
        key: 'posts',
        label: '文章',
        description: '全部内容',
        icon: 'file' as IconName,
        color: 'var(--primary)',
        to: '/admin/posts',
    },
    {
        key: 'views',
        label: '访问',
        description: `今日 ${overview.value.today_pv ?? 0} PV · ${overview.value.today_uv ?? 0} UV`,
        icon: 'eye' as IconName,
        color: 'var(--grad-to)',
        scroll: 'visits-section',
    },
    {
        key: 'comments',
        label: '评论',
        description: '已收录评论',
        icon: 'hash' as IconName,
        color: 'var(--ok)',
        to: '/admin/comments',
    },
    {
        key: 'users',
        label: '用户',
        description: '站点账号',
        icon: 'user' as IconName,
        color: 'var(--warn)',
        to: '/admin/users',
    },
])

function onCardClick(card: (typeof cards.value)[number])
{
    if (card.to)
    {
        router.push(card.to)
    }
    else if (card.scroll)
    {
        document.getElementById(card.scroll)?.scrollIntoView({ behavior: 'smooth' })
    }
}

onMounted(async () =>
{
    try
    {
        const data = await statsApi.dashboard()
        overview.value = data.overview
        recentPosts.value = data.recent_posts
        recentComments.value = data.recent_comments
        await Promise.all([trendPanelRef.value?.refresh(), visitsTableRef.value?.refresh()])
    } finally
    {
        loading.value = false
    }
})
</script>

<template>
    <div v-loading="loading" class="dashboard-page">
        <AdminPageHeader eyebrow="Overview" title="仪表盘">
            <template #actions>
                <span class="dashboard-date">{{ todayLabel }}</span>
                <el-button @click="router.push('/')">查看前台</el-button>
                <el-button type="primary" @click="router.push('/admin/posts/new')">新建文章</el-button>
            </template>
        </AdminPageHeader>

        <div class="stats-grid">
            <button
                v-for="card in cards"
                :key="card.key"
                class="card stat-card"
                type="button"
                :style="{ '--stat-color': card.color }"
                @click="onCardClick(card)"
            >
                <span class="stat-head">
                    <span class="stat-label">{{ card.label }}</span>
                    <span class="stat-icon"><MetaIcon :name="card.icon" size="16" /></span>
                </span>
                <strong class="stat-value">{{ formatNumber(overview[card.key]) }}</strong>
                <span class="stat-description">{{ card.description }}</span>
            </button>
        </div>

        <DashboardTrendPanel
            ref="trendPanelRef"
            class="dashboard-block"
            :today-pv="overview.today_pv ?? 0"
            :today-uv="overview.today_uv ?? 0"
            :page-loading="loading"
        />

        <DashboardVisitsTable ref="visitsTableRef" class="dashboard-block" />

        <div class="recent-grid">
            <section class="card recent-card">
                <div class="recent-head">
                    <h3>最新文章</h3>
                    <el-button text @click="router.push('/admin/posts')">查看全部</el-button>
                </div>
                <el-table
                    :data="recentPosts"
                    size="small"
                    class="recent-table"
                    @row-click="(row: PostItem) => router.push(`/admin/posts/${row.id}/edit`)"
                >
                    <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
                    <el-table-column prop="status" label="状态" width="80">
                        <template #default="{ row }">
                            <el-tag size="small" :type="row.status === 2 ? 'success' : 'info'">
                                {{ POST_STATUS_TEXT[row.status] }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="views" label="阅读" width="70" />
                </el-table>
            </section>

            <section class="card recent-card">
                <div class="recent-head">
                    <h3>最新评论</h3>
                    <el-button text @click="router.push('/admin/comments')">管理评论</el-button>
                </div>
                <el-table
                    :data="recentComments"
                    size="small"
                    class="recent-table"
                    @row-click="(row: CommentItem) => router.push(`/post/${row.post_id}`)"
                >
                    <el-table-column label="评论人" width="100">
                        <template #default="{ row }">{{ row.author_name || '匿名' }}</template>
                    </el-table-column>
                    <el-table-column prop="content" label="内容" min-width="160" show-overflow-tooltip />
                    <el-table-column label="时间" width="100">
                        <template #default="{ row }">{{ row.created_at.slice(0, 10) }}</template>
                    </el-table-column>
                </el-table>
            </section>
        </div>
    </div>
</template>

<style scoped>
.dashboard-date
{
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 11px;
    white-space: nowrap;
}

.stats-grid
{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
}

.stat-card
{
    display: flex;
    min-width: 0;
    flex-direction: column;
    align-items: stretch;
    padding: 18px;
    color: var(--text);
    font-family: inherit;
    text-align: left;
    cursor: pointer;
    transition:
        border-color var(--dur) var(--ease),
        background-color var(--dur) var(--ease),
        transform var(--dur) var(--ease);
}

.stat-card:hover
{
    border-color: var(--admin-border-strong);
    background: color-mix(in srgb, var(--admin-surface) 94%, var(--admin-surface-muted));
    transform: translateY(-1px);
}

.stat-head
{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.stat-label
{
    color: var(--muted);
    font-size: 12px;
    font-weight: 550;
}

.stat-icon
{
    display: inline-flex;
    width: 28px;
    height: 28px;
    align-items: center;
    justify-content: center;
    border: 1px solid color-mix(in srgb, var(--stat-color, var(--primary)) 18%, var(--admin-border));
    border-radius: var(--admin-radius-sm);
    background: color-mix(in srgb, var(--stat-color, var(--primary)) 8%, var(--admin-surface));
    color: var(--stat-color, var(--primary));
}

.stat-value
{
    margin-top: 18px;
    color: var(--text);
    font-size: 32px;
    font-weight: 650;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.045em;
    line-height: 1;
}

.stat-description
{
    margin-top: 8px;
    overflow: hidden;
    color: var(--muted);
    font-size: 11.5px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.dashboard-block
{
    margin-top: 16px;
}

.recent-grid
{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    margin-top: 16px;
}

.recent-card
{
    min-width: 0;
    padding: 0;
    overflow: hidden;
}

.recent-head
{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 16px 18px 12px;
}

.recent-head h3
{
    margin: 0;
    color: var(--text);
    font-size: 14px;
    font-weight: 650;
}

.recent-table
{
    cursor: pointer;
}

@media (max-width: 1100px)
{
    .stats-grid
    {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 760px)
{
    .dashboard-date
    {
        width: 100%;
    }

    .recent-grid
    {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 520px)
{
    .stats-grid
    {
        grid-template-columns: 1fr;
    }
}
</style>
