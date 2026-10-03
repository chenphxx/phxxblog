/**
 * 主题令牌推导
 *
 * 改造后的主题模型只接受两类输入(见 tokens.mjs):
 *   primary  品牌色
 *   bg       页面画布底色
 *
 * 其余令牌(文字/边框/卡片/语义色/终端/热力图)都在统一的中性基准上推导,
 * 因此 9 套主题只差品牌色与背景色, 视觉语言完全一致
 *
 * 这里同时导出生成器(base.css / theme-<id>.css)与自检脚本共用的工具函数,
 * 对比度算法只有这一份, 避免两处各写一遍导致标准漂移
 */

/**
 * 每套主题在两种模式下都会产出的颜色令牌键
 * 生成器会检查是否齐全, 自检脚本会检查生成物里是否写进去了
 */
export const COLOR_KEYS = [
  'bg',
  'cardBg',
  'text',
  'muted',
  'border',
  'borderStrong',
  'primary',
  'primaryStrong',
  'primaryWeak',
  'onPrimary',
  'link',
  'codeBg',
  'codeBlockBg',
  'ok',
  'warn',
  'danger',
  'ring',
  'gradFrom',
  'gradTo',
  'termBg',
  'termBorder',
  'termText',
  'termDim',
  'termAccent',
  'termPrompt',
  'cell0',
  'cell1',
  'cell2',
  'cell3',
  'cell4',
]

/** 颜色令牌键 -> CSS 变量名(顺序即输出顺序) */
export const COLOR_VARS = [
  ['bg', '--bg'],
  ['cardBg', '--card-bg'],
  ['text', '--text'],
  ['muted', '--muted'],
  ['border', '--border'],
  ['borderStrong', '--border-strong'],
  ['primary', '--primary'],
  ['primaryStrong', '--primary-strong'],
  ['primaryWeak', '--primary-weak'],
  ['onPrimary', '--on-primary'],
  ['link', '--link'],
  ['codeBg', '--code-bg'],
  ['codeBlockBg', '--code-block-bg'],
  ['ok', '--ok'],
  ['warn', '--warn'],
  ['danger', '--danger'],
  ['ring', '--ring'],
  ['gradFrom', '--grad-from'],
  ['gradTo', '--grad-to'],
  ['termBg', '--term-bg'],
  ['termBorder', '--term-border'],
  ['termText', '--term-text'],
  ['termDim', '--term-dim'],
  ['termAccent', '--term-accent'],
  ['termPrompt', '--term-prompt'],
  ['cell0', '--cell-0'],
  ['cell1', '--cell-1'],
  ['cell2', '--cell-2'],
  ['cell3', '--cell-3'],
  ['cell4', '--cell-4'],
]

/** 字体栈: UI 文字用系统无衬线, 等宽只留给代码/终端/数字 */
export const FONT_SANS =
  "'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', 'PingFang SC', 'HarmonyOS Sans SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif"
export const FONT_MONO =
  "'Cascadia Code', 'Cascadia Mono', 'JetBrains Mono', ui-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"

/**
 * 与主题无关的结构令牌(间距/圆角/阴影/动效)
 *
 * 这些值对所有主题完全一致 - 主题只改变颜色, 不再改变圆角与阴影气质,
 * 生成器把它们写进 themes/base.css 的 :root, 全站只出现一次
 */
export const STRUCTURE_TOKENS = [
  ['--space-1', '4px'],
  ['--space-2', '8px'],
  ['--space-3', '12px'],
  ['--space-4', '16px'],
  ['--space-5', '20px'],
  ['--space-6', '24px'],
  ['--space-8', '32px'],
  ['--space-10', '40px'],
  ['--space-12', '48px'],
  ['--space-16', '64px'],
  ['--radius-panel', '28px'],
  ['--radius-card', '20px'],
  ['--radius-control', '12px'],
  ['--radius-chip', '10px'],
  ['--radius-pill', '999px'],
  /* 旧令牌保留为别名, 既有组件样式不必逐个改类名 */
  ['--radius', 'var(--radius-card)'],
  ['--radius-sm', 'var(--radius-control)'],
  ['--radius-lg', 'var(--radius-panel)'],
  ['--shadow-panel', '0 1px 2px rgba(17, 17, 17, 0.04), 0 20px 44px -30px rgba(17, 17, 17, 0.22)'],
  ['--shadow-float', '0 2px 6px rgba(17, 17, 17, 0.06), 0 30px 60px -32px rgba(17, 17, 17, 0.3)'],
  ['--shadow', 'var(--shadow-panel)'],
  ['--shadow-hover', 'var(--shadow-float)'],
  ['--dur', '200ms'],
  ['--ease', 'cubic-bezier(0.22, 0.72, 0.28, 1)'],
  ['--code-fold-height', '420px'],
]

