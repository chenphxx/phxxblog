/**
 * 主题自检:
 *   1. tokens.mjs 里每套主题的令牌是否齐全
 *   2. 生成出来的 theme-*.css 是否与 tokens.mjs 一致(有没有忘记重新生成)
 *   3. theme-default.css 是否等于默认主题、且只有它写了颜色级裸 :root
 *   4. 深浅两种模式下的关键配色是否满足 WCAG AA(4.5:1)
 *   5. 用渐变装饰的族, 渐变两端是否肉眼可辨
 *   6. 主题之间主色是否过于接近(仅警告)
 *
 * 用法: npm run themes:audit
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { THEMES, COLOR_KEYS } from './tokens.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
// 产物就在 _source 的上一级
const themeDir = path.resolve(here, '..')
const repo = path.resolve(here, '../../../..')

let fail = 0

/* ---------- WCAG 对比度 ---------- */
function relLum(hex) {
  const m = hex.replace('#', '')
  const full = m.length === 3 ? m.split('').map((c) => c + c).join('') : m
  const ch = [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16) / 255)
  const lin = ch.map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)))
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
}
function contrast(a, b) {
  const l1 = relLum(a)
  const l2 = relLum(b)
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
}
/** 两个颜色的 RGB 欧氏距离, 用来判断是否肉眼可辨(与亮度无关) */
function rgbDistance(a, b) {
  const toRgb = (h) => [0, 2, 4].map((i) => parseInt(h.replace('#', '').slice(i, i + 2), 16))
  const x = toRgb(a)
  const y = toRgb(b)
  return Math.sqrt(x.reduce((s, v, i) => s + (v - y[i]) ** 2, 0))
}

/* ---------- 1) 令牌齐全 ---------- */
console.log('=== 1. 令牌齐全性 ===')
for (const t of THEMES) {
  for (const mode of ['light', 'dark']) {
    const missing = COLOR_KEYS.filter((k) => !t[mode][k])
    if (missing.length) {
      fail++
      console.log(`  FAIL ${t.id}.${mode} 缺: ${missing.join(', ')}`)
    }
    // 颜色格式
    const badHex = COLOR_KEYS.filter((k) => {
      const v = t[mode][k]
      return v && !/^#[0-9a-fA-F]{3,8}$/.test(v) && !/^rgba?\(/.test(v)
    })
    if (badHex.length) {
      fail++
      console.log(`  FAIL ${t.id}.${mode} 颜色格式异常: ${badHex.map((k) => k + '=' + t[mode][k]).join(', ')}`)
    }
  }
}
if (fail === 0) console.log(`  ok   ${THEMES.length} 套 × 2 模式 = ${THEMES.length * 2} 组令牌全部齐全`)

/* ---------- 2) 生成文件与数据一致 ---------- */
console.log('\n=== 2. 生成文件与 tokens.mjs 一致性 ===')
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

  // 抽查两种模式的关键令牌值是否写进去了
  for (const mode of ['light', 'dark']) {
    for (const key of ['primary', 'bg', 'text']) {
      if (!css.includes(t[mode][key])) problems.push(`${mode}.${key}=${t[mode][key]} 未出现`)
    }
  }
  if (!css.includes(`html[data-theme='${t.id}'].dark {`)) problems.push('深色选择器缺失')
  if (!css.includes(`html[data-theme='${t.id}'] {`)) problems.push('浅色选择器缺失')
  if (!css.includes(`--radius: ${t.radius};`)) problems.push('圆角未写入')

  if (problems.length) {
    fail++
    console.log(`  FAIL ${t.id}: ${problems.join(' | ')}`)
  }
}
if (fail === 0) console.log(`  ok   ${THEMES.length} 个生成文件与数据一致`)

