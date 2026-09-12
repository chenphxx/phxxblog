import type { CSSProperties } from 'vue'

/**
 * 分类/标签配色。
 *
 * 优先使用后台配置的颜色; 未配置时按名称生成稳定的兜底色,
 * 保证所有分类/标签在任何页面上都有背景色。
 */

const HEX_RE = /^#(?:[0-9a-f]{3}|[0-9a-f]{6})$/i

/** 阅读量与点赞数的固定配色(与分类/标签共用同一套渲染方式) */
export const VIEWS_COLOR = '#0284c7'
export const LIKES_COLOR = '#e11d48'

/** 名称 -> 稳定色相(0-359) */
function hueFromName(name: string): number {
  let hash = 0
  for (let i = 0; i < name.length; i += 1) {
    hash = (hash * 31 + name.charCodeAt(i)) % 360
  }
  return hash
}

/** 生成标签背景色样式(浅色/深色模式均自动适配) */
export function chipStyle(name: string, color?: string | null): CSSProperties {
  const base = color && HEX_RE.test(color) ? color : `hsl(${hueFromName(name)} 68% 45%)`
  return {
    background: `color-mix(in srgb, ${base} 16%, transparent)`,
    borderColor: `color-mix(in srgb, ${base} 42%, transparent)`,
    color: `color-mix(in srgb, ${base} 88%, var(--text))`,
  }
}
