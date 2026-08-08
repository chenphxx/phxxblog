<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { statsApi } from '@/api'
import type { CommentItem, PostItem, TrendPoint, VisitItem } from '@/types'
import TrendChart from '@/components/TrendChart.vue'

const overview = ref<Record<string, number>>({})
const trend = ref<TrendPoint[]>([])
const recentPosts = ref<PostItem[]>([])
const recentComments = ref<CommentItem[]>([])
const loading = ref(true)

// 访问记录
const visits = ref<VisitItem[]>([])
const visitsTotal = ref(0)
const visitsPage = ref(1)
const visitsPageSize = 10
const visitsLoading = ref(false)

// 趋势控制
const granularity = ref<'day' | 'month' | 'year'>('day')
const chartType = ref<'line' | 'bar'>('line')
const dateRange = ref<[string, string] | null>(null)
const router = useRouter()

const cards = [
  { key: 'posts', label: '文章数', color: '#0969da', to: '/admin/posts' },
  { key: 'views', label: '总访问量', color: '#cf222e', scroll: 'visits-section' },
  { key: 'comments', label: '评论数', color: '#1a7f37', to: '/admin/comments' },
  { key: 'users', label: '用户数', color: '#9a6700', to: '/admin/users' },
]

const QUICK_RANGES = [
  { key: '7d', label: '近七天' },
  { key: '30d', label: '近30天' },
  { key: 'month', label: '本月' },
  { key: 'lastMonth', label: '上个月' },
  { key: 'year', label: '本年' },
  { key: '1y', label: '近一年' },
  { key: 'lastYear', label: '上一年' },
]

async function loadTrend() {
  trend.value = await statsApi.trend({
    granularity: granularity.value,
    days: granularity.value === 'day' ? 14 : undefined,
    start_date: granularity.value === 'day' && dateRange.value ? dateRange.value[0] : undefined,
    end_date: granularity.value === 'day' && dateRange.value ? dateRange.value[1] : undefined,
  })
}

/** 日视图标签只显示 月-日 */
const chartPoints = computed(() =>
  trend.value.map((p) => ({
    ...p,
    label: granularity.value === 'day' ? p.label.slice(5) : p.label,
  })),
)

function onCardClick(card: (typeof cards)[number]) {
  if (card.to) {
    router.push(card.to)
  } else if (card.scroll) {
    document.getElementById(card.scroll)?.scrollIntoView({ behavior: 'smooth' })
  }
}

