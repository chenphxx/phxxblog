/**
 * 由同目录的 tokens.mjs 生成前端主题 CSS。
 *
 * 为什么要有生成器:
 *   主题有 12 套, 每套手写 400 行 CSS 既重复又会漂移(改一处忘一处)。
 *   这里把「与主题无关的结构」抽成模板, 只让令牌数据变化, 保证 12 套主题的
 *   增强层完全一致、只有配色与圆角/阴影/动效参数不同。
 *
 * 目录位置: frontend/src/styles/themes/_source/
 * 输出位置: 上一级目录(frontend/src/styles/themes/theme-<id>.css 与 registry.ts)
 *
 * 用法: npm run themes:generate   (或 node src/styles/themes/_source/generate-themes.mjs)
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { THEMES, COLOR_KEYS } from './tokens.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
// _source 的上一级就是主题产物目录; 再往上是 frontend/
const outDir = path.resolve(here, '..')
const repo = path.resolve(here, '../../../..')

/* ---------------------------------------------------------------
 * 令牌键 -> CSS 变量名(顺序即输出顺序)
 * ------------------------------------------------------------- */
const ORDERED_KEYS = [
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

/**
 * 按 Element Plus 的混合规则, 从一个十六进制主色推导整套 --el-color-* 色阶。
 * EP 默认: light-N = mix(white, primary, N*10%), dark-2 = mix(black, primary, 20%)
 */
function mix(hexA, hexB, weightB) {
  const parse = (h) => {
    const s = h.replace('#', '')
    return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16))
  }
  const a = parse(hexA)
  const b = parse(hexB)
  const out = a.map((v, i) => Math.round(v * (1 - weightB) + b[i] * weightB))
  return '#' + out.map((v) => v.toString(16).padStart(2, '0')).join('')
}

/** 主色色阶: 浅色模式混白, 深色模式也混白(EP 的 light 系列始终是偏浅的强调底) */
function elementScale(primary) {
  return {
    light3: mix(primary, '#ffffff', 0.3),
    light5: mix(primary, '#ffffff', 0.5),
    light7: mix(primary, '#ffffff', 0.7),
    light8: mix(primary, '#ffffff', 0.8),
    light9: mix(primary, '#ffffff', 0.9),
    dark2: mix(primary, '#000000', 0.2),
  }
}

/* ---------------------------------------------------------------
 * 渲染: 令牌块
 * ------------------------------------------------------------- */
