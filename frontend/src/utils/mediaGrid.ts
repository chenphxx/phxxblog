/**
 * 媒体库栅格的一屏容量计算。
 *
 * 媒体库是"铺满一屏"的栅格(`.media-grid` 的高度由 `calc(100vh - N)` 固定), 因此:
 *   - 每页取多少条必须跟着一屏能放下的格子数走, 否则会出现"还有很多空位却已经翻页";
 *   - 行高不能用 CSS 的 `1fr`, 否则末页只剩一行时那一行会被拉伸占满整屏。
 * 这里的取整决定了"整页正好铺满"还是"多出一条滚动条", 所以抽成纯函数单独测。
 */

/** 与 `MediaManageView.vue` 的 `.media-grid` 保持一致 */
export const CELL_MIN_WIDTH = 200
export const ROW_MIN_HEIGHT = 210
export const GRID_GAP = 16
/** 与后端 `/media` 的 `page_size` 上限一致 */
export const MAX_PAGE_SIZE = 100

/** 一屏栅格的容量与行高 */
export interface MediaGridMetrics {
  /** 一屏能放下的格子数(列 × 行) */
  capacity: number
  /** 每行应有的高度 */
  rowHeight: number
}

/**
 * 按栅格容器的实际尺寸算出一屏容量与行高。
 *
 * @param width 栅格容器宽度(px)
 * @param height 栅格容器高度(px)
 * @return 容量与行高; 宽高为 0(尚未布局)时返回 null, 由调用方沿用上一次的值
 */
export function mediaGridMetrics(width: number, height: number): MediaGridMetrics | null {
  if (width <= 0 || height <= 0) return null
  const columns = Math.max(1, Math.floor((width + GRID_GAP) / (CELL_MIN_WIDTH + GRID_GAP)))
  const rows = Math.max(1, Math.floor((height + GRID_GAP) / (ROW_MIN_HEIGHT + GRID_GAP)))
  return {
    capacity: Math.min(columns * rows, MAX_PAGE_SIZE),
    // 向下取整: 宁可整页底部空出一两个像素, 也不要因为凑满高度而多出一条滚动条
    rowHeight: Math.floor((height - (rows - 1) * GRID_GAP) / rows),
  }
}
