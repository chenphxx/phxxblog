/**
 * 生成主题预览页(每套 × 深/浅 + 总览页)。
 *
 * 为什么要有这个脚本:
 *   预览必须与真正引入项目的 themes/*.css 完全一致, 否则没有参考价值。
 *   所以这里不在 HTML 里复制样式, 而是把主题 CSS 原样抽出、注入到 demo 脚手架中。
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
const outDir = path.join(themeDir, '_preview')
const repo = path.resolve(here, '../../../..')

/** 主题清单来自 tokens.mjs, 与前端 registry.ts 同源 */
const THEMES = TOKENS.map((t) => ({
  key: t.id,
  id: t.id,
  family: t.family,
  file: `theme-${t.id}.css`,
  name: t.name,
  en: t.en,
  desc: t.desc,
  tag: t.desc,
  swatch: [t.light.primary, t.light.gradTo, t.dark.primary, t.dark.bg],
}))

/** 抽出与模式无关的共享 :root 块 */
function sharedBlock(css) {
  const start = css.indexOf('\n:root {')
  if (start < 0) return ''
  const open = css.indexOf('{', start)
  const end = css.indexOf('\n}', open)
  return css.slice(open + 1, end).trim()
}

/**
 * 抽默认主题的裸 :root 块(theme-default.css)。
 * 预览页也要带上它, 否则预览与真实首屏的默认配色不一致。
 */
function defaultRootBlock() {
  const file = path.join(themeDir, 'theme-default.css')
  if (!fs.existsSync(file)) return ''
  const css = fs.readFileSync(file, 'utf8')
  const start = css.indexOf('\n:root {')
  if (start < 0) return ''
  const open = css.indexOf('{', start)
  const end = css.indexOf('\n}', open)
  return css.slice(open + 1, end).trim()
}

/** 抽浅色令牌块 —— 生成格式: html[data-theme='<id>'] { */
function lightBlock(css, id) {
  const start = css.indexOf(`html[data-theme='${id}'] {`)
  if (start < 0) throw new Error(`找不到浅色令牌块: ${id}`)
  const open = css.indexOf('{', start)
  const end = css.indexOf('\n}', open)
  return css.slice(open + 1, end).trim()
}

/** 抽深色令牌块 —— 生成格式: html[data-theme='<id>'].dark { */
function darkBlock(css, id) {
  const start = css.indexOf(`html[data-theme='${id}'].dark {`)
  if (start < 0) throw new Error(`找不到深色令牌块: ${id}`)
  const open = css.indexOf('{', start)
  const end = css.indexOf('\n}', open)
  return css.slice(open + 1, end).trim()
}

