/**
 * 将 node_modules/vditor/dist 复制到 public/vditor/dist,
 * 让 Vditor 的 Lute / 图标 / 高亮等资源走本地, 不依赖 unpkg/jsdelivr CDN。
 * 已在 package.json 的 predev / prebuild 中自动执行。
 */
import { cpSync, existsSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const src = join(frontendRoot, 'node_modules', 'vditor', 'dist')
const dest = join(frontendRoot, 'public', 'vditor', 'dist')

if (!existsSync(src)) {
  console.error('[copy-vditor-assets] 未找到 node_modules/vditor, 请先执行 npm install')
  process.exit(1)
}

mkdirSync(dirname(dest), { recursive: true })
cpSync(src, dest, { recursive: true, force: true })
console.log('[copy-vditor-assets] Vditor 静态资源已就绪: public/vditor/dist')