/** 深色模式下阴影需要更重一点才看得出来, base.css 里单独覆盖这两项 */
export const DARK_SHADOW_TOKENS = [
  ['--shadow-panel', '0 1px 2px rgba(0, 0, 0, 0.5), 0 22px 46px -30px rgba(0, 0, 0, 0.75)'],
  ['--shadow-float', '0 2px 8px rgba(0, 0, 0, 0.55), 0 32px 64px -34px rgba(0, 0, 0, 0.85)'],
]

/**
 * 与主题无关的中性色基准
 *
 * 浅色下卡片恒为白色(参考稿的"白面板 + 灰画布"), 深色下卡片由主题背景色微微提亮,
 * 文字/边框/语义色在 9 套主题间完全一致 - 换主题只换品牌色与画布
 */
export const NEUTRAL = {
  light: {
    text: '#171717',
    muted: '#6b6b6b',
    border: '#e6e6e6',
    borderStrong: '#d4d4d4',
    codeBg: '#f2f2f2',
    codeBlockBg: '#ffffff',
    ok: '#18794e',
    warn: '#8a5a1f',
    danger: '#b8272c',
    termBg: '#121212',
    termBorder: '#2b2b2b',
    termText: '#e6e6e6',
    termDim: '#909090',
    termPrompt: '#fafafa',
    cell0: '#ececec',
  },
  dark: {
    text: '#ededed',
    muted: '#a3a3a3',
    border: '#2c2c2c',
    borderStrong: '#3c3c3c',
    codeBg: '#1b1b1b',
    codeBlockBg: '#1e1e1e',
    ok: '#5cc98d',
    warn: '#dfb167',
    danger: '#ef8073',
    termBg: '#0c0c0c',
    termBorder: '#272727',
    termText: '#e6e6e6',
    termDim: '#8b8b8b',
    termPrompt: '#fafafa',
    cell0: '#262626',
  },
}

/** 主按钮上的文字只在这两个候选里选, 都比纯黑/纯白更耐看 */
const ON_PRIMARY_DARK = '#141414'
const ON_PRIMARY_LIGHT = '#ffffff'

/*
 * ---------------------------------------------------------------
 * 颜色工具
 * ---------------------------------------------------------------
 */

/**
 * @brief 把 #rgb / #rrggbb / #rrggbbaa 解析成 [r, g, b]
 *
 * @param {string} hex 十六进制颜色
 * @return {number[]} RGB 三元组
 */
export function toRgb(hex) {
  let body = hex.replace('#', '')
  if (body.length === 3) {
    body = body
      .split('')
      .map((c) => c + c)
      .join('')
  }
  return [0, 2, 4].map((i) => parseInt(body.slice(i, i + 2), 16))
}

/**
 * @brief 把 [r, g, b] 写成小写十六进制
 *
 * @param {number[]} rgb RGB 三元组
 * @return {string} 十六进制颜色
 */
function toHex(rgb) {
  return (
    '#' +
    rgb
      .map((v) =>
        Math.round(Math.min(255, Math.max(0, v)))
          .toString(16)
          .padStart(2, '0'),
      )
      .join('')
  )
}

/**
 * @brief 按权重把 a 混向 b
 *
 * @param {string} a 起点颜色
 * @param {string} b 终点颜色
 * @param {number} weightB 终点权重(0 = 全 a, 1 = 全 b)
 * @return {string} 混合后的颜色
 */
export function mix(a, b, weightB) {
  const x = toRgb(a)
  const y = toRgb(b)
  return toHex(x.map((v, i) => v * (1 - weightB) + y[i] * weightB))
}

/**
 * @brief 给十六进制颜色补上透明度
 *
 * @param {string} hex 十六进制颜色
 * @param {number} alpha 透明度 0~1
 * @return {string} #rrggbbaa
 */
export function withAlpha(hex, alpha) {
  const body = hex.replace('#', '').slice(0, 6)
  const tail = Math.round(alpha * 255)
    .toString(16)
    .padStart(2, '0')
  return '#' + body + tail
}

/**
 * @brief 相对亮度(WCAG 2.x)
 *
 * @param {string} hex 十六进制颜色
 * @return {number} 相对亮度
 */
export function relLum(hex) {
  return toRgb(hex)
    .map((v) => v / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)))
    .reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0)
}

/**
 * @brief WCAG 对比度
 *
 * @param {string} a 颜色一
 * @param {string} b 颜色二
 * @return {number} 对比度倍数
 */
export function contrast(a, b) {
  const l1 = relLum(a)
  const l2 = relLum(b)
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
}

/**
 * @brief 两个颜色的 RGB 欧氏距离, 用来判断肉眼是否可辨
 *
 * @param {string} a 颜色一
 * @param {string} b 颜色二
 * @return {number} 距离
 */
export function rgbDistance(a, b) {
  const x = toRgb(a)
  const y = toRgb(b)
  return Math.sqrt(x.reduce((s, v, i) => s + (v - y[i]) ** 2, 0))
}

