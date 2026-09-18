/**
 * @brief 站点链接的图标与显示名
 *
 * 首页的个人资料(社交账号)与常用网站两块都要"先按域名取图标, 取不到退回站点根目录的
 * favicon.ico, 再取不到就藏起来", 这里集中一份。分开写两份时很容易出现只有一处修好的情况,
 * 表现为首页上"一个链接有图标, 另一个同样的链接是空白"。
 */

/**
 * @brief 取站点图标的地址
 * @param url 目标站点地址
 * @return 图标地址; url 不是合法地址时返回空串, 调用方据此不渲染 img
 */
export function faviconOf(url: string): string {
  try {
    return `https://www.google.com/s2/favicons?domain=${new URL(url).hostname}&sz=64`
  } catch {
    return ''
  }
}

/**
 * @brief 图标加载失败时退回站点根目录的 favicon.ico
 *
 * 事件回调没有返回值, 只能直接改 img: 二次失败就隐藏, 否则浏览器会显示裂图。
 *
 * @param event img 的 error 事件
 * @param url 目标站点地址
 */
export function onFaviconError(event: Event, url: string): void {
  const img = event.target as HTMLImageElement
  try {
    img.src = `https://${new URL(url).hostname}/favicon.ico`
  } catch {
    img.style.visibility = 'hidden'
  }
}

/**
 * @brief 链接的显示名
 * @param link 链接配置, 可带自定义名称
 * @return 优先用配置的名称, 其次域名, 最后原样返回 url
 */
export function linkName(link: { name?: string; url: string }): string {
  if (link.name) return link.name
  try {
    return new URL(link.url).hostname
  } catch {
    return link.url
  }
}