/** 只保留增强层(令牌块由上面的函数单独注入, 避免重复) */
function modernLayer(css) {
  const marker = css.indexOf('* 现代化增强层')
  const start = css.lastIndexOf('/* =', marker)
  let layer = css.slice(start)
  return layer.replace(/^[\s\S]*?\*\//, '').trim()
}

/** 缩进整段 CSS */
function indent(text, pad) {
  return text
    .split('\n')
    .map((l) => (l.trim() ? pad + l : l))
    .join('\n')
}

const PAGE = (opts) => `<!DOCTYPE html>
<html lang="zh-CN" data-theme="${opts.id}"${opts.mode === 'dark' ? ' class="dark"' : ''}>
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="color-scheme" content="light dark" />
<title>${opts.name} · ${opts.mode === 'dark' ? '深色' : '浅色'} · ${opts.site}</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
<style>
/* ============================================================
 * 以下令牌与增强层, 原样来自:
 *   frontend/src/styles/themes/${opts.file}
 * 改动主题请改 _source/tokens.mjs 后:
 *   npm run themes:generate && npm run themes:preview
 * ============================================================ */

/* ---------- 与模式无关的共享令牌 (源文件: 共享 :root) ---------- */
:root {
${indent(opts.shared, '  ')}
}

/* ---------- 默认主题的裸 :root 令牌(源文件: theme-default.css) ---------- */
/* 预览里 data-theme 一定被设成当前主题, 这份只是为了与真实首屏保持一致 */
${indent(opts.defaultRoot, '')}

/* ---------- 浅色令牌 (源文件: html[data-theme='${opts.id}']) ---------- */
:root,
html[data-theme='${opts.id}'] {
${indent(opts.light, '  ')}
}

/* ---------- 深色令牌 (源文件: html[data-theme='${opts.id}'].dark) ---------- */
html[data-theme='${opts.id}'].dark {
${indent(opts.dark, '  ')}
}

/* ---------- 增强层 (源文件增强层原样) ---------- */
${indent(opts.layer, '')}

/* ============================================================
 * 预览脚手架: 模拟项目真实组件结构 (SiteLayout / HomeView / PostCard)
 * 这些样式不在主题文件里, 只用于展示
 * ============================================================ */
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 15px;
  line-height: 1.7;
  transition: background-color .3s ease, color .3s ease;
}
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; text-underline-offset: 3px; }
.page-container { padding: 24px 20px 40px; }
.home-grid { display: grid; grid-template-columns: 260px 1fr; gap: 20px; align-items: start; }
.home-left { display: flex; flex-direction: column; gap: 20px; }
.home-main { min-width: 0; }
.muted { color: var(--muted); font-size: 13px; }
.eyebrow { font-family: var(--font-mono); font-size: 12px; color: var(--muted); margin: 0; }
.eyebrow::before { content: '// '; color: var(--primary); }

/* 站点头部 */
.site-header {
  position: sticky; top: 0; z-index: 50;
  background: color-mix(in srgb, var(--card-bg) 88%, transparent);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(10px);
}
.site-header-inner {
  max-width: 1400px; margin: 0 auto; padding: 10px 20px;
  display: flex; align-items: center; gap: 24px;
}
.site-brand { font-family: var(--font-mono); font-size: 16px; font-weight: 700; color: var(--text); white-space: nowrap; }
.site-brand:hover { text-decoration: none; }
.brand-path { color: var(--primary); }
.site-nav { display: flex; gap: 4px; flex: 1; }
.site-nav a { font-family: var(--font-mono); font-size: 13px; color: var(--muted); padding: 6px 10px; border-radius: 4px; }
.header-tools { display: flex; align-items: center; gap: 10px; margin-left: auto; }

/* 纯 CSS 主题开关: 不需要 JS */
.theme-switch { position: relative; display: inline-flex; cursor: pointer; }
.theme-switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.theme-switch .track {
  width: 58px; height: 28px; border-radius: 999px;
  background: var(--code-bg); border: 1px solid var(--border-strong);
  display: inline-flex; align-items: center; padding: 2px;
  transition: background-color .25s ease, border-color .25s ease;
}
.theme-switch .thumb {
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--card-bg); border: 1px solid var(--border-strong);
  display: grid; place-items: center; font-size: 12px;
  transform: translateX(0);
  transition: transform .28s cubic-bezier(.22,.72,.28,1);
}
.theme-switch input:checked + .track .thumb { transform: translateX(30px); }
.theme-switch .thumb::after { content: '☀'; }
.theme-switch input:checked + .track .thumb::after { content: '☾'; }
.theme-switch:hover .track { border-color: var(--primary); }

/* 卡片与资料卡 */
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
}
.profile-card { text-align: center; padding: 26px 18px 20px; }
.profile-avatar {
  width: 96px; height: 96px; border-radius: 50%; margin: 0 auto 12px;
  background: var(--accent-grad); color: #fff;
  display: grid; place-items: center; font-size: 34px; font-weight: 700;
  box-shadow: 0 10px 24px -16px var(--ring);
}
.profile-name { margin: 0 0 6px; font-size: 21px; font-weight: 700; letter-spacing: -.01em; }
.profile-bio { font-family: var(--font-mono); color: var(--muted); font-size: 12px; margin: 0 0 16px; }
.profile-social { display: flex; justify-content: center; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.social-link {
  display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px;
  border: 1px solid var(--border); border-radius: 4px; color: var(--text);
  font-family: var(--font-mono); font-size: 11.5px;
}
.social-link:hover { border-color: var(--primary); color: var(--primary); text-decoration: none; }
.profile-tags { display: flex; justify-content: center; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.el-tag {
  font-family: var(--font-mono); font-size: 11px; line-height: 1.75;
  padding: 1px 9px; border-radius: var(--radius-pill);
  border: 1px solid var(--border-strong); color: var(--muted); background: transparent;
}
.profile-categories {
  border-top: 1px solid var(--border); padding-top: 12px;
  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
}
.chip {
  display: inline-flex; align-items: center; border: 1px solid transparent;
  border-radius: 4px; padding: 1px 8px;
  font-family: var(--font-mono); font-size: 11.5px; line-height: 1.75; white-space: nowrap;
  background: color-mix(in srgb, var(--chip-c, var(--primary)) 16%, transparent);
  border-color: color-mix(in srgb, var(--chip-c, var(--primary)) 42%, transparent);
  color: color-mix(in srgb, var(--chip-c, var(--primary)) 88%, var(--text));
}
.chip:hover { text-decoration: none; filter: saturate(1.2); }
.cat-green { --chip-c: #0d9488; }
.cat-lime { --chip-c: #16a34a; }
.cat-clay { --chip-c: #b5654a; }
.cat-sage { --chip-c: #64748b; }

/* 终端卡片 */
.term-card {
  margin-bottom: 20px; background: var(--term-bg); border: 1px solid var(--term-border);
  border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden;
}
.term-head {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  border-bottom: 1px solid var(--term-border);
  background: color-mix(in srgb, var(--term-bg) 82%, #0d1b14);
}
.term-dot { width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0; }
.term-dot-red { background: #f87171; } .term-dot-amber { background: #fbbf24; } .term-dot-green { background: #34d399; }
.term-title { font-family: var(--font-mono); font-size: 12px; color: var(--term-dim); flex: 1; text-align: center; }
.term-btn {
  font-family: var(--font-mono); font-size: 11px; padding: 3px 9px; cursor: pointer;
  background: transparent; border: 1px solid var(--term-border); border-radius: var(--radius-sm);
  color: var(--term-dim); transition: all var(--dur, .2s) var(--ease, ease);
}
.term-btn:hover { color: var(--term-text); border-color: var(--term-dim); }
.term-body { padding: 16px 20px 18px; font-family: var(--font-mono); font-size: 13.5px; line-height: 1.75; }
.term-line { margin: 8px 0 0; color: var(--term-prompt); }
.term-prompt { color: var(--term-accent); margin-right: 8px; }
.term-out { margin: 0 0 2px 20px; color: var(--term-text); overflow-wrap: anywhere; }
.term-out a { color: var(--term-text); text-decoration: underline; text-underline-offset: 3px; }
.term-cursor {
  display: inline-block; width: 8px; height: 15px; margin-left: 2px; vertical-align: -2px;
  background: var(--term-accent); animation: term-blink 1.1s steps(2, start) infinite;
}
@keyframes term-blink { 0%,49% { opacity: 1; } 50%,100% { opacity: 0; } }

/* 历史上的今天 */
.history-card { margin-bottom: 20px; }
.history-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.history-event { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px dashed var(--border); }
.history-event:last-child { border-bottom: none; }
.history-year { flex-shrink: 0; width: 54px; font-weight: 700; color: var(--primary); font-size: 15px; }
.history-title { font-size: 14.5px; font-weight: 600; }
.history-desc { font-size: 13px; color: var(--muted); margin: 4px 0 6px; line-height: 1.6; }
.code-token {
  font-family: var(--font-mono); font-size: 11.5px; color: var(--primary);
  background: var(--primary-weak); border-radius: 4px; padding: 1px 7px; margin-right: 6px;
}

/* 贡献热力图 */
.contrib { display: flex; gap: 3px; overflow: hidden; margin-top: 6px; }
.contrib-week { display: flex; flex-direction: column; gap: 3px; }
.cell { width: 11px; height: 11px; border-radius: 2px; }
.legend { display: flex; align-items: center; gap: 6px; margin-top: 12px; font-size: 12px; color: var(--muted); }

/* 文章卡片 */
.post-card { margin-bottom: 14px; }
.post-card .post-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.post-title { margin: 0; font-size: 17px; font-weight: 700; letter-spacing: -.01em; line-height: 1.45; }
.post-title a { color: var(--text); }
.post-summary { margin: 6px 0 10px; color: var(--muted); font-size: 13.5px; line-height: 1.65; }
.post-meta {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 11.5px; color: var(--muted);
}
.status-tag {
  flex-shrink: 0; font-family: var(--font-mono); font-size: 11px; padding: 1px 8px;
  border-radius: var(--radius-pill); color: var(--warn);
  border: 1px solid color-mix(in srgb, var(--warn) 45%, transparent);
  background: color-mix(in srgb, var(--warn) 14%, transparent);
}

/* 按钮区(展示 Element Plus 按钮的优化效果) */
.btn-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 18px; }
.btn {
  font-family: var(--font-sans); font-size: 14px; font-weight: 500;
  padding: 8px 18px; border-radius: var(--el-border-radius-base, 6px);
  border: 1px solid var(--border-strong); background: var(--card-bg); color: var(--text);
  cursor: pointer;
}
.btn-primary { background: var(--primary); border-color: var(--primary); color: var(--on-primary); }
.btn-round { border-radius: 999px; }
.btn-circle { width: 36px; height: 36px; padding: 0; border-radius: var(--radius-sm); display: grid; place-items: center; }
.btn-row .el-button--primary { background: var(--primary); border-color: var(--primary); color: var(--on-primary); }

/* 分页 */
.pagination-row { display: flex; justify-content: center; gap: 6px; margin-top: 20px; }
.el-pagination.is-background .el-pager { display: flex; gap: 6px; }
.el-pagination.is-background .el-pager li {
  list-style: none; min-width: 32px; height: 32px; display: grid; place-items: center;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-family: var(--font-mono); font-size: 13px; cursor: pointer; background: var(--card-bg);
}
.el-pagination.is-background .el-pager li.is-active { color: #fff; }

/* 站脚 */
.site-footer {
  margin-top: 34px; text-align: center; padding: 16px;
  border-top: 1px solid var(--border); background: var(--card-bg);
  font-family: var(--font-mono); font-size: 12px; color: var(--muted);
}

/* 预览说明条 */
.preview-banner {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between;
  max-width: 1400px; margin: 0 auto; padding: 10px 20px 0;
  font-family: var(--font-mono); font-size: 11.5px; color: var(--muted);
}
.preview-banner b { color: var(--text); }

@media (max-width: 900px) {
  .home-grid { grid-template-columns: 1fr; }
  .site-nav { display: none; }
}
</style>
</head>
<body>
<header class="site-header">
  <div class="site-header-inner">
    <a class="site-brand" href="#"><span>phxxblog</span><span>@blog</span><span class="brand-path">:~$</span></a>
    <nav class="site-nav">
      <a href="#" class="router-link-active">首页</a>
      <a href="#">归档</a>
      <a href="#">全部文章</a>
      <a href="#">写文章</a>
      <a href="#">管理后台</a>
    </nav>
    <div class="header-tools">
      <label class="theme-switch" title="切换深色 / 浅色">
        <input type="checkbox" ${opts.mode === 'dark' ? 'checked' : ''} onchange="document.documentElement.classList.toggle('dark', this.checked)" />
        <span class="track"><span class="thumb"></span></span>
      </label>
    </div>
  </div>
</header>

<div class="preview-banner">
  <span>主题 <b>${opts.name}</b> · ${opts.en} · ${opts.tag}</span>
  <span>当前: <b>${opts.mode === 'dark' ? '深色' : '浅色'}</b> · 样式来自 frontend/src/styles/themes/${opts.file}</span>
</div>

<div class="page-container">
  <div class="home-grid">
    <!-- 左侧: 资料卡 -->
    <div class="home-left">
      <aside class="card profile-card">
        <div class="profile-avatar">C</div>
        <h1 class="profile-name">phxxblog</h1>
        <p class="profile-bio">写代码, 也写点别的</p>
        <div class="profile-social">
          <a class="social-link" href="#">GitHub</a>
          <a class="social-link" href="#">Blog</a>
          <a class="social-link" href="#">Email</a>
        </div>
        <div class="profile-tags">
          <span class="el-tag">Vue3</span><span class="el-tag">FastAPI</span><span class="el-tag">TypeScript</span>
        </div>
        <div class="profile-categories">
          <a class="chip cat-green" href="#">前端 (24)</a>
          <a class="chip cat-lime" href="#">后端 (18)</a>
          <a class="chip cat-clay" href="#">随笔 (9)</a>
          <a class="chip cat-sage" href="#">运维 (5)</a>
        </div>
      </aside>
    </div>

    <!-- 右侧: 终端 + 内容 -->
    <main class="home-main">
      <section class="term-card">
        <div class="term-head">
          <span class="term-dot term-dot-red"></span>
          <span class="term-dot term-dot-amber"></span>
          <span class="term-dot term-dot-green"></span>
          <span class="term-title">session — phxxblog</span>
          <button class="term-btn">复制</button>
          <button class="term-btn">换一句</button>
        </div>
        <div class="term-body">
          <p class="term-line"><span class="term-prompt">$</span> whoami</p>
          <p class="term-out">phxxblog — 写代码, 也写点别的</p>
          <p class="term-line"><span class="term-prompt">$</span> ls posts | wc -l</p>
          <p class="term-out">56</p>
          <p class="term-line"><span class="term-prompt">$</span> tail -n 1 posts/latest</p>
          <p class="term-out"><a href="#">2024-06-12 · 用 Vite 重构一个老项目的实战记录</a></p>
          <p class="term-line"><span class="term-prompt">$</span> say</p>
          <p class="term-out">保持热爱, 奔赴山海。</p>
          <p class="term-line"><span class="term-prompt">$</span><span class="term-cursor"></span></p>
        </div>
      </section>

      <section class="card history-card">
        <div class="history-head">
          <p class="eyebrow">history — 程序员历史上的今天</p>
          <button class="term-btn" style="color: var(--muted); border-color: var(--border);">刷新</button>
        </div>
        <p class="muted" style="margin: 0 0 8px;">6 月 12 日</p>
        <div class="history-event">
          <span class="history-year">1985</span>
          <div>
            <div class="history-title">C++ 的第一个商业实现发布</div>
            <div class="history-desc">Bjarne Stroustrup 在贝尔实验室发布 Cfront 1.0, 从此 C 有了类。</div>
            <div><span class="code-token">language</span><span class="code-token">#cpp</span></div>
          </div>
        </div>
      </section>

      <section class="card" style="margin-bottom: 20px;">
        <p class="eyebrow" style="margin-bottom: 12px;">activity — 文章发布记录</p>
        <div class="contrib">
          ${opts.cells}
        </div>
        <div class="legend">
          <span>少</span>
          <span class="cell" style="background: var(--cell-0);"></span>
          <span class="cell" style="background: var(--cell-1);"></span>
          <span class="cell" style="background: var(--cell-2);"></span>
          <span class="cell" style="background: var(--cell-3);"></span>
          <span class="cell" style="background: var(--cell-4);"></span>
          <span>多</span>
        </div>
      </section>

      <section class="home-posts">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px;">
          <div>
            <p class="eyebrow" style="margin-bottom:4px;">posts — 全部文章</p>
            <h2 class="posts-title" style="margin:0;font-size:20px;letter-spacing:-.01em;">全部文章</h2>
          </div>
          <span class="muted" style="font-family:var(--font-mono);font-size:12px;">共 56 篇</span>
        </div>

        ${opts.posts}

        <div class="pagination-row">
          <div class="el-pagination is-background">
            <ul class="el-pager">
              <li>1</li><li class="is-active">2</li><li>3</li><li>4</li>
            </ul>
          </div>
        </div>
      </section>

      <div class="btn-row">
        <button class="btn btn-primary el-button--primary">主要操作</button>
        <button class="btn">次要操作</button>
        <button class="btn btn-round">圆角按钮</button>
        <button class="btn btn-circle">★</button>
      </div>
    </main>
  </div>
</div>

<footer class="site-footer">© 2024 phxxblog · Vue3 + FastAPI</footer>
</body>
</html>
`

const POSTS = [
  {
    title: '用 Vite 重构一个老项目的实战记录',
    summary: '从 webpack 迁到 Vite 的完整过程: 踩过的坑、构建耗时变化, 以及那些不值得迁移的部分。',
    cat: ['cat-green', '前端'],
    tags: ['#vite', '#build'],
    date: '2024-06-12',
  },
  {
    title: 'FastAPI + Vue 的鉴权方案复盘',
    summary: 'JWT 存在哪里、刷新时机怎么定、401 之后如何优雅重试, 一次真实的踩坑记录。',
    cat: ['cat-lime', '后端'],
    tags: ['#fastapi', '#auth'],
    date: '2024-06-02',
  },
  {
    title: '关于写作这件事的一些想法',
    summary: '写了三年技术博客, 我对「写给谁看」这个问题的答案变了好几次。',
    cat: ['cat-clay', '随笔'],
    tags: ['#writing'],
    status: '草稿',
    date: '2024-05-20',
  },
]

function postHtml(p) {
  const tags = p.tags.map((t) => `<span class="chip cat-sage">${t}</span>`).join('\n          ')
  return `<article class="card post-card">
          <div class="post-head">
            <h2 class="post-title"><a href="#">${p.title}</a></h2>
            ${p.status ? `<span class="status-tag">${p.status}</span>` : ''}
          </div>
          <p class="post-summary">${p.summary}</p>
          <div class="post-meta">
            <a class="chip ${p.cat[0]}" href="#">${p.cat[1]}</a>
            <span>约 2400 字 · 大约 9 分钟</span>
            ${tags}
            <span>${p.date}</span>
            <span class="chip cat-sage">views 128</span>
            <span class="chip cat-clay">likes 12</span>
          </div>
        </article>`
}

/** 生成 52 周 x 7 天的热力图占位 */
function cells() {
  const levels = [1, 2, 3, 4, 0, 2, 1, 3, 0, 1, 2, 2, 4, 1, 0, 3, 2, 1, 1, 0, 2, 3, 1, 4, 0, 2, 1, 3]
  let out = ''
  for (let w = 0; w < 52; w += 1) {
    out += '          <div class="contrib-week">\n'
    for (let d = 0; d < 7; d += 1) {
      const lv = levels[(w * 7 + d) % levels.length]
      out += `            <span class="cell" style="background: var(--cell-${lv});"></span>\n`
    }
    out += '          </div>\n'
  }
  return out.trimEnd()
}

fs.mkdirSync(outDir, { recursive: true })

for (const t of THEMES) {
  const css = fs.readFileSync(path.join(themeDir, t.file), 'utf8')
  const shared = sharedBlock(css)
  const defaultRoot = defaultRootBlock()
  const light = lightBlock(css, t.id)
  const dark = darkBlock(css, t.id)
  const layer = modernLayer(css)
  const posts = POSTS.map(postHtml).join('\n\n        ')

  for (const mode of ['light', 'dark']) {
    const out = path.join(outDir, `${t.id}-${mode}.html`)
    fs.writeFileSync(
      out,
      PAGE({ ...t, mode, shared, defaultRoot, light, dark, layer, posts, cells: cells(), site: 'phxxblog' }),
      'utf8'
    )
    console.log('written:', path.relative(repo, out))
  }
}

/* ---------------------------------------------------------------
 * 总览页: 把主题清单注入 index.html 的占位符
 * (index.html 本身是手写模板, 每次重新生成只是刷新里面的数据)
 * ------------------------------------------------------------- */
/*
 * 总览页: 以 _gallery-template.html 为模板, 注入主题清单后输出 index.html。
 * 模板只有一份, 每次重建都从模板生成, 因此可以直接覆盖输出, 不会累积漂移。
 */
const templatePath = path.join(here, '_gallery-template.html')
const outPath = path.join(outDir, 'index.html')
const template = fs.readFileSync(templatePath, 'utf8')
if (!template.includes('__THEMES__')) throw new Error('_gallery-template.html 里找不到 __THEMES__ 占位符')

const html = template.replace('__THEMES__', JSON.stringify(THEMES, null, 2))
fs.writeFileSync(outPath, html, 'utf8')
console.log('written: ' + path.relative(repo, outPath) + ' (注入 ' + THEMES.length + ' 套主题)')

console.log('\n共 ' + THEMES.length + ' 套主题 × 2 模式 = ' + THEMES.length * 2 + ' 个预览页')
console.log('打开 ' + path.relative(repo, outPath) + ' 查看总览')
