<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { statsApi } from '@/api'
import type { CommentItem, PostItem } from '@/types'
import MetaIcon, { type IconName } from '@/components/MetaIcon.vue'
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

/*
 * 数据卡片: 强调色不再写死十六进制, 而是引用主题令牌
 * 这样换主题时后台的强调色会跟着变(旧代码写死 GitHub 蓝/红/绿/黄, 换主题后很突兀)
 */
const cards = [
  {
    key: 'posts',
    label: '文章数',
    hint: '含草稿与回收站',
    icon: 'file' as IconName,
    color: 'var(--primary)',
    to: '/admin/posts',
  },
  {
    key: 'views',
    label: '总访问量',
    hint: '全站累计阅读',
    icon: 'eye' as IconName,
    color: 'var(--grad-to)',
    scroll: 'visits-section',
  },
  {
    key: 'comments',
    label: '评论数',
    hint: '含待审核回复',
    icon: 'hash' as IconName,
    color: 'var(--ok)',
    to: '/admin/comments',
  },
  {
    key: 'users',
    label: '用户数',
    hint: '含管理员账号',
    icon: 'user' as IconName,
    color: 'var(--warn)',
    to: '/admin/users',
  },
]

function onCardClick(card: (typeof cards)[number]) {
  if (card.to) {
    router.push(card.to)
  } else if (card.scroll) {
    document.getElementById(card.scroll)?.scrollIntoView({ behavior: 'smooth' })
  }
}

onMounted(async () => {
  try {
    // 返回类型由 statsApi.dashboard() 的 DashboardData 保证, 不再需要 as 断言
    const data = await statsApi.dashboard()
    overview.value = data.overview
    recentPosts.value = data.recent_posts
    recentComments.value = data.recent_comments
    await Promise.all([trendPanelRef.value?.refresh(), visitsTableRef.value?.refresh()])
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading">
    <h2>仪表盘</h2>

    <!-- 数据卡片 -->
    <el-row :gutter="16">
      <el-col v-for="card in cards" :key="card.key" :xs="12" :sm="6">
        <div class="card stat-card clickable" :style="{ '--stat-color': card.color }" @click="onCardClick(card)">
          <div class="stat-head">
            <span class="stat-label">{{ card.label }}</span>
            <span class="stat-icon"><MetaIcon :name="card.icon" size="16" /></span>
          </div>
          <div class="stat-value">{{ overview[card.key] ?? 0 }}</div>
          <div class="stat-hint">{{ card.hint }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 访问趋势 -->
    <DashboardTrendPanel
      ref="trendPanelRef"
      style="margin-top: 20px"
      :today-pv="overview.today_pv ?? 0"
      :today-uv="overview.today_uv ?? 0"
      :page-loading="loading"
    />

    <!-- 访问记录 -->
    <DashboardVisitsTable ref="visitsTableRef" style="margin-top: 20px" />

    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :xs="24" :md="12">
        <div class="card">
          <h3>最新文章</h3>
          <el-table
            :data="recentPosts"
            size="small"
            style="cursor: pointer"
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
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card">
          <h3>最新评论</h3>
          <el-table
            :data="recentComments"
            size="small"
            style="cursor: pointer"
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
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
/* 数据卡片: 用主题强调色做淡底图标, 数字用正文色, 不再写死颜色 */
.stat-card {
  margin-bottom: 16px;
  padding: var(--space-5);
}
.clickable {
  cursor: pointer;
  transition:
    box-shadow var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}
.clickable:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-hover);
}
.stat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.stat-label {
  font-size: 14px;
  color: var(--muted);
}
.stat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: var(--radius-control);
  color: var(--stat-color, var(--primary));
  background: color-mix(in srgb, var(--stat-color, var(--primary)) 14%, transparent);
}
.stat-value {
  font-size: 40px;
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.03em;
  margin-top: var(--space-4);
  font-variant-numeric: tabular-nums;
  color: var(--text);
}
/* 大数字配一句说明, 让指标有口径而不是只有数字 */
.stat-hint {
  margin-top: 6px;
  color: var(--muted);
  font-size: 12.5px;
}
</style>