function renderTokens(t, mode) {
  const c = t[mode]
  const missing = COLOR_KEYS.filter((k) => !c[k])
  if (missing.length) throw new Error(`${t.id}.${mode} 缺少令牌: ${missing.join(', ')}`)

  const lines = ORDERED_KEYS.map(([k, name]) => `  ${name}: ${c[k]};`)

  // 与圆角/阴影/动效相关的令牌(两种模式共用同一套, 但按 EP 约定深浅各写一份也无妨)
  const scale = elementScale(c.primary)
  const isDark = mode === 'dark'
  const shadow = isDark
    ? '0 1px 2px rgba(0, 0, 0, 0.45), 0 12px 32px -20px rgba(0, 0, 0, 0.7)'
    : '0 1px 2px rgba(16, 45, 32, 0.04), 0 8px 24px -14px rgba(16, 45, 32, 0.18)'
  const shadowHover = isDark
    ? '0 6px 14px -6px var(--ring), 0 26px 46px -26px rgba(0, 0, 0, 0.8)'
    : '0 4px 10px -4px var(--ring), 0 22px 40px -22px rgba(16, 45, 32, 0.28)'

  const rest = [
    `--radius: ${t.radius};`,
    `--radius-sm: ${t.radius === '6px' ? '5px' : t.radius === '16px' ? '12px' : '8px'};`,
    `--radius-lg: ${t.radius};`,
    '--radius-pill: 999px;',
    `--shadow: ${shadow};`,
    `--shadow-hover: ${shadowHover};`,
    '--ease: cubic-bezier(0.22, 0.72, 0.28, 1);',
    `--dur: ${t.family === 'hard' ? '170ms' : t.family === 'editorial' ? '280ms' : '220ms'};`,
    '--accent-grad: linear-gradient(135deg, var(--grad-from), var(--grad-to));',
    '',
    '/* Element Plus 主色对齐(色阶由主色推导, 保证 EP 组件与主题一致) */',
    `--el-color-primary: ${c.primary};`,
    `--el-color-primary-light-3: ${scale.light3};`,
    `--el-color-primary-light-5: ${scale.light5};`,
    `--el-color-primary-light-7: ${scale.light7};`,
    `--el-color-primary-light-8: ${scale.light8};`,
    `--el-color-primary-light-9: ${scale.light9};`,
    `--el-color-primary-dark-2: ${scale.dark2};`,
    `--el-border-radius-base: ${t.radius === '6px' ? '6px' : t.radius === '16px' ? '12px' : '10px'};`,
    `--el-border-radius-small: ${t.radius === '6px' ? '5px' : '8px'};`,
    '--el-border-radius-round: 999px;',
    `--el-bg-color: ${c.cardBg};`,
    `--el-bg-color-overlay: ${c.cardBg};`,
    `--el-fill-color: ${c.bg};`,
    `--el-fill-color-light: color-mix(in srgb, ${c.bg} 60%, ${c.cardBg});`,
    `--el-fill-color-lighter: color-mix(in srgb, ${c.bg} 30%, ${c.cardBg});`,
    `--el-text-color-primary: ${c.text};`,
    `--el-text-color-regular: color-mix(in srgb, ${c.text} 78%, ${c.muted});`,
    `--el-text-color-secondary: ${c.muted};`,
    `--el-border-color: ${c.borderStrong};`,
    `--el-border-color-light: ${c.border};`,
    `--el-border-color-lighter: color-mix(in srgb, ${c.border} 60%, ${c.cardBg});`,
  ]

  return [...lines, '', ...rest].join('\n')
}

/* ---------------------------------------------------------------
 * 渲染: 增强层
 * ------------------------------------------------------------- */
