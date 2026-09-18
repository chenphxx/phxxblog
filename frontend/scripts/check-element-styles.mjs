/**
 * 检查「程序式调用的 Element Plus 组件」是否都补了样式。
 *
 * 背景(一次真实事故):
 *   Element Plus 改成按需引入后, 样式只在**模板里出现**的标签上自动注入。
 *   `ElMessageBox.confirm(...)` / `ElMessage.success(...)` 是 JS 调用, 不在模板里,
 *   解析器看不到 → 样式没进来 → 确认框变成页面左上角一堆裸按钮(没有遮罩、没有圆角),
 *   提示条更是完全不可见(那句"请输入日记内容"被吞掉, 用户以为按钮没反应)。
 *   这类问题 type-check 与单测都发现不了, 只能在构建产物/源码里查。
 *
 * 做法: 扫描 src 下所有 .vue/.ts 用到了哪些程序式 API, 再核对 main.ts 是否 import 了
 * 对应组件的样式。少一行就在这里失败, 而不是等到某天用户看见一个裸对话框。
 *
 * 用法: npm run check:element-styles
 */
import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const src = path.resolve(here, '..', 'src')
const mainTs = path.join(src, 'main.ts')

/** 程序式 API -> 需要的样式入口(与 main.ts 里的 import 一一对应) */
const PROGRAMMATIC = {
  ElMessage: 'element-plus/es/components/message/style/css',
  ElMessageBox: 'element-plus/es/components/message-box/style/css',
  ElLoading: 'element-plus/es/components/loading/style/css',
  ElNotification: 'element-plus/es/components/notification/style/css',
}

/** 递归收集 src 下的源码文件(测试文件不算: 它们不会进产物) */
function walk(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      walk(full, out)
    } else if (/\.(vue|ts)$/.test(entry.name) && !/\.test\.ts$/.test(entry.name)) {
      out.push(full)
    }
  }
  return out
}

/** 去掉注释, 避免把说明文字里的 API 名当成真实调用 */
function stripComments(code) {
  return code.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1')
}

const files = walk(src)
const mainSource = readFileSync(mainTs, 'utf8')
const used = new Map()

for (const file of files) {
  // main.ts 自己只是做 import, 不作为调用点统计
  if (file === mainTs) continue
  const code = stripComments(readFileSync(file, 'utf8'))
  for (const api of Object.keys(PROGRAMMATIC)) {
    const pattern = new RegExp(`\\b${api}\\.`)
    if (pattern.test(code) && !used.has(api)) {
      used.set(api, path.relative(src, file))
    }
  }
}

const problems = []
console.log('程序式 Element Plus API 与样式引入检查:')
for (const [api, file] of [...used.entries()].sort()) {
  const stylePath = PROGRAMMATIC[api]
  const imported = mainSource.includes(`'${stylePath}'`)
  console.log(`  ${imported ? 'ok  ' : 'MISS'} ${api.padEnd(15)} 用于 ${file}`)
  if (!imported) problems.push({ api, stylePath })
}

if (!used.size) {
  console.log('  没有发现程序式 API 调用(只统计 src 下的 .vue/.ts, 不含测试)')
}

if (problems.length) {
  console.error('\n以下程序式组件的样式没有在 src/main.ts 中引入, 运行时会是"裸样式":')
  for (const { api, stylePath } of problems) {
    console.error(`  ${api}  ->  在 src/main.ts 增加: import '${stylePath}'`)
  }
  console.error('\n原因说明见 src/main.ts 中「程序式调用的组件必须手动补样式」一节。')
  process.exit(1)
}

console.log('\nALL OK')
