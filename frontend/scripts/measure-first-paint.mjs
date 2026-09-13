/**
 * 测量首屏(首屏 HTML 直接引到的资源)与整包的体积。
 *
 * 为什么需要它: docs/architecture.md 的部署一节要给出"未压缩 / gzip 后"的具体数字,
 * 而肉眼估算是不可靠的 —— 之前文档里写着 780 KB, 实际优化后主 chunk 已经降到 45 KB,
 * 数字失真会让"要不要开 gzip"这类决策失去依据。
 *
 * 口径:
 *   首屏 = dist/index.html 里的 <script type="module"> + <link rel="modulepreload">
 *          + <link rel="stylesheet"> 指向的文件(即浏览器渲染首屏前必须下载的资源)。
 *   整包 = dist 下所有 .js / .css / .html 文件之和(不含 vditor/ 与 fonts/ 这类按需资源)。
 *
 * 用法: node scripts/measure-first-paint.mjs   (需先 npm run build)
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { gzipSync } from 'node:zlib'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const dist = path.resolve(here, '..', 'dist')

const kb = (bytes) => `${(bytes / 1024).toFixed(1)} KB`

let html
try {
  html = readFileSync(path.join(dist, 'index.html'), 'utf8')
} catch {
  console.error(`找不到 ${dist}/index.html, 请先执行 npm run build`)
  process.exit(1)
}

/** 从 index.html 中收集首屏必须加载的资源路径 */
function firstPaintAssets(source) {
  const files = new Set()
  // <script type="module" crossorigin src="/assets/xxx.js">
  for (const match of source.matchAll(/<script[^>]+src="([^"]+)"/g)) files.add(match[1])
  // <link rel="modulepreload" href="/assets/xxx.js"> 与 <link rel="stylesheet" href="...">
  for (const match of source.matchAll(/<link[^>]+href="([^"]+\.(?:js|css))"/g)) files.add(match[1])
  return [...files].map((href) => path.join(dist, href.replace(/^\//, '')))
}

/** 递归列出 dist 下的 .js/.css/.html(按需加载的 vditor 与字体不计入) */
function walk(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'vditor' || entry.name === 'fonts') continue
      walk(full, out)
    } else if (/\.(js|css|html)$/.test(entry.name)) {
      out.push(full)
    }
  }
  return out
}

/** 返回 [原始字节, gzip 字节] */
function measure(file) {
  const raw = readFileSync(file)
  return [raw.length, gzipSync(raw).length]
}

const firstPaint = firstPaintAssets(html)
if (!firstPaint.length) {
  console.error('index.html 里没有解析到任何脚本/样式引用, 打包格式可能变了')
  process.exit(1)
}

const [fpRaw, fpGzip] = firstPaint.reduce(
  ([r, g], file) => {
    const [raw, gz] = measure(file)
    return [r + raw, g + gz]
  },
  [0, 0],
)

const bundle = walk(dist).filter((file) => !firstPaint.includes(file))
const [bundleRaw, bundleGzip] = bundle.reduce(
  ([r, g], file) => {
    const [raw, gz] = measure(file)
    return [r + raw, g + gz]
  },
  [0, 0],
)

console.log('首屏资源(渲染首屏前必须下载):')
for (const file of firstPaint) {
  const [raw, gz] = measure(file)
  console.log(`  ${path.relative(dist, file).padEnd(38)} ${kb(raw).padStart(10)}  gzip ${kb(gz).padStart(9)}`)
}
console.log(`  ${'合计'.padEnd(36)} ${kb(fpRaw).padStart(10)}  gzip ${kb(fpGzip).padStart(9)}`)
console.log()
console.log(`按需资源(${bundle.length} 个文件, 进页面后按路由/功能懒加载):`)
console.log(`  ${'合计'.padEnd(36)} ${kb(bundleRaw).padStart(10)}  gzip ${kb(bundleGzip).padStart(9)}`)
console.log()
console.log(`整包合计: ${kb(fpRaw + bundleRaw)} (gzip 后 ${kb(fpGzip + bundleGzip)})`)
console.log(`dist 文件总数: ${firstPaint.length + bundle.length}`)
console.log()
console.log('提示: vditor/(约 21MB)与 fonts/ 未计入, 它们是编辑器与字体按需资源。')

// 供 CI 判断是否需要重新生成文档中的数字
if (process.argv.includes('--json')) {
  console.log(
    JSON.stringify({
      firstPaint: { raw: fpRaw, gzip: fpGzip },
      lazy: { raw: bundleRaw, gzip: bundleGzip, files: bundle.length },
    }),
  )
}