const FAMILY_VALUES = {
  soft: {
    POST_BAR_W: '3px',
    POST_BAR_BG: 'linear-gradient(to bottom, var(--grad-from), var(--grad-to))',
    BTN_BG: 'var(--accent-grad)',
    BTN_BORDER: 'transparent',
    BTN_SHADOW: '0 6px 16px -10px var(--ring)',
    BTN_HOVER_BG: 'var(--accent-grad)',
    BTN_HOVER_BORDER: 'transparent',
    BTN_HOVER_TRANSFORM: 'translateY(-1px)',
    BTN_HOVER_SHADOW: '0 10px 22px -12px var(--ring)',
    BTN_ACTIVE_TRANSFORM: 'translateY(0) scale(0.985)',
    PAGER_ACTIVE_BG: 'var(--accent-grad)',
    PAGER_ACTIVE_BORDER: 'transparent',
    RADIUS_PILL_OR_SM: 'var(--radius-pill)',
    NAV_A_BASE: 'border-radius: var(--radius-pill);\n  padding: 6px 13px;',
    NAV_A_HOVER: 'background: var(--primary-weak);\n  color: var(--primary-strong);',
    NAV_A_ACTIVE: 'font-weight: 600;',
    NAV_EXTRA: '',
    TERM_EXTRA: '',
    TIMELINE_HOVER_SHADOW: '0 0 0 2px var(--primary), 0 0 0 7px var(--ring)',
    TIMELINE_HOVER_TRANSFORM: 'none',
    MARKDOWN_EXTRA: '',
    KEYFRAME_NAME: 'rise-in',
    RISE_Y: '10px',
    RISE_DUR: '420ms',
  },
  hard: {
    POST_BAR_W: '2px',
    POST_BAR_BG: 'var(--primary)',
    BTN_BG: 'var(--primary)',
    BTN_BORDER: 'var(--primary)',
    BTN_SHADOW: '3px 3px 0 color-mix(in srgb, var(--primary) 26%, transparent)',
    BTN_HOVER_BG: 'var(--primary-strong)',
    BTN_HOVER_BORDER: 'var(--primary-strong)',
    BTN_HOVER_TRANSFORM: 'translate(-1px, -1px)',
    BTN_HOVER_SHADOW:
      '5px 5px 0 color-mix(in srgb, var(--primary) 34%, transparent), 0 0 22px -6px var(--ring)',
    BTN_ACTIVE_TRANSFORM: 'translate(1px, 1px)',
    PAGER_ACTIVE_BG: 'var(--primary)',
    PAGER_ACTIVE_BORDER: 'var(--primary)',
    RADIUS_PILL_OR_SM: 'var(--radius)',
    NAV_A_BASE: 'border-radius: var(--radius-sm);\n  font-weight: 600;',
    NAV_A_HOVER: 'background: var(--primary-weak);\n  color: var(--primary);',
    NAV_A_ACTIVE:
      'color: var(--primary);\n  background: var(--primary-weak);\n  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--primary) 35%, transparent);',
    NAV_EXTRA: '',
    TERM_EXTRA: '',
    TIMELINE_HOVER_SHADOW: '0 0 0 2px var(--primary), 0 0 18px -2px var(--ring)',
    TIMELINE_HOVER_TRANSFORM: 'none',
    MARKDOWN_EXTRA: '',
    KEYFRAME_NAME: 'snap-in',
    RISE_Y: '8px',
    RISE_DUR: '300ms',
  },
  editorial: {
    POST_BAR_W: '3px',
    POST_BAR_BG: 'linear-gradient(to bottom, var(--grad-from), var(--grad-to))',
    BTN_BG: 'var(--primary)',
    BTN_BORDER: 'var(--primary)',
    BTN_SHADOW: '0 8px 18px -14px var(--ring)',
    BTN_HOVER_BG: 'var(--primary-strong)',
    BTN_HOVER_BORDER: 'var(--primary-strong)',
    BTN_HOVER_TRANSFORM: 'translateY(-1px)',
    BTN_HOVER_SHADOW: '0 8px 18px -14px var(--ring)',
    BTN_ACTIVE_TRANSFORM: 'none',
    PAGER_ACTIVE_BG: 'var(--primary)',
    PAGER_ACTIVE_BORDER: 'var(--primary)',
    RADIUS_PILL_OR_SM: 'var(--radius-sm)',
    NAV_A_BASE: 'border-radius: 0;\n  color: var(--muted);',
    NAV_A_HOVER: 'background: transparent;\n  color: var(--text);',
    NAV_A_ACTIVE: 'background: transparent;\n  color: var(--primary-strong);\n  font-weight: 600;',
    NAV_EXTRA: `/* 导航细下划线(编辑族用线条而不是色块) */
.site-nav a {
  position: relative;
}

.site-nav a::after {
  content: '';
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 2px;
  height: 1px;
  background: currentColor;
  transform: scaleX(0);
  transition: transform var(--dur) var(--ease);
}

.site-nav a:hover::after,
.site-nav a.router-link-active::after {
  transform: scaleX(1);
}`,
    TERM_EXTRA: '',
    TIMELINE_HOVER_SHADOW: 'none',
    TIMELINE_HOVER_TRANSFORM: 'scale(1.15)',
    MARKDOWN_EXTRA: '',
    KEYFRAME_NAME: 'fade-up',
    RISE_Y: '8px',
    RISE_DUR: '460ms',
  },
  /**
   * minimal: 文档站气质(VitePress / Teek, 即 cuanmu.com 的风格)。
   * 只做很轻的反馈: 细边框、极淡阴影、颜色过渡, 不使用位移与硬阴影。
   */
  minimal: {
    POST_BAR_W: '2px',
    POST_BAR_BG: 'var(--primary)',
    BTN_BG: 'var(--primary)',
    BTN_BORDER: 'var(--primary)',
    BTN_SHADOW: '0 1px 2px rgba(0, 0, 0, 0.06)',
    BTN_HOVER_BG: 'var(--primary-strong)',
    BTN_HOVER_BORDER: 'var(--primary-strong)',
    BTN_HOVER_TRANSFORM: 'none',
    BTN_HOVER_SHADOW: '0 2px 6px rgba(0, 0, 0, 0.1)',
    BTN_ACTIVE_TRANSFORM: 'none',
    PAGER_ACTIVE_BG: 'var(--primary)',
    PAGER_ACTIVE_BORDER: 'var(--primary)',
    RADIUS_PILL_OR_SM: 'var(--radius)',
    NAV_A_BASE: 'border-radius: var(--radius);\n  color: var(--muted);',
    NAV_A_HOVER: 'background: var(--code-bg);\n  color: var(--text);',
    NAV_A_ACTIVE: 'background: var(--primary-weak);\n  color: var(--link);\n  font-weight: 600;',
    NAV_EXTRA: '',
    TERM_EXTRA: '',
    TIMELINE_HOVER_SHADOW: '0 0 0 2px var(--primary)',
    TIMELINE_HOVER_TRANSFORM: 'none',
    MARKDOWN_EXTRA: '',
    KEYFRAME_NAME: 'fade-in',
    RISE_Y: '6px',
    RISE_DUR: '360ms',
  },
}

