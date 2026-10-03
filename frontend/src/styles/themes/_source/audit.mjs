/**
 * 主题自检
 *
 *   1. tokens.mjs 的输入是否完整(每套主题两模式都要有 primary 与 bg), 推导出的颜色令牌是否齐全
 *   2. 生成出来的 theme-*.css / base.css 是否与数据一致(有没有忘记重新生成)
 *   3. theme-default.css 是否等于默认主题, 且只有它写了颜色级裸 :root
 *   4. 深浅两种模式下的关键配色是否满足 WCAG AA(4.5:1), 装饰渐变两端是否肉眼可辨
 *   5. 结构令牌(间距/圆角/字体)是否只出现在 base.css 一处, 主题文件里不再带头尾
 *   6. 主题之间主色是否过于接近(仅警告)
 *
 * 用法: npm run themes:audit
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { THEMES } from './tokens.mjs'
import { COLOR_KEYS, STRUCTURE_TOKENS, contrast, deriveMode, relLum, rgbDistance, toRgb } from './derive.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
// 产物就在 _source 的上一级
const themeDir = path.resolve(here, '..')
const repo = path.resolve(here, '../../../..')

const isHex = (v) => /^#[0-9a-fA-F]{3,8}$/.test(v)

let fail = 0

/* ---------- 1) 输入与推导后的令牌 ---------- */
console.log('=== 1. 令牌齐全性 ===')
const derived = new Map()
for (const t of THEMES) {
  for (const mode of ['light', 'dark']) {
    const input = t[mode]
    if (!input || !input.primary || !input.bg) {
      fail++
      console.log(`  FAIL ${t.id}.${mode} 缺少 primary / bg`)
      continue
    }
    if (!isHex(input.primary) || !isHex(input.bg)) {
      fail++
      console.log(`  FAIL ${t.id}.${mode} 品牌色或画布色不是十六进制: ${input.primary} / ${input.bg}`)
      continue
    }

    const tokens = deriveMode(t, mode)
    derived.set(`${t.id}.${mode}`, tokens)

    const missing = COLOR_KEYS.filter((k) => !tokens[k])
    if (missing.length) {
      fail++
      console.log(`  FAIL ${t.id}.${mode} 推导后缺: ${missing.join(', ')}`)
    }
    const badHex = COLOR_KEYS.filter((k) => tokens[k] && !isHex(tokens[k]))
    if (badHex.length) {
      fail++
      console.log(`  FAIL ${t.id}.${mode} 颜色格式异常: ${badHex.map((k) => k + '=' + tokens[k]).join(', ')}`)
    }
  }
}
if (fail === 0) {
  console.log(`  ok   ${THEMES.length} 套 × 2 模式 = ${THEMES.length * 2} 组令牌全部齐全`)
}

/* ---------- 2) 生成文件与数据一致 ---------- */
console.log('\n=== 2. 生成文件与 tokens.mjs 一致性 ===')

/** 结构令牌不该出现在主题文件里(它们只在 base.css) */
const STRUCTURE_PROBES = ['--font-sans', '--radius-panel', '--radius-card', '--space-4', '--shadow-panel']

for (const t of THEMES) {
  const file = path.join(themeDir, `theme-${t.id}.css`)
  if (!fs.existsSync(file)) {
    fail++
    console.log(`  FAIL ${t.id}: 缺少 ${path.relative(repo, file)}, 请运行 generate-themes.mjs`)
    continue
  }
  const css = fs.readFileSync(file, 'utf8')
  const problems = []
  const leftovers = css.match(/@@[A-Z_]+@@/g)
  if (leftovers) problems.push('未替换占位符 ' + [...new Set(leftovers)].join(','))

  for (const mode of ['light', 'dark']) {
    const tokens = derived.get(`${t.id}.${mode}`)
    for (const key of ['primary', 'bg', 'text', 'link', 'onPrimary']) {
      if (tokens && !css.includes(tokens[key])) problems.push(`${mode}.${key}=${tokens[key]} 未出现`)
    }
  }
  if (!css.includes(`html[data-theme='${t.id}'].dark {`)) problems.push('深色选择器缺失')
  if (!css.includes(`html[data-theme='${t.id}'] {`)) problems.push('浅色选择器缺失')
  const leaked = STRUCTURE_PROBES.filter((name) => css.includes(name))
  if (leaked.length) problems.push('主题文件里出现了结构令牌: ' + leaked.join(', '))

  if (problems.length) {
    fail++
    console.log(`  FAIL ${t.id}: ${problems.join(' | ')}`)
  }
}
if (fail === 0) console.log(`  ok   ${THEMES.length} 个生成文件与数据一致`)