/*
 * theme-default.css 必须等于 THEMES[0] 的浅色令牌:
 * 它承担「新访客第一次打开」的配色, 与 registry.ts 的 DEFAULT_THEME 是一对。
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
    for (const key of ['primary', 'bg', 'text', 'link', 'onPrimary']) {
      if (!css.includes(first.light[key])) problems.push(`默认主题浅色 ${key}=${first.light[key]} 未出现`)
    }
    if (!/^:root \{/m.test(css)) problems.push('缺少裸 :root 块')
    // 其余主题不应再定义颜色令牌级的裸 :root, 否则默认主题会被后加载的覆盖。
    // 每个主题文件都有一个只放字体/尺寸的共享 :root 块, 那是允许的。
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
console.log(
  '  主题'.padEnd(20) + '模式   链接   主按钮  正文   次要  hover主色  渐变两端(RGB距离)'
)
for (const t of THEMES) {
  for (const mode of ['light', 'dark']) {
    const c = t[mode]
    // 文字类: 必须达到 AA 4.5
    const textChecks = {
      链接: contrast(c.link, c.cardBg),
      主按钮: contrast(c.onPrimary, c.primary),
      正文: contrast(c.text, c.cardBg),
      次要: contrast(c.muted, c.cardBg),
    }
    // 图形类: 悬停强调色属于 UI 组件边界, 按 AA 图形对象 3.0 要求。
    // 渐变色带是纯装饰元素(站点头部/终端卡片顶部的 1~2px 光带), WCAG 不对装饰设对比度门槛,
    // 也不该用亮度对比度衡量 —— 何况渐变两端刻意同亮度不同色相。
    // 这里只校验「两端有可见的色彩差异」, 避免渐变退化成一条纯色。
    const gfxChecks = {
      'hover主色': contrast(c.primaryStrong, c.cardBg),
    }
    const gradVisible = rgbDistance(c.gradFrom, c.gradTo)
    /*
     * 渐变是否退化成纯色, 只对「用渐变装饰」的族有意义:
     * soft / editorial 用渐变画文章卡左侧色条, hard 用纯色, 所以都不校验。
     * minimal(VitePress/Teek 风格)本身不用渐变色带, 同样跳过。
     */
    const useGradient = t.family === 'soft' || t.family === 'editorial'
    const badGrad = useGradient && gradVisible < 40
    const badText = Object.entries(textChecks).filter(([, v]) => v < 4.5)
    const badGfx = Object.entries(gfxChecks).filter(([, v]) => v < 3)
    if (badText.length || badGfx.length || badGrad) fail++

    const cells = [
      ...Object.values(textChecks).map((v) => v.toFixed(2).padStart(6)),
      contrast(c.primaryStrong, c.cardBg).toFixed(2).padStart(9),
      (useGradient ? gradVisible.toFixed(0) : '—').padStart(9),
    ].join(' ')

    console.log(
      '  ' +
        (badText.length || badGfx.length || badGrad ? 'FAIL ' : 'ok   ') +
        (t.id + ' ' + t.name).padEnd(16) +
        (mode === 'light' ? '浅色' : '深色') +
        cells
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
function toRgb(h) {
  const m = h.replace('#', '')
  return [0, 2, 4].map((i) => parseInt(m.slice(i, i + 2), 16))
}
let tooClose = 0
for (let i = 0; i < THEMES.length; i++) {
  for (let j = i + 1; j < THEMES.length; j++) {
    const a = toRgb(THEMES[i].light.primary)
    const b = toRgb(THEMES[j].light.primary)
    const d = Math.sqrt(a.reduce((s, v, k) => s + (v - b[k]) ** 2, 0))
    if (d < 28) {
      tooClose++
      console.log(`  WARN ${THEMES[i].name} 与 ${THEMES[j].name} 的浅色主色很接近 (距离 ${d.toFixed(0)})`)
    }
  }
}
if (tooClose === 0) console.log('  ok   任意两套主题的浅色主色都有明显区分')

console.log(fail === 0 ? '\nALL OK' : `\nFAILURES: ${fail}`)
process.exit(fail === 0 ? 0 : 1)