function renderEnhance(t) {
  const base = fs.readFileSync(path.join(here, 'enhance.base.css'), 'utf8')
  const family = fs.readFileSync(path.join(here, `enhance-${t.family}.css`), 'utf8')
  const values = FAMILY_VALUES[t.family]
  if (!values) throw new Error(`未知的增强层族: ${t.family}`)

  let css = family.replace('@@BASE@@', base.trimEnd())
  for (const [k, v] of Object.entries(values)) {
    css = css.split(`@@${k}@@`).join(v)
  }
  const left = css.match(/@@[A-Z_]+@@/g)
  if (left) throw new Error(`${t.id}: 增强层还有未替换的占位符 ${[...new Set(left)].join(', ')}`)
  return css
}

/* ---------------------------------------------------------------
 * 主流程
 * ------------------------------------------------------------- */
fs.mkdirSync(outDir, { recursive: true })

const template = fs.readFileSync(path.join(here, 'template.css'), 'utf8')
const ids = new Set()

/** 主题文件头部注释 */
function renderHeader(t) {
  return `/* ============================================================
 * 主题: ${t.name} (${t.en})
 * ${t.desc}
 * ------------------------------------------------------------
 * 本文件由 src/styles/themes/_source/generate-themes.mjs 生成, 请勿手改。
 * 改配色/圆角请改 _source/tokens.mjs, 然后重新运行:
 *   npm run themes:generate
 *
 * 切换方式: html[data-theme='${t.id}'] (见 stores/theme.ts), 深色再加 .dark
 * ============================================================ */`
}

/* ---------------------------------------------------------------
 * 默认主题的令牌写进裸 :root
 * 这样 12 套主题里只有默认那套占着 :root, 新访客(还没选过主题)
 * 看到的就是它, 不存在"谁在后面谁覆盖"的问题。
 *
 * 这里同时写入共享令牌(字体、代码折叠高度), 让该文件自成一体:
 * 就算不加载任何 theme-<id>.css, 页面也有完整可用的字体与配色。
 * ------------------------------------------------------------- */