/* base.css: 结构令牌与字体只在这里出现 */
{
  const file = path.join(themeDir, 'base.css')
  const problems = []
  if (!fs.existsSync(file)) {
    problems.push('缺少 base.css')
  } else {
    const css = fs.readFileSync(file, 'utf8')
    const missing = STRUCTURE_TOKENS.filter(([name]) => !css.includes(`${name}:`)).map(([name]) => name)
    if (missing.length) problems.push('缺结构令牌: ' + missing.join(', '))
    if (!css.includes('--font-sans:') || !css.includes('--font-mono:')) problems.push('缺字体令牌')
    for (const mode of ['light', 'dark']) {
      const tokens = derived.get(`${THEMES[0].id}.${mode}`)
      if (css.includes(tokens.primary)) problems.push('base.css 里不应出现主题颜色令牌')
    }
  }
  if (problems.length) {
    fail++
    console.log('  FAIL base.css: ' + problems.join(' | '))
  } else {
    console.log('  ok   base.css 结构令牌齐全, 且不含主题颜色')
  }
}

/*
 * theme-default.css 必须等于 THEMES[0] 的浅色令牌:
 * 它承担"新访客第一次打开"的配色, 与 registry.ts 的 DEFAULT_THEME 是一对
 */
{
  const file = path.join(themeDir, 'theme-default.css')
  const registry = fs.readFileSync(path.join(themeDir, 'registry.ts'), 'utf8')
  const problems = []
  if (!fs.existsSync(file)) {
    problems.push('缺少 theme-default.css')
  } else {
    const css = fs.readFileSync(file, 'utf8')
    const first = THEMES[0]
    const tokens = derived.get(`${first.id}.light`)
    for (const key of ['primary', 'bg', 'text', 'link', 'onPrimary']) {
      if (!css.includes(tokens[key])) problems.push(`默认主题浅色 ${key}=${tokens[key]} 未出现`)
    }
    if (!/^:root \{/m.test(css)) problems.push('缺少裸 :root 块')
    /* 其余主题文件不应再定义颜色令牌级的裸 :root, 否则默认主题会被后加载的覆盖 */
    const withBareRoot = THEMES.filter((t) => {
      const f = path.join(themeDir, `theme-${t.id}.css`)
      if (!fs.existsSync(f)) return false
      const content = fs.readFileSync(f, 'utf8')
      const blocks = [...content.matchAll(/^:root \{([\s\S]*?)^\}/gm)]
      return blocks.some((b) => /--(bg|card-bg|text|primary)\s*:/.test(b[1]))
    })
    if (withBareRoot.length) {
      problems.push('这些主题文件里出现了颜色级裸 :root, 会覆盖默认主题: ' + withBareRoot.map((t) => t.id).join(','))
    }
    const regDefault = (registry.match(/DEFAULT_THEME: ThemeId = '([^']+)'/) || [])[1]
    if (regDefault !== first.id) problems.push(`registry 默认主题 ${regDefault} 与 theme-default 的 ${first.id} 不一致`)
  }
  if (problems.length) {
    fail++
    console.log('  FAIL theme-default.css: ' + problems.join(' | '))
  } else {
    console.log(`  ok   theme-default.css 与默认主题 ${THEMES[0].name} (${THEMES[0].id}) 一致`)
  }
}

/* ---------- 3) 对比度 ---------- */
console.log('\n=== 3. 配色对比度 (文字类需 >= 4.5, 图形/渐变需 >= 3.0) ===')
console.log('  主题'.padEnd(20) + '模式   链接   主按钮  正文   次要  hover主色  渐变两端(RGB距离)')
for (const t of THEMES) {
  for (const mode of ['light', 'dark']) {
    const c = derived.get(`${t.id}.${mode}`)
    if (!c) continue

    /* 文字类: 必须达到 AA 4.5 */
    const textChecks = {
      链接: contrast(c.link, c.cardBg),
      主按钮: contrast(c.onPrimary, c.primary),
      正文: contrast(c.text, c.cardBg),
      次要: contrast(c.muted, c.cardBg),
    }
    /* 图形类: 悬停强调色是 UI 组件边界, 按 AA 图形对象 3.0 要求 */
    const gfxChecks = {
      hover主色: contrast(c.primaryStrong, c.cardBg),
    }
    /*
     * 装饰渐变只用在品牌标记这类小面积图形上, WCAG 不对装饰设对比度门槛,
     * 这里只校验"两端有可见的色彩差异", 避免渐变退化成一条纯色
     */
    const gradVisible = rgbDistance(c.gradFrom, c.gradTo)
    const badText = Object.entries(textChecks).filter(([, v]) => v < 4.5)
    const badGfx = Object.entries(gfxChecks).filter(([, v]) => v < 3)
    const badGrad = gradVisible < 40
    if (badText.length || badGfx.length || badGrad) fail++

    const cells = [
      ...Object.values(textChecks).map((v) => v.toFixed(2).padStart(6)),
      contrast(c.primaryStrong, c.cardBg).toFixed(2).padStart(9),
      gradVisible.toFixed(0).padStart(9),
    ].join(' ')

    console.log(
      '  ' +
        (badText.length || badGfx.length || badGrad ? 'FAIL ' : 'ok   ') +
        (t.id + ' ' + t.name).padEnd(16) +
        (mode === 'light' ? '浅色' : '深色') +
        cells,
    )
    if (badText.length) {
      console.log('         -> 文字对比度不足: ' + badText.map(([k, v]) => `${k} ${v.toFixed(2)}:1`).join('; '))
    }
    if (badGfx.length) {
      console.log('         -> 图形对比度不足: ' + badGfx.map(([k, v]) => `${k} ${v.toFixed(2)}:1`).join('; '))
    }
    if (badGrad) {
      console.log(`         -> 渐变两端几乎同色(RGB 距离 ${gradVisible.toFixed(0)}), 看不出渐变`)
    }
  }
}

/* ---------- 4) 主题间重复度(避免两套看起来一样) ---------- */
console.log('\n=== 4. 主题可辨识度(浅色主色两两距离) ===')
let tooClose = 0
for (let i = 0; i < THEMES.length; i += 1) {
  for (let j = i + 1; j < THEMES.length; j += 1) {
    const a = toRgb(THEMES[i].light.primary)
    const b = toRgb(THEMES[j].light.primary)
    const d = Math.sqrt(a.reduce((s, v, k) => s + (v - b[k]) ** 2, 0))
    if (d < 28) {
      tooClose += 1
      console.log(`  WARN ${THEMES[i].name} 与 ${THEMES[j].name} 的浅色主色很接近 (距离 ${d.toFixed(0)})`)
    }
  }
}
if (tooClose === 0) console.log('  ok   任意两套主题的浅色主色都有明显区分')

/* ---------- 5) 明暗反转是否合理(深色主色通常更亮) ---------- */
console.log('\n=== 5. 深浅两套品牌色 ===')
let flat = 0
for (const t of THEMES) {
  const lightLum = relLum(t.light.primary)
  const darkLum = relLum(t.dark.primary)
  if (darkLum <= lightLum) {
    flat += 1
    console.log(`  WARN ${t.name} 的深色品牌色不比浅色更亮, 深色模式下按钮可能偏闷`)
  }
}
if (flat === 0) console.log('  ok   每套主题的深色品牌色都更亮, 深色模式下仍能辨认')

console.log(fail === 0 ? '\nALL OK' : `\nFAILURES: ${fail}`)
process.exit(fail === 0 ? 0 : 1)
