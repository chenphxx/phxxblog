import { describe, expect, it } from 'vitest'
import { formatDate, formatDateTime } from '@/utils/datetime'

/**
 * 时间格式化是所有列表/详情页共用的, 改动会影响全站显示, 因此值得钉住行为。
 */
describe('formatDateTime', () => {
  it('把 ISO 字符串转成 "YYYY-MM-DD HH:mm:ss"', () => {
    expect(formatDateTime('2026-09-14T10:20:30')).toBe('2026-09-14 10:20:30')
  })

  it('保留毫秒与更长的部分会被裁掉', () => {
    expect(formatDateTime('2026-09-14T10:20:30.123456')).toBe('2026-09-14 10:20:30')
  })

  it('带时区偏移的字符串按原样截断(不做时区换算)', () => {
    expect(formatDateTime('2026-09-14T10:20:30+08:00')).toBe('2026-09-14 10:20:30')
  })

  it('空值统一显示为 "-"', () => {
    expect(formatDateTime(null)).toBe('-')
    expect(formatDateTime(undefined)).toBe('-')
    expect(formatDateTime('')).toBe('-')
  })
})

describe('formatDate', () => {
  it('只取日期部分', () => {
    expect(formatDate('2026-09-14T10:20:30')).toBe('2026-09-14')
  })

  it('空值同样返回 "-"', () => {
    expect(formatDate(null)).toBe('-')
  })
})
