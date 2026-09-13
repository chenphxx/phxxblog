<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown, Check, Histogram, TrendCharts } from '@element-plus/icons-vue'
import { statsApi } from '@/api'
import type { CommentItem, PostItem, TrendPoint, VisitItem } from '@/types'
import TrendChart from '@/components/TrendChart.vue'
import MetaIcon, { type IconName } from '@/components/MetaIcon.vue'
import {
  QUICK_RANGES,
  TREND_MAX_DAYS,
  addDays,
  deltaPercent,
  formatDay,
  parseDay,
  previousRange,
  resolveQuickRange,
  spanDays,
  summarize,
  type QuickRangeKey,
} from '@/utils/trendRange'

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

/** 日粒度默认看近 14 天(与后端 dashboard 的聚合窗口一致) */
const DEFAULT_DAYS = 14

/** 日粒度当前区间; 初值即为默认区间, 避免"图形是 14 天但日期框是空的" */
function defaultDayRange(): [string, string] {
  const today = new Date()
  return [formatDay(addDays(today, -(DEFAULT_DAYS - 1))), formatDay(today)]
}

const dateRange = ref<[string, string] | null>(defaultDayRange())
const trendLoading = ref(false)
/** 上期 PV 合计, null 表示当前粒度/区间没有可比的上期数据 */
const prevPv = ref<number | null>(null)
const router = useRouter()

/*
 * 数据卡片: 强调色不再写死十六进制, 而是引用主题令牌。
 * 这样换主题时后台的强调色会跟着变(旧代码写死 GitHub 蓝/红/绿/黄, 换主题后很突兀)。
 */
const cards = [
  { key: 'posts', label: '文章数', icon: 'file' as IconName, color: 'var(--primary)', to: '/admin/posts' },
  { key: 'views', label: '总访问量', icon: 'eye' as IconName, color: 'var(--grad-to)', scroll: 'visits-section' },
  { key: 'comments', label: '评论数', icon: 'hash' as IconName, color: 'var(--ok)', to: '/admin/comments' },
  { key: 'users', label: '用户数', icon: 'user' as IconName, color: 'var(--warn)', to: '/admin/users' },
]

/**
 * 当前生效的快捷区间。
 *
 * 由 dateRange 反推而不是单独维护一份状态: 手改日期后高亮会自动消失,
 * 不需要再靠 @change 回调去手动同步(那正是两边状态会不一致的原因)。
 */
const activeRange = computed<QuickRangeKey | null>(() => {
  if (!dateRange.value) return null
  const current = dateRange.value.join('~')
  return QUICK_RANGES.find((r) => resolveQuickRange(r.key).join('~') === current)?.key ?? null
})

const activeRangeLabel = computed(
  () => QUICK_RANGES.find((r) => r.key === activeRange.value)?.label ?? '快捷筛选',
)

/** 区间 KPI: 总量/日均/峰值 */
const kpi = computed(() => summarize(trend.value))

/** 环比: 上期为 0 或没有上期数据时为 null, 不做除法 */
const delta = computed(() => deltaPercent(kpi.value.pv, prevPv.value))

/** 均值口径随粒度变化: 日粒度才是"日均" */
const avgLabel = computed(() =>
  granularity.value === 'day' ? '日均 PV' : granularity.value === 'month' ? '月均 PV' : '年均 PV',
)

