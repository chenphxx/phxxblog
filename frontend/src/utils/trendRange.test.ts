import { describe, expect, it } from 'vitest'
import {
  deltaPercent,
  parseDay,
  previousRange,
  resolveQuickRange,
  spanDays,
  summarize,
} from '@/utils/trendRange'
import type { TrendPoint } from '@/types'

/** 构造一个趋势点, 只关心 KPI 汇总用到的字段 */
function point(label: string, pv: number, uv: number, postViews = 0): TrendPoint {
  return { label, pv, uv, post_views: postViews }
}

/**
 * 区间计算决定环比是否取到正确的天数, 且容易在时区/跨月边界上出错, 因此逐个钉住。
 */
describe('resolveQuickRange', () => {
  const today = new Date(2026, 8, 14) // 2026-09-14

  it('近七天为含今天在内的 7 天', () => {
    expect(resolveQuickRange('7d', today)).toEqual(['2026-09-08', '2026-09-14'])
  })

  it('近30天为含今天在内的 30 天', () => {
    expect(resolveQuickRange('30d', today)).toEqual(['2026-08-16', '2026-09-14'])
  })

  it('本月从当月 1 号到今天', () => {
    expect(resolveQuickRange('month', today)).toEqual(['2026-09-01', '2026-09-14'])
  })

  it('上个月为整月(含 31 号)', () => {
    expect(resolveQuickRange('lastMonth', today)).toEqual(['2026-08-01', '2026-08-31'])
  })

  it('本年从 1 月 1 号到今天', () => {
    expect(resolveQuickRange('year', today)).toEqual(['2026-01-01', '2026-09-14'])
  })

  it('近一年为含今天在内的 365 天', () => {
    expect(spanDays(parseDay(resolveQuickRange('1y', today)[0]), today)).toBe(365)
  })

  it('上一年为上一自然年的整年', () => {
    expect(resolveQuickRange('lastYear', today)).toEqual(['2025-01-01', '2025-12-31'])
  })

  it('跨月边界按自然日回推(3 月 1 日的近七天要落到 2 月)', () => {
    expect(resolveQuickRange('7d', new Date(2026, 2, 1))).toEqual(['2026-02-23', '2026-03-01'])
  })
})

describe('previousRange', () => {
  it('取紧邻的等长区间, 不重叠', () => {
    expect(previousRange('2026-09-08', '2026-09-14')).toEqual(['2026-09-01', '2026-09-07'])
  })

  it('跨月同样成立', () => {
    expect(previousRange('2026-03-01', '2026-03-07')).toEqual(['2026-02-22', '2026-02-28'])
  })
})

describe('summarize', () => {
  it('汇总区间总量、日均与峰值日', () => {
    const kpi = summarize([point('2026-09-12', 10, 4), point('2026-09-13', 30, 6), point('2026-09-14', 20, 5, 7)])
    expect(kpi.pv).toBe(60)
    expect(kpi.uv).toBe(15)
    expect(kpi.postViews).toBe(7)
    expect(kpi.avgPv).toBe(20)
    expect(kpi.peakLabel).toBe('2026-09-13')
    expect(kpi.peakPv).toBe(30)
  })

  it('空区间返回全 0 而不是 NaN', () => {
    const kpi = summarize([])
    expect(kpi).toEqual({ pv: 0, uv: 0, postViews: 0, avgPv: 0, peakLabel: '', peakPv: 0 })
  })

  it('全 0 数据不产生虚假峰值', () => {
    expect(summarize([point('2026-09-13', 0, 0), point('2026-09-14', 0, 0)]).peakPv).toBe(0)
  })
})

describe('deltaPercent', () => {
  it('计算环比百分比', () => {
    expect(deltaPercent(120, 100)).toBeCloseTo(20)
    expect(deltaPercent(80, 100)).toBeCloseTo(-20)
  })

  it('上期为 0 或缺失时返回 null(而不是无穷大)', () => {
    expect(deltaPercent(10, 0)).toBeNull()
    expect(deltaPercent(10, null)).toBeNull()
  })
})
