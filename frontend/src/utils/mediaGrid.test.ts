import { describe, expect, it } from 'vitest'
import { CELL_MIN_WIDTH, GRID_GAP, MAX_PAGE_SIZE, ROW_MIN_HEIGHT, mediaGridMetrics } from '@/utils/mediaGrid'

/**
 * 这几处取整决定了媒体库"一屏正好铺满"还是"多出一条滚动条 / 少放一行",
 * 所以把边界逐个钉住, 而不是只靠肉眼看页面。
 */
describe('mediaGridMetrics', () => {
  it('按 200px 列宽与 210px 行高算出列数与行数', () => {
    // 宽 2283 -> floor((2283+16)/216) = 10 列; 高 1016 -> floor((1016+16)/226) = 4 行
    expect(mediaGridMetrics(2283, 1016)).toEqual({ capacity: 40, rowHeight: 242 })
  })

  it('铺满时行高之和不超过容器高度(不会多出滚动条)', () => {
    for (const height of [400, 700, 1016, 1200, 1600, 2160]) {
      const metrics = mediaGridMetrics(2283, height)
      expect(metrics).not.toBeNull()
      const rows = Math.floor((height + GRID_GAP) / (ROW_MIN_HEIGHT + GRID_GAP))
      // 行高向下取整, 所以只需贴上界; 同时行高不应小于最小行高(除非容器本身比一行还矮)
      expect(rows * metrics!.rowHeight + (rows - 1) * GRID_GAP).toBeLessThanOrEqual(height)
      expect(metrics!.rowHeight).toBeGreaterThanOrEqual(Math.min(ROW_MIN_HEIGHT, height))
    }
  })

  it('列数随宽度变化', () => {
    // 宽 632 -> floor(648/216) = 3 列
    expect(mediaGridMetrics(632, 1016)?.capacity).toBe(12)
    // 宽 2160 -> floor(2176/216) = 10 列(列宽上限来自 auto-fill 的 1fr)
    expect(mediaGridMetrics(2160, 1016)?.capacity).toBe(40)
  })

  it('容器比一行还矮或还窄时至少保留 1 行 1 列, 且行高不超过容器高度', () => {
    expect(mediaGridMetrics(120, 150)).toEqual({ capacity: 1, rowHeight: 150 })
    expect(mediaGridMetrics(CELL_MIN_WIDTH, ROW_MIN_HEIGHT)).toEqual({ capacity: 1, rowHeight: ROW_MIN_HEIGHT })
  })

  it('容量不超过后端 page_size 上限', () => {
    // 4K: 宽 3700 -> 17 列, 高 2000 -> 9 行 => 153, 应被截到 100
    expect(mediaGridMetrics(3700, 2000)?.capacity).toBe(MAX_PAGE_SIZE)
  })

  it('尚未布局(宽或高为 0)时返回 null, 由调用方沿用上一次的值', () => {
    expect(mediaGridMetrics(0, 1016)).toBeNull()
    expect(mediaGridMetrics(2283, 0)).toBeNull()
  })
})