async function loadTrend() {
  trendLoading.value = true
  try {
    if (granularity.value !== 'day') {
      // 月/年粒度由后端固定窗口(近 12 个月 / 有数据的最近 6 年), 没有可比的上期区间
      prevPv.value = null
      trend.value = await statsApi.trend({ granularity: granularity.value })
      return
    }
    const [start, end] = dateRange.value ?? defaultDayRange()
    const span = spanDays(parseDay(start), parseDay(end))
    /*
     * 本期与上期一次取回(而不是发两个请求), 因此需要 2 倍区间长度不超上限。
     * 超上限(如自定义 366 天)时只取本期, 环比显示"无上期对比"。
     */
    if (span > 0 && span * 2 <= TREND_MAX_DAYS) {
      const [prevStart] = previousRange(start, end)
      const all = await statsApi.trend({ granularity: 'day', start_date: prevStart, end_date: end })
      trend.value = all.slice(span)
      prevPv.value = summarize(all.slice(0, span)).pv
    } else {
      trend.value = await statsApi.trend({ granularity: 'day', start_date: start, end_date: end })
      prevPv.value = null
    }
  } finally {
    trendLoading.value = false
  }
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

/** 快捷时间段: 只改区间与粒度, 高亮由 activeRange 反推 */
function applyQuickRange(command: string | number | object) {
  granularity.value = 'day'
  dateRange.value = resolveQuickRange(String(command) as QuickRangeKey)
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

/*
 * 合并成一个 watcher: 点快捷区间会同时改粒度与区间, 分成两个 watcher 会发两次请求。
 * 同一个 flush 内多个来源只触发一次回调。
 */
watch([granularity, dateRange], loadTrend)
watch(visitsPage, loadVisits)

onMounted(async () => {
  try {
    // 返回类型由 statsApi.dashboard() 的 DashboardData 保证, 不再需要 as 断言
    const data = await statsApi.dashboard()
    overview.value = data.overview
    recentPosts.value = data.recent_posts
    recentComments.value = data.recent_comments
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
        <div
          class="card stat-card clickable"
          :style="{ '--stat-color': card.color }"
          @click="onCardClick(card)"
        >
          <div class="stat-head">
            <span class="stat-label muted">{{ card.label }}</span>
            <span class="stat-icon"><MetaIcon :name="card.icon" size="16" /></span>
          </div>
          <div class="stat-value">{{ overview[card.key] ?? 0 }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 访问趋势 -->
    <div class="card" style="margin-top: 20px">
      <div class="trend-header">
        <div class="trend-title">
          <h3 style="margin: 0">访问趋势</h3>
          <span class="trend-today muted">
            今日 PV <b>{{ overview.today_pv ?? 0 }}</b> · UV <b>{{ overview.today_uv ?? 0 }}</b>
          </span>
        </div>
        <div class="trend-controls">
          <el-dropdown trigger="click" @command="applyQuickRange">
            <el-button size="small" :type="activeRange ? 'primary' : 'default'">
              {{ activeRangeLabel }}
              <el-icon style="margin-left: 4px"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="range in QUICK_RANGES" :key="range.key" :command="range.key">
                  <el-icon v-if="range.key === activeRange"><Check /></el-icon>
                  <span :class="{ 'is-current-range': range.key === activeRange }">{{ range.label }}</span>
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
          <span v-else class="muted range-hint">月/年粒度使用固定窗口, 不支持自定义区间</span>
          <el-radio-group v-model="chartType" size="small" aria-label="图表类型">
            <el-radio-button value="line"><el-icon><TrendCharts /></el-icon></el-radio-button>
            <el-radio-button value="bar"><el-icon><Histogram /></el-icon></el-radio-button>
          </el-radio-group>
          <el-radio-group v-model="granularity" size="small" aria-label="统计粒度">
            <el-radio-button value="day">日</el-radio-button>
            <el-radio-button value="month">月</el-radio-button>
            <el-radio-button value="year">年</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- 区间 KPI: 让看板先给结论, 再给曲线 -->
      <div class="trend-kpi" :class="{ 'is-loading': trendLoading }">
        <div class="kpi">
          <span class="kpi-label">区间总 PV</span>
          <span class="kpi-value">{{ kpi.pv.toLocaleString() }}</span>
          <span v-if="delta !== null" class="kpi-delta" :class="delta >= 0 ? 'is-up' : 'is-down'">
            {{ delta >= 0 ? '↑' : '↓' }}{{ Math.abs(delta).toFixed(1) }}%
            <em class="muted">较上期</em>
          </span>
          <span v-else class="kpi-delta muted">无上期对比</span>
        </div>
        <div class="kpi">
          <span class="kpi-label" title="按天去重 UV 的累加值, 不等于区间内的独立访客数">区间 UV 累加</span>
          <span class="kpi-value">{{ kpi.uv.toLocaleString() }}</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">{{ avgLabel }}</span>
          <span class="kpi-value">{{ kpi.avgPv.toFixed(1) }}</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">峰值日</span>
          <span class="kpi-value">{{ kpi.peakPv ? kpi.peakPv.toLocaleString() : '-' }}</span>
          <span class="kpi-delta muted">{{ kpi.peakLabel || '暂无数据' }}</span>
        </div>
      </div>

      <!-- 首屏由外层 v-loading 统一遮罩, 这里只在切换区间/粒度时单独提示 -->
      <div v-loading="trendLoading && !loading" class="chart-body">
        <TrendChart :points="chartPoints" :type="chartType" />
      </div>

      <div class="legend muted">
        <span><i class="swatch-line swatch-pv" />PV</span>
        <span><i class="swatch-line swatch-uv" />UV</span>
        <span class="legend-hint">指向曲线查看单点数值, 也可用左右方向键浏览</span>
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
  /* 数据卡片: 用主题强调色做淡底图标, 数字用正文色, 不再写死颜色 */
  .stat-card {
    margin-bottom: 16px;
    padding: 14px 16px;
  }
  .clickable {
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  }
  .clickable:hover {
    transform: translateY(-2px);
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
    font-size: 13px;
  }
  .stat-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: var(--radius-sm);
    color: var(--stat-color, var(--primary));
    background: color-mix(in srgb, var(--stat-color, var(--primary)) 14%, transparent);
  }
  .stat-value {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    margin-top: 8px;
    color: var(--text);
  }
  .trend-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 12px;
  }
  .trend-title {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 6px 12px;
  }
  .trend-today {
    font-family: var(--font-mono);
  }
  .trend-today b {
    color: var(--text);
  }
  .trend-controls {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
  }
  .range-hint {
    font-size: 12px;
  }
  /* 快捷区间下拉里当前生效项: 加粗并用主题色, 与选中态的按钮呼应 */
  .is-current-range {
    color: var(--primary);
    font-weight: 600;
  }

  /* ---------- 区间 KPI ---------- */
  .trend-kpi {
    display: flex;
    flex-wrap: wrap;
    gap: 12px 32px;
    padding: 14px 0 10px;
    margin-top: 4px;
    border-top: 1px solid var(--border);
    transition: opacity var(--dur) var(--ease);
  }
  .trend-kpi.is-loading {
    opacity: 0.55;
  }
  .kpi {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 92px;
  }
  .kpi-label {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 0.02em;
  }
  .kpi-value {
    font-family: var(--font-mono);
    font-size: 21px;
    font-weight: 700;
    line-height: 1.25;
    color: var(--text);
  }
  .kpi-delta {
    font-family: var(--font-mono);
    font-size: 11px;
  }
  .kpi-delta em {
    font-style: normal;
  }
  .kpi-delta.is-up {
    color: var(--ok);
  }
  .kpi-delta.is-down {
    color: var(--danger);
  }

  /* 图表容器: 给 v-loading 遮罩留出与图一致的高度, 避免加载时卡片高度跳动 */
  .chart-body {
    min-height: 260px;
  }

  .legend {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 8px;
    font-size: 12px;
    flex-wrap: wrap;
  }
  /* 图例与图内线条同源: 都取 TrendChart 里的同名令牌, 保证颜色始终一致 */
  .swatch-line {
    display: inline-block;
    width: 16px;
    height: 2px;
    margin-right: 6px;
    vertical-align: middle;
  }
  .swatch-pv {
    background: var(--primary);
  }
  .swatch-uv {
    background: repeating-linear-gradient(90deg, var(--grad-to) 0 5px, transparent 5px 9px);
  }
  .legend-hint {
    margin-left: auto;
    opacity: 0.8;
  }
  @media (max-width: 720px) {
    .legend-hint {
      margin-left: 0;
    }
  }
</style>
