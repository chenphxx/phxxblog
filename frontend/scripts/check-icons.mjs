/**
 * 校验 MetaIcon 的 SVG path 是否合法。
 *
 * 为什么需要它: 图标是内联 path 数据, 手写容易出「数字粘连」这类错误,
 * 例如 arc 参数写成 `7.5.5`(本应是 `7.5 .5`)。这种错误不会报错,
 * 只会让某一笔画不出来 —— 没有浏览器时几乎发现不了。
 *
 * 做法: 按 SVG 规范对 path 分词, 再逐段核对命令参数个数。
 * 注意 SVG 允许省略数字间的分隔符(负号本身即分隔符), 所以 `0-20` 是合法的两个数。
 *
 * 用法: npm run check:icons
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const file = path.resolve(here, '../src/components/MetaIcon.vue')
const src = fs.readFileSync(file, 'utf8')

const begin = src.indexOf('const PATHS')
const end = src.indexOf('\n}', begin)
if (begin < 0 || end < 0) throw new Error('在 MetaIcon.vue 里找不到 PATHS 定义')

const body = src.slice(begin, end)
const entries = [...body.matchAll(/(\w+):\s*'([^']+)'/g)].map((m) => ({ name: m[1], d: m[2] }))
if (!entries.length) throw new Error('没有解析到任何路径')

/** 各 SVG 命令的参数个数 */
const ARITY = {
  M: 2, m: 2, L: 2, l: 2, H: 1, h: 1, V: 1, v: 1,
  C: 6, c: 6, S: 4, s: 4, Q: 4, q: 4, T: 2, t: 2, A: 7, a: 7, Z: 0, z: 0,
}

/**
 * 按 SVG 规范把 path 解析成 [{ cmd, args }]。
 * 命令字母 | 数字(可带正负号与小数), 空白和逗号作为分隔。
 */
function parsePath(d) {
  const re = /([MmLlHhVvCcSsQqTtAaZz])|(-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)/g
  const tokens = []
  let m
  while ((m = re.exec(d)) !== null) {
    tokens.push(m[1] ? { type: 'cmd', value: m[1] } : { type: 'num', value: Number(m[2]) })
  }
  const leftover = d.replace(re, '').replace(/[\s,]+/g, '')
  if (leftover) throw new Error(`无法分词的内容: "${leftover}"`)

  const segments = []
  let current = null
  for (const tk of tokens) {
    if (tk.type === 'cmd') {
      current = { cmd: tk.value, args: [] }
      segments.push(current)
    } else {
      if (!current) throw new Error('路径以数字开头(缺少 M/m 命令)')
      current.args.push(tk.value)
    }
  }
  return segments
}

let fail = 0

for (const { name, d } of entries) {
  const problems = []
  let segments = []

  try {
    segments = parsePath(d)
  } catch (e) {
    problems.push(e.message)
  }

  if (!problems.length) {
    if (!/^[Mm]/.test(d.trim())) problems.push('未以 M/m 开头')

    segments.forEach((seg, i) => {
      const need = ARITY[seg.cmd]
      if (need === undefined) {
        problems.push(`未知命令 "${seg.cmd}"`)
        return
      }
      if (need === 0) {
        if (seg.args.length) problems.push(`闭合命令 ${seg.cmd} 不应带参数`)
        return
      }
      // M/m 之后重复的坐标对等价于 L/l, 属合法写法, 只要求是整数倍
      if (seg.args.length === 0 || seg.args.length % need !== 0) {
        problems.push(`第 ${i + 1} 段命令 ${seg.cmd} 参数 ${seg.args.length} 个, 不是 ${need} 的整数倍`)
      }
      seg.args.forEach((n) => {
        if (Number.isNaN(n)) problems.push(`第 ${i + 1} 段命令 ${seg.cmd} 出现非法数字`)
      })
    })

    const glued = d.match(/\d+\.\d+\.\d+/g)
    if (glued) problems.push('数字粘连: ' + glued.join(', '))
  }

  if (problems.length) {
    fail++
    console.log(`  FAIL ${name.padEnd(10)} ${problems.join(' | ')}`)
  } else {
    const argCount = segments.reduce((s, seg) => s + seg.args.length, 0)
    console.log(`  ok   ${name.padEnd(10)} ${segments.length} 段命令, ${argCount} 个参数`)
  }
}

// 模板里用到但未定义的图标名
const used = [...src.matchAll(/name="(\w+)"/g)].map((m) => m[1])
const defined = new Set(entries.map((e) => e.name))
const missing = [...new Set(used)].filter((n) => !defined.has(n))
if (missing.length) {
  fail++
  console.log('  FAIL 模板里用到但未定义的图标: ' + missing.join(', '))
}

console.log(`\n共 ${entries.length} 个图标, ${fail === 0 ? 'ALL OK' : fail + ' 个有问题'}`)
process.exit(fail === 0 ? 0 : 1)
