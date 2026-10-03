/**
 * 生成主题预览页(每套 × 深/浅 + 总览页)
 *
 * 为什么要有这个脚本:
 *   预览必须与真正引入项目的样式完全一致, 否则没有参考价值
 *   所以这里不复制样式, 而是把真实的 base.css / theme-<id>.css / theme.css
 *   原样注入到 demo 页面里, 预览效果 = 实际效果
 *
 * 目录位置: frontend/src/styles/themes/_source/
 * 输出位置: frontend/src/styles/themes/_preview/  (纯产物, 已 gitignore, 可随时重建)
 *
 * 用法: npm run themes:preview
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { THEMES as TOKENS } from './tokens.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const themeDir = path.resolve(here, '..')
const stylesDir = path.resolve(themeDir, '..')
const outDir = path.join(themeDir, '_preview')
const repo = path.resolve(here, '../../../..')

/** 主题清单来自 tokens.mjs, 与前端 registry.ts 同源 */
const THEMES = TOKENS.map((t) => ({
  key: t.id,
  id: t.id,
  file: `theme-${t.id}.css`,
  name: t.name,
  en: t.en,
  desc: t.desc,
  tag: t.desc,
  swatch: [t.light.primary, t.light.bg, t.dark.primary],
}))

/**
 * @brief 抽出一个 CSS 文件里的令牌块内容
 *
 * @param {string} css 样式文本
 * @param {string} selector 选择器(如 ":root" 或 "html[data-theme='mist'].dark")
 * @return {string} 大括号内的声明, 找不到时返回空串
 */
function blockOf(css, selector) {
  const start = css.indexOf(`${selector} {`)
  if (start < 0) return ''
  const open = css.indexOf('{', start)
  const end = css.indexOf('\n}', open)
  return css.slice(open + 1, end).trim()
}

/** @brief 缩进整段 CSS */
function indent(text, pad) {
  return text
    .split('\n')
    .map((line) => (line.trim() ? pad + line : line))
    .join('\n')
}

const base = fs.readFileSync(path.join(themeDir, 'base.css'), 'utf8')
const defaultRoot = fs.readFileSync(path.join(themeDir, 'theme-default.css'), 'utf8')
/** 真实组件样式(面板, 列表行, 正文, 终端, 按钮...) - 预览直接复用 */
const themeCss = fs.readFileSync(path.join(stylesDir, 'theme.css'), 'utf8')
/** 布局层在阶段二出现, 存在就注入, 预览与线上保持一致 */
const layoutPath = path.join(stylesDir, 'layout.css')
const layoutCss = fs.existsSync(layoutPath) ? fs.readFileSync(layoutPath, 'utf8') : ''

