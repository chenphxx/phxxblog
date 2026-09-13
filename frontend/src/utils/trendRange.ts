/**
 * 访问趋势看板的区间计算与区间汇总。
 *
 * 为什么单独抽成纯函数:
 *   看板要同时算出「本期区间」「上一个等长区间」两份数据(用于环比), 还要按区间做 KPI 汇总。
 *   这些计算散在视图里既容易算错, 又无法测试(视图组件没有测试环境)。
 */
import type { TrendPoint } from '@/types'

/** 快捷区间标识 */
export type QuickRangeKey = '7d' | '30d' | 'month' | 'lastMonth' | 'year' | '1y' | 'lastYear'

/** 快捷区间的展示文案, 顺序即下拉菜单顺序 */
export const QUICK_RANGES: { key: QuickRangeKey; label: string }[] = [
  { key: '7d', label: '近七天' },
  { key: '30d', label: '近30天' },
  { key: 'month', label: '本月' },
  { key: 'lastMonth', label: '上个月' },
  { key: 'year', label: '本年' },
  { key: '1y', label: '近一年' },
  { key: 'lastYear', label: '上一年' },
]

/** 日粒度一次能取的区间上限(与后端 `/stats/trend` 的 `Query(le=366)` 对应) */
export const TREND_MAX_DAYS = 366

/**
 * 把 Date 格式化为 `YYYY-MM-DD`。
 *
 * 不用 `toISOString().slice(0, 10)`: 它按 UTC 取日期, 东八区的 00:00~08:00 会被算成前一天。
 *
 * @param d 待格式化的日期
 * @return 本地时区的 `YYYY-MM-DD`
 */
export function formatDay(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/**
 * 解析 `YYYY-MM-DD` 为**本地零点**的 Date。
 *
 * `new Date('2026-09-14')` 会按 UTC 解析(结果是本地 08:00), 再与本地零点相减会差一天,
 * 所以这里显式拆出年月日交给 Date 构造函数。
 *
 * @param value `YYYY-MM-DD`
 * @return 本地零点日期
 */
export function parseDay(value: string): Date {
  const [y, m, d] = value.split('-').map(Number)
  return new Date(y, (m || 1) - 1, d || 1)
}

/** 按天偏移(跨月/跨年由 Date 构造函数自行进位) */
export function addDays(d: Date, days: number): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + days)
}

/**
 * 两个日期之间相差的天数(含首尾)。
 *
 * 用 UTC 归一化后的「天序号」相减, 避免夏令时切换那天出现 23/25 小时导致算少一天。
 *
 * @return 天数, 起始日晚于结束日时返回 0
 */
export function spanDays(start: Date, end: Date): number {
  const toDayNumber = (d: Date) => Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000
  return Math.max(0, Math.round(toDayNumber(end) - toDayNumber(start)) + 1)
}

/**
 * 计算快捷区间的起止日期。
 *
 * @param key 快捷区间标识
 * @param today 基准日期, 默认今天(注入以便测试)
 * @return `[start, end]`, 均为 `YYYY-MM-DD`
 */
export function resolveQuickRange(key: QuickRangeKey, today = new Date()): [string, string] {
  const base = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  let start = base
  let end = base
  switch (key) {
    case '7d':
      start = addDays(base, -6)
      break
    case '30d':
      start = addDays(base, -29)
      break
    case 'month':
      start = new Date(base.getFullYear(), base.getMonth(), 1)
      break
    case 'lastMonth':
      start = new Date(base.getFullYear(), base.getMonth() - 1, 1)
      end = new Date(base.getFullYear(), base.getMonth(), 0)
      break
    case 'year':
      start = new Date(base.getFullYear(), 0, 1)
      break
    case '1y':
      start = addDays(base, -364)
      break
    case 'lastYear':
      start = new Date(base.getFullYear() - 1, 0, 1)
      end = new Date(base.getFullYear() - 1, 11, 31)
      break
  }
  return [formatDay(start), formatDay(end)]
}

/**
 * 本期区间紧邻的前一个等长区间。
 *
 * @param start 本期起始日 `YYYY-MM-DD`
 * @param end 本期结束日 `YYYY-MM-DD`
 * @return `[start, end]`, 均为 `YYYY-MM-DD`
 */
export function previousRange(start: string, end: string): [string, string] {
  const startDate = parseDay(start)
  const span = spanDays(startDate, parseDay(end))
  return [formatDay(addDays(startDate, -span)), formatDay(addDays(startDate, -1))]
}

/** 区间汇总 KPI */
export interface TrendKpi {
  /** 区间 PV 合计 */
  pv: number
  /** 区间 UV 合计(按日 UV 累加, 不等于区间独立访客数) */
  uv: number
  /** 区间内文章阅读量合计 */
  postViews: number
  /** 日均 PV */
  avgPv: number
  /** PV 最高那天的标签, 全为 0 时为空串 */
  peakLabel: string
  /** PV 最高那天的数值 */
  peakPv: number
}

/** 汇总一个区间的 KPI(空数组返回全 0) */
export function summarize(points: TrendPoint[]): TrendKpi {
  const kpi: TrendKpi = { pv: 0, uv: 0, postViews: 0, avgPv: 0, peakLabel: '', peakPv: 0 }
  for (const p of points) {
    kpi.pv += p.pv
    kpi.uv += p.uv
    kpi.postViews += p.post_views
    if (p.pv > kpi.peakPv) {
      kpi.peakPv = p.pv
      kpi.peakLabel = p.label
    }
  }
  kpi.avgPv = points.length ? kpi.pv / points.length : 0
  return kpi
}

/**
 * 环比增长百分比。
 *
 * @param current 本期总量
 * @param previous 上期总量, 传 null 表示没有上期数据
 * @return 百分比数值(如 12.5 表示 +12.5%), 上期为 0 或无上期数据时返回 null
 */
export function deltaPercent(current: number, previous: number | null): number | null {
  if (previous === null || previous <= 0) return null
  return ((current - previous) / previous) * 100
}
