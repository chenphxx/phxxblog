/**
 * 由同目录的 tokens.mjs 生成前端主题 CSS
 *
 * 生成物分成两类, 这是"按视觉语言统一"的关键:
 *   1. themes/base.css         结构令牌(间距/圆角/阴影/动效/字体) - 全站只有这一份, 与主题无关
 *   2. themes/theme-<id>.css   颜色令牌 - 每套主题只差品牌色与背景色
 *   (另有 theme-default.css 承载"新访客未选主题"时的裸 :root 浅色令牌)
 *
 * 改配色请改 tokens.mjs, 改圆角/间距/阴影请改 derive.mjs 的 STRUCTURE_TOKENS,
 * 两者都由本脚本输出, 不要手改生成物
 *
 * 目录位置: frontend/src/styles/themes/_source/
 * 输出位置: 上一级目录(frontend/src/styles/themes/)
 *
 * 用法: npm run themes:generate
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { THEMES } from './tokens.mjs'
import {
  COLOR_VARS,
  DARK_SHADOW_TOKENS,
  FONT_MONO,
  FONT_SANS,
  STRUCTURE_TOKENS,
  deriveMode,
  elementScale,
} from './derive.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
// _source 的上一级就是主题产物目录; 再往上是 frontend/
const outDir = path.resolve(here, '..')
const repo = path.resolve(here, '../../../..')

const REL_SOURCE = 'src/styles/themes/_source/generate-themes.mjs'

/** @brief 生成文件头部注释 */
function header(title, extra) {
  return `/* ============================================================
 * ${title}
 * ${extra}
 * ------------------------------------------------------------
 * 本文件由 ${REL_SOURCE} 生成, 请勿手改
 * 改配色请改 _source/tokens.mjs, 改结构令牌请改 _source/derive.mjs, 然后运行:
 *   npm run themes:generate
 * ============================================================ */`
}

/** @brief 把令牌表渲染成缩进过的 CSS 声明行 */
function declarations(entries) {
  return entries.map(([name, value]) => `  ${name}: ${value};`).join('\n')
}

/**
 * @brief 渲染一套主题 + 一种模式的颜色令牌块
 *
 * @param {object} theme 主题输入
 * @param {'light'|'dark'} mode 模式
 * @return {string} 颜色令牌声明行
 */
function renderColors(theme, mode) {
  const tokens = deriveMode(theme, mode)
  const scale = elementScale(tokens.primary)
  const lines = declarations(COLOR_VARS.map(([key, name]) => [name, tokens[key]]))
  const el = declarations([
    ['--el-color-primary', tokens.primary],
    ['--el-color-primary-light-3', scale.light3],
    ['--el-color-primary-light-5', scale.light5],
    ['--el-color-primary-light-7', scale.light7],
    ['--el-color-primary-light-8', scale.light8],
    ['--el-color-primary-light-9', scale.light9],
    ['--el-color-primary-dark-2', scale.dark2],
  ])
  return `${lines}\n\n  /* Element Plus 主色色阶由品牌色推导, 组件与主题保持一致 */\n${el}`
}

fs.mkdirSync(outDir, { recursive: true })

/* ---------------------------------------------------------------
 * 1) 结构令牌与字体: 所有主题共用, 只写一次
 * ------------------------------------------------------------- */
const baseCss = `${header('共享结构令牌(间距, 圆角, 阴影, 动效)与字体', '主题只负责颜色, 结构令牌在这里统一')}

:root {
  /* 字体: UI 文字用系统无衬线, 等宽字体只留给代码块, 终端与数字指标 */
  --font-sans: ${FONT_SANS};
  --font-mono: ${FONT_MONO};

${declarations(STRUCTURE_TOKENS)}

  /* Element Plus 的圆角跟随结构令牌, 组件外观与页面保持一致 */
  --el-border-radius-base: var(--radius-control);
  --el-border-radius-small: calc(var(--radius-control) - 2px);
  --el-border-radius-round: var(--radius-pill);
}

/* 深色下阴影需要更重才看得出来 */
html.dark {
${declarations(DARK_SHADOW_TOKENS)}
}
`
fs.writeFileSync(path.join(outDir, 'base.css'), baseCss, 'utf8')
console.log('written:', path.relative(repo, path.join(outDir, 'base.css')))

/* ---------------------------------------------------------------
 * 2) 默认主题的裸 :root
 *
 * 未选过主题的新访客拿不到任何 html[data-theme=...] 匹配, 靠的就是这份浅色令牌
 * 因此只有它允许写颜色级裸 :root, 其余主题一律只写 html[data-theme='<id>']
 * ------------------------------------------------------------- */
const defaultTheme = THEMES[0]
const defaultCss = `${header(
  `默认主题: ${defaultTheme.name} (${defaultTheme.en})`,
  `新访客(未在 localStorage 里存过主题)看到的就是这一套\n * 想换默认主题: 把 tokens.mjs 里想用的那套挪到 THEMES 数组第一位`,
)}

:root {
${renderColors(defaultTheme, 'light')}
}
`
fs.writeFileSync(path.join(outDir, 'theme-default.css'), defaultCss, 'utf8')
console.log('written:', path.relative(repo, path.join(outDir, 'theme-default.css')))

/* ---------------------------------------------------------------
 * 3) 9 套主题的颜色令牌
 * ------------------------------------------------------------- */
const ids = new Set()

for (const t of THEMES) {
  if (ids.has(t.id)) throw new Error(`主题 id 重复: ${t.id}`)
  ids.add(t.id)

  const css = `${header(`主题: ${t.name} (${t.en})`, `${t.desc}\n * 切换方式: html[data-theme='${t.id}'] (见 stores/theme.ts), 深色再加 .dark`)}

html[data-theme='${t.id}'] {
${renderColors(t, 'light')}
}

html[data-theme='${t.id}'].dark {
${renderColors(t, 'dark')}
}
`
  const out = path.join(outDir, `theme-${t.id}.css`)
  fs.writeFileSync(out, css, 'utf8')
  console.log('written:', path.relative(repo, out), '(' + Math.round(css.length / 1024) + ' KB)')
}

/* ---------------------------------------------------------------
 * 4) 主题清单: 前端下拉菜单与类型都用它
 * ------------------------------------------------------------- */
const registry = `/**
 * 主题清单 - 由 ${REL_SOURCE} 生成, 请勿手改
 * 改主题请改 _source/tokens.mjs 后运行 npm run themes:generate
 */

export type ThemeId =
${THEMES.map((t) => `  | '${t.id}'`).join('\n')}

export interface ThemeOption {
  id: ThemeId
  name: string
  en: string
  desc: string
  /** 预览用的两个代表色, 供下拉菜单左侧色点显示(品牌色 + 画布色) */
  swatch: string[]
}

export const DEFAULT_THEME: ThemeId = '${THEMES[0].id}'

export const THEME_OPTIONS: ThemeOption[] = [
${THEMES.map(
  (t) =>
    `  {\n    id: '${t.id}',\n    name: '${t.name}',\n    en: '${t.en}',\n    desc: '${t.desc}',\n    swatch: ['${t.light.primary}', '${t.light.bg}'],\n  },`,
).join('\n')}
]

export const THEME_IDS = THEME_OPTIONS.map((t) => t.id)
`
fs.writeFileSync(path.join(outDir, 'registry.ts'), registry, 'utf8')
console.log('written:', path.relative(repo, path.join(outDir, 'registry.ts')))

console.log(
  `\n共 ${THEMES.length} 套主题, 默认: ${defaultTheme.name} (${defaultTheme.id}); 结构令牌集中在 themes/base.css`,
)