const PAGE = (opts) => `<!DOCTYPE html>
<html lang="zh-CN" data-theme="${opts.id}"${opts.mode === 'dark' ? ' class="dark"' : ''}>
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="color-scheme" content="light dark" />
<title>${opts.name} · ${opts.mode === 'dark' ? '深色' : '浅色'} · phxxblog</title>
<style>
/* ============================================================
 * 以下样式原样来自 frontend/src/styles/:
 *   themes/base.css         结构令牌与字体
 *   themes/theme-default.css 默认主题的裸 :root 颜色令牌
 *   themes/${opts.file}      当前主题的浅色/深色令牌
 *   theme.css               组件与结构样式${layoutCss ? '\n *   layout.css              应用外壳(侧栏/画布)' : ''}
 * 改动主题请改 _source/tokens.mjs 后:
 *   npm run themes:generate && npm run themes:preview
 * ============================================================ */

/* ---------- 共享结构令牌(源文件: themes/base.css) ---------- */
:root {
${indent(blockOf(base, ':root'), '  ')}
}

html.dark {
${indent(blockOf(base, 'html.dark'), '  ')}
}

/* ---------- 默认主题的裸 :root 颜色令牌(源文件: themes/theme-default.css) ---------- */
:root {
${indent(blockOf(defaultRoot, ':root'), '  ')}
}

/* ---------- 当前主题的颜色令牌(源文件: themes/${opts.file}) ---------- */
html[data-theme='${opts.id}'] {
${indent(opts.light, '  ')}
}

html[data-theme='${opts.id}'].dark {
${indent(opts.dark, '  ')}
}

/* ---------- 真实组件样式(源文件: theme.css) ---------- */
${themeCss}

${layoutCss ? '/* ---------- 应用外壳(源文件: layout.css) ---------- */\n' + layoutCss + '\n' : ''}

/* ============================================================
 * 预览脚手架: 只用于把组件摆成首页/详情页的样子, 不属于项目样式
 * ============================================================ */
.preview-banner {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between;
  padding: 10px 0 0; font-size: 12px; color: var(--muted);
}
.preview-banner b { color: var(--text); }
.preview-stack { display: flex; flex-direction: column; gap: 24px; }
.preview-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 24px; }
.preview-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.preview-grid { display: grid; grid-template-columns: minmax(0, 1fr) 260px; gap: 24px; align-items: start; }
.preview-title { margin: 0; font-size: 19px; font-weight: 600; letter-spacing: -0.015em; }
.preview-title a { color: var(--text); }
.preview-summary { margin: 8px 0 12px; color: var(--muted); font-size: 14px; line-height: 1.7; }
.preview-meta { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; color: var(--muted); font-size: 12.5px; }
.preview-btn {
  font-family: var(--font-sans); font-size: 14px; padding: 8px 18px;
  border-radius: var(--radius-control); border: 1px solid var(--border-strong);
  background: var(--card-bg); color: var(--text); cursor: pointer;
}
.preview-btn-primary { background: var(--primary); border-color: var(--primary); color: var(--on-primary); }
.preview-pager { display: flex; gap: 6px; }
.preview-pager span {
  min-width: 32px; height: 32px; display: grid; place-items: center;
  border: 1px solid var(--border); border-radius: var(--radius-control);
  font-size: 13px; color: var(--muted);
}
.preview-pager span.is-active { background: var(--primary); border-color: var(--primary); color: var(--on-primary); }
.preview-cells { display: flex; gap: 3px; flex-wrap: wrap; max-width: 100%; }
.preview-cells i { width: 11px; height: 11px; border-radius: 3px; display: block; }
/* 终端卡片的真实外观在 HomeSessionCard.vue 的 scoped 样式里, 预览这里补一份等价的最小实现 */
.term-card { background: var(--term-bg); border: 1px solid var(--term-border); border-radius: var(--radius-card); overflow: hidden; }
.term-head { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-bottom: 1px solid var(--term-border); }
.term-dot { width: 11px; height: 11px; border-radius: 50%; }
.term-dot-red { background: #f87171; } .term-dot-amber { background: #fbbf24; } .term-dot-green { background: #34d399; }
.term-title { flex: 1; text-align: center; font-family: var(--font-mono); font-size: 12px; color: var(--term-dim); }
.term-body { padding: 16px 20px 18px; font-family: var(--font-mono); font-size: 13px; line-height: 1.75; }
.term-line { margin: 8px 0 0; color: var(--term-prompt); }
.term-prompt { color: var(--term-accent); margin-right: 8px; }
.term-out { margin: 0 0 2px 20px; color: var(--term-text); }
@media (max-width: 900px) {
  .preview-grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<div class="page-container" style="max-width: 1200px">
  <div class="preview-banner">
    <span>主题 <b>${opts.name}</b> · ${opts.en} · ${opts.tag}</span>
    <span>
      当前 <b>${opts.mode === 'dark' ? '深色' : '浅色'}</b> ·
      <label style="cursor:pointer">切换
        <input type="checkbox" ${opts.mode === 'dark' ? 'checked' : ''}
          onchange="document.documentElement.classList.toggle('dark', this.checked)" />
      </label>
    </span>
  </div>

  <div class="page-head">
    <div>
      <p class="eyebrow" style="margin: 0 0 6px">pages — 预览</p>
      <h1 class="page-title">首页</h1>
    </div>
    <span class="muted">共 56 篇</span>
  </div>

  <div class="preview-stack">
    <section class="panel">
      <div class="preview-grid" style="align-items: center">
        <div>
          <h2 class="panel-title">phxxblog</h2>
          <p class="muted" style="margin: 8px 0 14px">写代码, 也写点别的 · Software Developer / Builder</p>
          <div class="preview-row">
            <span class="chip" style="background: color-mix(in srgb, var(--primary) 10%, transparent); border-color: color-mix(in srgb, var(--primary) 26%, transparent); color: color-mix(in srgb, var(--primary) 76%, var(--text))">GitHub</span>
            <span class="chip" style="background: color-mix(in srgb, var(--primary) 10%, transparent); border-color: color-mix(in srgb, var(--primary) 26%, transparent); color: color-mix(in srgb, var(--primary) 76%, var(--text))">Email</span>
            <span class="chip" style="background: color-mix(in srgb, var(--primary) 10%, transparent); border-color: color-mix(in srgb, var(--primary) 26%, transparent); color: color-mix(in srgb, var(--primary) 76%, var(--text))">RSS</span>
          </div>
        </div>
        <div class="preview-metrics">
          <div class="metric">
            <p class="metric-label">文章</p>
            <p class="metric-value">56</p>
          </div>
          <div class="metric">
            <p class="metric-label">分类</p>
            <p class="metric-value">8</p>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2 class="panel-title">最新文章</h2>
        <a href="#" style="font-size: 14px">查看全部 →</a>
      </div>
      <article class="list-row">
        <h3 class="preview-title"><a href="#">用 Vite 重构一个老项目的实战记录</a></h3>
        <p class="preview-summary">从 webpack 迁到 Vite 的完整过程: 踩过的坑、构建耗时变化, 以及那些不值得迁移的部分。</p>
        <div class="preview-meta">
          <span class="num">2026.09.28</span>
          <span class="chip" style="background: color-mix(in srgb, var(--primary) 10%, transparent); border-color: color-mix(in srgb, var(--primary) 26%, transparent); color: color-mix(in srgb, var(--primary) 76%, var(--text))">前端</span>
          <span class="num">8 min read</span>
        </div>
      </article>
      <article class="list-row">
        <h3 class="preview-title"><a href="#">FastAPI + Vue 的鉴权方案复盘</a></h3>
        <p class="preview-summary">JWT 存在哪里、刷新时机怎么定、401 之后如何优雅重试, 一次真实的踩坑记录。</p>
        <div class="preview-meta">
          <span class="num">2026.09.21</span>
          <span class="chip" style="background: color-mix(in srgb, var(--primary) 10%, transparent); border-color: color-mix(in srgb, var(--primary) 26%, transparent); color: color-mix(in srgb, var(--primary) 76%, var(--text))">后端</span>
          <span class="num">6 min read</span>
        </div>
      </article>
      <div style="display: flex; justify-content: center; padding-top: 20px">
        <div class="preview-pager"><span>1</span><span class="is-active">2</span><span>3</span><span>4</span></div>
      </div>
    </section>

    <div class="preview-grid">
      <section class="panel">
        <div class="panel-head">
          <h2 class="panel-title">文章发布记录</h2>
          <span class="muted num">2026</span>
        </div>
        <div class="preview-cells">
          ${opts.cells}
        </div>
      </section>
      <section class="term-card" style="margin: 0">
        <div class="term-head">
          <span class="term-dot term-dot-red"></span>
          <span class="term-dot term-dot-amber"></span>
          <span class="term-dot term-dot-green"></span>
          <span class="term-title">session — phxxblog</span>
        </div>
        <div class="term-body">
          <p class="term-line"><span class="term-prompt">$</span> whoami</p>
          <p class="term-out">phxxblog — 写代码, 也写点别的</p>
          <p class="term-line"><span class="term-prompt">$</span> ls posts | wc -l</p>
          <p class="term-out">56</p>
          <p class="term-line"><span class="term-prompt">$</span> say</p>
          <p class="term-out">保持热爱, 奔赴山海。</p>
        </div>
      </section>
    </div>

    <section class="panel">
      <h2 class="panel-title" style="margin-bottom: 16px">文章正文</h2>
      <div class="markdown-body">
        <h2>一次真实的刷新令牌踩坑</h2>
        <p>
          并发请求几乎必然同时 401, 而 refresh token 是一次性轮换的 - 并发刷新会让后到的那次拿到已失效的令牌,
          于是整页掉线。这里的做法是所有并发 401 共用同一个刷新 Promise, 并给重放过的请求打上标记。
        </p>
        <blockquote>只有"换令牌失败"才算掉线, 重放失败按普通错误处理。</blockquote>
        <pre><code class="hljs"><span class="hljs-keyword">const</span> refreshOnce = <span class="hljs-title function_">memoize</span>(refresh)</code></pre>
      </div>
      <div class="preview-row" style="margin-top: 20px">
        <button class="preview-btn preview-btn-primary">主要操作</button>
        <button class="preview-btn">次要操作</button>
      </div>
    </section>
  </div>
</div>
</body>
</html>
`

