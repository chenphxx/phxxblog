<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowDown, Check, Histogram, TrendCharts } from '@element-plus/icons-vue'
import { statsApi } from '@/api'
import type { TrendPoint } from '@/types'
import TrendChart from '@/components/TrendChart.vue'
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

/**
 * @brief 仪表盘的访问趋势区块
 *
 * 自带区间/粒度/图表类型状态与取数逻辑, 首屏统一加载由页面通过 refresh() 触发
 * (见 HomeView 里辅助模块的同一套做法)
 */
const props = defineProps<{
  /** 今日 PV, 来自页面的聚合首屏请求 */
  todayPv: number
  /** 今日 UV, 来自页面的聚合首屏请求 */
  todayUv: number
  /** 页面级首屏遮罩是否进行中: 首屏由外层统一遮罩, 这里不重复显示 */
  pageLoading: boolean
}>()

const trend = ref<TrendPoint[]>([])

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

/**
 * 当前生效的快捷区间
 *
 * 由 dateRange 反推而不是单独维护一份状态: 手改日期后高亮会自动消失,
 * 不需要再靠 @change 回调去手动同步(那正是两边状态会不一致的原因)
 */
const activeRange = computed<QuickRangeKey | null>(() => {
  if (!dateRange.value) return null
  const current = dateRange.value.join('~')
  return QUICK_RANGES.find((r) => resolveQuickRange(r.key).join('~') === current)?.key ?? null
})

const activeRangeLabel = computed(() => QUICK_RANGES.find((r) => r.key === activeRange.value)?.label ?? '快捷筛选')

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
     * 本期与上期一次取回(而不是发两个请求), 因此需要 2 倍区间长度不超上限
     * 超上限(如自定义 366 天)时只取本期, 环比显示"无上期对比"
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

/** 快捷时间段: 只改区间与粒度, 高亮由 activeRange 反推 */
function applyQuickRange(command: string | number | object) {
  granularity.value = 'day'
  dateRange.value = resolveQuickRange(String(command) as QuickRangeKey)
}

/*
 * 合并成一个 watcher: 点快捷区间会同时改粒度与区间, 分成两个 watcher 会发两次请求
 * 同一个 flush 内多个来源只触发一次回调
 */
watch([granularity, dateRange], loadTrend)

defineExpose({ refresh: loadTrend })
</script>

<template>
  <div class="card">
    <div class="trend-header">
      <div class="trend-title">
        <h3 style="margin: 0">访问趋势</h3>
        <span class="trend-today muted">
          今日 PV <b>{{ props.todayPv }}</b> · UV <b>{{ props.todayUv }}</b>
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
          <el-radio-button value="line"
            ><el-icon><TrendCharts /></el-icon
          ></el-radio-button>
          <el-radio-button value="bar"
            ><el-icon><Histogram /></el-icon
          ></el-radio-button>
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
    <div v-loading="trendLoading && !props.pageLoading" class="chart-body">
      <TrendChart :points="chartPoints" :type="chartType" />
    </div>

    <div class="legend muted">
      <span><i class="swatch-line swatch-pv" />PV</span>
      <span><i class="swatch-line swatch-uv" />UV</span>
      <span class="legend-hint">指向曲线查看单点数值, 也可用左右方向键浏览</span>
    </div>
  </div>
</template>

<style scoped>
.trend-title {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 6px 12px;
}
.trend-today {
  font-variant-numeric: tabular-nums;
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
  font-size: 12px;
  color: var(--muted);
}
.kpi-value {
  font-size: 22px;
  font-weight: 600;
  line-height: 1.25;
  font-variant-numeric: tabular-nums;
  color: var(--text);
}
.kpi-delta {
  font-size: 11px;
  font-variant-numeric: tabular-nums;
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