function fmtDate(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** 快捷时间段 */
function applyQuickRange(command: string | number | object) {
  const key = String(command)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  let start: Date = today
  let end: Date = today
  if (key === '7d') {
    start = new Date(today); start.setDate(start.getDate() - 6)
  } else if (key === '30d') {
    start = new Date(today); start.setDate(start.getDate() - 29)
  } else if (key === 'month') {
    start = new Date(today.getFullYear(), today.getMonth(), 1)
  } else if (key === 'lastMonth') {
    start = new Date(today.getFullYear(), today.getMonth() - 1, 1)
    end = new Date(today.getFullYear(), today.getMonth(), 0)
  } else if (key === 'year') {
    start = new Date(today.getFullYear(), 0, 1)
  } else if (key === '1y') {
    start = new Date(today); start.setDate(start.getDate() - 364)
  } else if (key === 'lastYear') {
    start = new Date(today.getFullYear() - 1, 0, 1)
    end = new Date(today.getFullYear() - 1, 11, 31)
  }
  dateRange.value = [fmtDate(start), fmtDate(end)]
  granularity.value = 'day'
}

async function loadVisits() {
  visitsLoading.value = true
  try {
    const data = await statsApi.visits({ page: visitsPage.value, page_size: visitsPageSize })
    visits.value = data.items
    visitsTotal.value = data.total
  } finally {
    visitsLoading.value = false
  }
}

watch(granularity, loadTrend)
watch(dateRange, loadTrend)
watch(visitsPage, loadVisits)

onMounted(async () => {
  try {
    const data = await statsApi.dashboard()
    overview.value = data.overview as Record<string, number>
    recentPosts.value = data.recent_posts as PostItem[]
    recentComments.value = data.recent_comments as CommentItem[]
    await Promise.all([loadTrend(), loadVisits()])
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
        <div class="card stat-card clickable" @click="onCardClick(card)">
          <div class="stat-label muted">{{ card.label }}</div>
          <div class="stat-value" :style="{ color: card.color }">{{ overview[card.key] ?? 0 }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 访问趋势 -->
    <div class="card" style="margin-top: 20px">
      <div class="trend-header">
        <h3 style="margin: 0">访问趋势</h3>
        <div class="trend-controls">
          <el-dropdown trigger="click" @command="applyQuickRange">
            <el-button size="small">快捷筛选<el-icon style="margin-left: 4px"><ArrowDown /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="range in QUICK_RANGES" :key="range.key" :command="range.key">
                  {{ range.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-date-picker
            v-if="granularity === 'day'"
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            style="width: 260px"
            :clearable="true"
          />
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button value="line">折线图</el-radio-button>
            <el-radio-button value="bar">柱状图</el-radio-button>
          </el-radio-group>
          <el-radio-group v-model="granularity" size="small">
            <el-radio-button value="day">日</el-radio-button>
            <el-radio-button value="month">月</el-radio-button>
            <el-radio-button value="year">年</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <TrendChart :points="chartPoints" :type="chartType" />
      <div class="legend muted">
        <span><i class="dot dot-pv" /> PV</span>
        <span><i class="dot dot-uv" /> UV</span>
      </div>
    </div>

    <!-- 访问记录 -->
    <div class="card" id="visits-section" style="margin-top: 20px">
      <div class="trend-header">
        <h3 style="margin: 0">访问记录</h3>
        <el-button size="small" @click="visitsPage = 1; loadVisits()">刷新</el-button>
      </div>
      <el-table :data="visits" v-loading="visitsLoading" size="small">
        <el-table-column prop="visit_time" label="时间" width="150">
          <template #default="{ row }">{{ (row.visit_time || '').replace('T', ' ').slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="120" />
        <el-table-column prop="location" label="省市区" width="110" />
        <el-table-column label="设备" width="90">
          <template #default="{ row }">{{ row.device || '-' }}</template>
        </el-table-column>
        <el-table-column prop="browser" label="浏览器" width="90" />
        <el-table-column prop="os" label="系统" width="90" />
        <el-table-column label="文章" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link v-if="row.post_id" :to="`/post/${row.post_id}`">{{ row.post_title || `#${row.post_id}` }}</router-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="referer" label="来源" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.referer || '-' }}</template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="visitsTotal > visitsPageSize"
        v-model:current-page="visitsPage"
        :page-size="visitsPageSize"
        :total="visitsTotal"
        layout="prev, pager, next, total"
        style="justify-content: center; margin-top: 12px"
      />
    </div>

    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :xs="24" :md="12">
        <div class="card">
          <h3>最新文章</h3>
          <el-table :data="recentPosts" size="small" style="cursor: pointer" @row-click="(row: PostItem) => router.push(`/admin/posts/${row.id}/edit`)">
            <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 2 ? 'success' : 'info'">
                  {{ ['草稿', '审核中', '已发布', '私密', '回收站'][row.status] }}
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
          <el-table :data="recentComments" size="small" style="cursor: pointer" @row-click="(row: CommentItem) => router.push(`/post/${row.post_id}`)">
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
.stat-card {
  margin-bottom: 16px;
}
.clickable {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.clickable:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}
.stat-label {
  font-size: 13px;
}
.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-top: 4px;
}
.trend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}
.trend-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.legend {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 12px;
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 4px;
}
.dot-pv {
  background: #0969da;
}
.dot-uv {
  background: #54aeff;
}
</style>