/** 生成 52 周 x 7 天的热力图占位 */
function cells() {
  const levels = [1, 2, 3, 4, 0, 2, 1, 3, 0, 1, 2, 2, 4, 1, 0, 3, 2, 1, 1, 0, 2, 3, 1, 4, 0, 2, 1, 3]
  let out = ''
  for (let i = 0; i < 52 * 7; i += 1) {
    const lv = levels[i % levels.length]
    out += `<i style="background: var(--cell-${lv})"></i>`
  }
  return out
}

fs.mkdirSync(outDir, { recursive: true })

for (const t of THEMES) {
  const css = fs.readFileSync(path.join(themeDir, t.file), 'utf8')
  const light = blockOf(css, `html[data-theme='${t.id}']`)
  const dark = blockOf(css, `html[data-theme='${t.id}'].dark`)

  for (const mode of ['light', 'dark']) {
    const out = path.join(outDir, `${t.id}-${mode}.html`)
    fs.writeFileSync(out, PAGE({ ...t, mode, light, dark, cells: cells() }), 'utf8')
    console.log('written:', path.relative(repo, out))
  }
}

/* ---------------------------------------------------------------
 * 总览页: 以 _gallery-template.html 为模板, 注入主题清单后输出 index.html
 * 模板只有一份, 每次重建都从模板生成, 因此可以直接覆盖输出, 不会累积漂移
 * ------------------------------------------------------------- */
const templatePath = path.join(here, '_gallery-template.html')
const outPath = path.join(outDir, 'index.html')
const template = fs.readFileSync(templatePath, 'utf8')
if (!template.includes('__THEMES__')) throw new Error('_gallery-template.html 里找不到 __THEMES__ 占位符')

fs.writeFileSync(outPath, template.replace('__THEMES__', JSON.stringify(THEMES, null, 2)), 'utf8')
console.log('written: ' + path.relative(repo, outPath) + ' (注入 ' + THEMES.length + ' 套主题)')

console.log('\n共 ' + THEMES.length + ' 套主题 × 2 模式 = ' + THEMES.length * 2 + ' 个预览页')
console.log('打开 ' + path.relative(repo, outPath) + ' 查看总览')