const defaultTheme = THEMES[0]
const defaultRoot = `/* ============================================================
 * 默认主题: ${defaultTheme.name} (${defaultTheme.en})
 * 新访客(未在 localStorage 里存过主题)看到的就是这一套。
 * 下面的裸 :root 浅色令牌属于它; 其余主题只写
 * html[data-theme='<id>'], 两者互不覆盖。
 * 想换默认主题: 把 tokens.mjs 里想用的那套挪到 THEMES 数组第一位。
 * ============================================================ */

:root {
  /* 超过 20 行的代码块折叠后的高度(MarkdownView 会覆盖这个值) */
  --code-fold-height: 420px;

  /*
   * 字体: 字母 / 数字 / 符号统一用 Cascadia Code。
   * Cascadia Code 不含中文字形, 中文会自动回退到后面的系统字体
   * (PingFang SC / 微软雅黑), 中文排版质量不受影响。
   */
  --font-sans: 'Cascadia Code', 'Cascadia Mono', ui-monospace, 'PingFang SC', 'Microsoft YaHei',
    'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  --font-mono: 'Cascadia Code', 'Cascadia Mono', 'JetBrains Mono', ui-monospace, 'SFMono-Regular',
    Consolas, 'Liberation Mono', monospace;

${renderTokens(defaultTheme, 'light')}
}

`
fs.writeFileSync(path.join(outDir, 'theme-default.css'), defaultRoot, 'utf8')
console.log('written:', path.relative(repo, path.join(outDir, 'theme-default.css')))

for (const t of THEMES) {
  if (ids.has(t.id)) throw new Error(`主题 id 重复: ${t.id}`)
  ids.add(t.id)

  const css = template
    .split('@@ID@@')
    .join(t.id)
    .replace('@@HEADER@@', () => renderHeader(t))
    .replace('@@LIGHT@@', () => renderTokens(t, 'light'))
    .replace('@@DARK@@', () => renderTokens(t, 'dark'))
    .replace('@@ENHANCE@@', () => renderEnhance(t).trim())

  const left = css.match(/@@[A-Z_]+@@/g)
  if (left) throw new Error(`${t.id}: 模板还有未替换的占位符 ${[...new Set(left)].join(', ')}`)

  const out = path.join(outDir, `theme-${t.id}.css`)
  fs.writeFileSync(out, css, 'utf8')
  console.log('written:', path.relative(repo, out), '(' + Math.round(css.length / 1024) + ' KB)')
}

// 主题清单: 前端下拉菜单与类型都用它
const registry = `/**
 * 主题清单 —— 由 src/styles/themes/_source/generate-themes.mjs 生成, 请勿手改。
 * 改主题请改 _source/tokens.mjs 后运行 npm run themes:generate。
 */

export type ThemeId =
${THEMES.map((t) => `  | '${t.id}'`).join('\n')}

export interface ThemeOption {
  id: ThemeId
  name: string
  en: string
  desc: string
  /** 预览用的两三个代表色, 供下拉菜单左侧色点显示 */
  swatch: string[]
}

export const DEFAULT_THEME: ThemeId = '${THEMES[0].id}'

export const THEME_OPTIONS: ThemeOption[] = [
${THEMES.map(
  (t) =>
    `  {\n    id: '${t.id}',\n    name: '${t.name}',\n    en: '${t.en}',\n    desc: '${t.desc}',\n    swatch: ['${t.light.primary}', '${t.light.gradTo}', '${t.dark.primary}'],\n  },`
).join('\n')}
]

export const THEME_IDS = THEME_OPTIONS.map((t) => t.id)
`
fs.writeFileSync(path.join(outDir, 'registry.ts'), registry, 'utf8')
console.log('written:', path.relative(repo, path.join(outDir, 'registry.ts')))
console.log(
  `\n共 ${THEMES.length} 套主题, 默认: ${defaultTheme.name} (${defaultTheme.id}), 增强层族: soft / hard / editorial / minimal`
)
console.log('提示: 后端首屏读取的是 theme-default.css, 它必须与 registry.ts 的 DEFAULT_THEME 一致')
