/** 时间格式化: 统一展示为 YYYY-MM-DD HH:mm:ss。 */
export function formatDateTime(value?: string | null): string {
  if (!value) return '-'
  return value.replace('T', ' ').slice(0, 19)
}

/** 日期部分(YYYY-MM-DD), 用于时间轴分组等只需要日期的场景。 */
export function formatDate(value?: string | null): string {
  return formatDateTime(value).slice(0, 10)
}
