/**
 * 媒体库栅格的分页容量计算
 *
 * 媒体库一页固定放 MAX_PAGE_ROWS 行, 一行的格子数由容器宽度决定, 超出部分翻页查看:
 *   - 每页条数不能写死成常数, 否则窗口一宽就会出现"还有很多空位却已经翻页";
 *   - 行高由 CSS 固定(`.media-grid` 的 `grid-auto-rows`), 一页 10 行的高度因此是稳定的,
 *     放不下的部分由后台主内容区滚动, 而不是压缩行数去铺满一屏
 */

/** 与 `MediaManageView.vue` 的 `.media-grid` 保持一致 */
export const CELL_MIN_WIDTH = 200
export const GRID_GAP = 16
/** 与后端 `/media` 的 `page_size` 上限一致 */
export const MAX_PAGE_SIZE = 100
/** 每页的行数: 超过就翻页 */
export const MAX_PAGE_ROWS = 10

/** 一页的容量 */
export interface MediaGridMetrics {
  /** 一页的格子数(列 × 每页行数) */
  capacity: number
}

/**
 * 按栅格容器的实际宽度算出一页的容量
 *
 * @param width 栅格容器宽度(px)
 * @return 一页的格子数; 宽度为 0(尚未布局)时返回 null, 由调用方沿用上一次的值
 */
export function mediaGridMetrics(width: number): MediaGridMetrics | null {
  if (width <= 0) return null
  const columns = Math.max(1, Math.floor((width + GRID_GAP) / (CELL_MIN_WIDTH + GRID_GAP)))
  return { capacity: Math.min(columns * MAX_PAGE_ROWS, MAX_PAGE_SIZE) }
}