/**
 * @brief 把颜色朝 toward 逐步混合, 直到与背景的对比度达标
 *
 * @param {string} color 待调整的颜色
 * @param {string} bg 背景色
 * @param {number} ratio 目标对比度
 * @param {string} toward 调整方向(#000000 变暗 / #ffffff 变亮)
 * @return {string} 满足对比度的颜色
 */
export function ensureContrast(color, bg, ratio, toward) {
  let current = color
  for (let i = 0; i < 20; i += 1) {
    if (contrast(current, bg) >= ratio) return current
    current = mix(current, toward, 0.08)
  }
  return current
}

/**
 * @brief 推导装饰渐变的起点色
 *
 * 渐变只用在品牌标记这类小面积图形上, 因此要求"与主色肉眼可辨"而不是对比度:
 * 暗色主色朝白走一档, 亮色主色朝黑走一档, 保证两端始终拉得开
 *
 * @param {string} primary 品牌色
 * @return {string} 渐变起点色
 */
export function gradientStart(primary) {
  return relLum(primary) < 0.35 ? mix(primary, '#ffffff', 0.35) : mix(primary, '#000000', 0.35)
}

/*
 * ---------------------------------------------------------------
 * 单一主题 + 模式的令牌推导
 * ---------------------------------------------------------------
 */

/**
 * @brief 由品牌色与画布色推导出该模式下完整的颜色令牌
 *
 * @param {object} theme tokens.mjs 里的一套主题
 * @param {'light'|'dark'} mode 模式
 * @return {Record<string, string>} COLOR_KEYS 对应的令牌表
 */
export function deriveMode(theme, mode) {
  const input = theme[mode]
  if (!input || !input.primary || !input.bg) {
    throw new Error(`主题 ${theme.id} 的 ${mode} 必须提供 primary 与 bg`)
  }

  const base = NEUTRAL[mode]
  const isLight = mode === 'light'
  /* 深色下卡片比画布亮一档, 浅色下卡片恒为白色(白面板 + 灰画布) */
  const cardBg = isLight ? '#ffffff' : mix(input.bg, '#ffffff', 0.07)
  const towardBlack = isLight ? '#000000' : '#ffffff'

  const primary = input.primary
  const onPrimary =
    contrast(ON_PRIMARY_LIGHT, primary) >= contrast(ON_PRIMARY_DARK, primary) ? ON_PRIMARY_LIGHT : ON_PRIMARY_DARK
  const termBg = base.termBg
  const termAccent = input.termAccent || ensureContrast(primary, termBg, 4.5, '#ffffff')

  return {
    bg: input.bg,
    cardBg,
    text: base.text,
    muted: base.muted,
    border: base.border,
    borderStrong: base.borderStrong,
    primary,
    primaryStrong: mix(primary, towardBlack, isLight ? 0.22 : 0.18),
    /* 主色淡底: 从卡片底色朝主色混一点点, 用来做选中态/悬停底色 */
    primaryWeak: mix(cardBg, primary, isLight ? 0.1 : 0.16),
    onPrimary,
    /* 链接是"主色当文字用": 达不到 4.5:1 时朝背景的反方向调整 */
    link: ensureContrast(primary, cardBg, 4.5, towardBlack),
    codeBg: isLight ? base.codeBg : mix(cardBg, '#ffffff', 0.06),
    codeBlockBg: base.codeBlockBg,
    ok: base.ok,
    warn: base.warn,
    danger: base.danger,
    ring: withAlpha(primary, 0.3),
    gradFrom: input.gradFrom || gradientStart(primary),
    gradTo: input.gradTo || primary,
    termBg,
    termBorder: base.termBorder,
    termText: base.termText,
    termDim: base.termDim,
    termAccent,
    termPrompt: base.termPrompt,
    cell0: base.cell0,
    /* 热力图由浅到深: 从 cell0 朝主色递进, 换成近黑/浅色品牌色时梯度依然单调 */
    cell1: mix(base.cell0, primary, 0.18),
    cell2: mix(base.cell0, primary, 0.42),
    cell3: mix(base.cell0, primary, 0.68),
    cell4: primary,
  }
}

/**
 * @brief 按 Element Plus 的混合规则, 从主色推导整套 --el-color-* 色阶
 *
 * EP 默认: light-N = mix(white, primary, N*10%), dark-2 = mix(black, primary, 20%)
 *
 * @param {string} primary 品牌色
 * @return {{light3: string, light5: string, light7: string, light8: string, light9: string, dark2: string}}
 */
export function elementScale(primary) {
  return {
    light3: mix(primary, '#ffffff', 0.3),
    light5: mix(primary, '#ffffff', 0.5),
    light7: mix(primary, '#ffffff', 0.7),
    light8: mix(primary, '#ffffff', 0.8),
    light9: mix(primary, '#ffffff', 0.9),
    dark2: mix(primary, '#000000', 0.2),
  }
}
