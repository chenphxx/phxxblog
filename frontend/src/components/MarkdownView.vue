<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Vditor from 'vditor'
import { useThemeStore } from '@/stores/theme'
import type { MarkdownHeading } from '@/types'

const props = defineProps<{ content: string }>()
/**
 * @brief 渲染完成后把正文标题抛给父组件(文章详情页据此生成右侧目录)
 *
 * @param headings 按文档顺序排列的标题; 正文没有标题时为空数组
 */
const emit = defineEmits<{ headings: [MarkdownHeading[]] }>()
const el = ref<HTMLDivElement>()
const theme = useThemeStore()

/** highlight.js 的最小类型(Vditor 会在运行时把 highlight.js 挂到 window.hljs) */
interface HljsLike {
  getLanguage: (name: string) => unknown
  highlight: (
    code: string,
    options: { language: string; ignoreIllegals?: boolean },
  ) => { relevance: number }
}

/**
 * 自动识别语言的候选集合(按本站常见程度排序, 相关度相同时取靠前者)。
 * 不直接使用全部语言, 既是为了速度, 也是为了避免长尾语言给出离谱的结果。
 */
const AUTO_LANGS = [
  'c', 'cpp', 'rust', 'python', 'javascript', 'typescript', 'java', 'go', 'csharp',
  'bash', 'shell', 'powershell', 'sql', 'json', 'yaml', 'xml', 'html', 'css', 'php',
  'kotlin', 'swift', 'objectivec', 'ruby', 'lua', 'perl', 'r', 'matlab', 'dart',
  'scala', 'dockerfile', 'makefile', 'ini', 'markdown',
]

/** 代码高亮主题: 对齐 VSCode 默认配色(浅色 vs / 深色 vs2015) */
function codeStyle() {
  return theme.isDark ? 'vs2015' : 'vs'
}

function getHljs(): HljsLike | undefined {
  return (window as unknown as { hljs?: HljsLike }).hljs
}

/** 等待 Vditor 异步加载 highlight.js 完成(带超时, 避免无限等待) */
async function waitForHljs(timeout = 3000): Promise<HljsLike | undefined> {
  const deadline = Date.now() + timeout
  while (Date.now() < deadline) {
    const instance = getHljs()
    if (instance) return instance
    await new Promise((resolve) => setTimeout(resolve, 50))
  }
  return undefined
}

/** 语言标记正则(支持 c#, f# 这类别名) */
const LANGUAGE_RE = /(?:^|\s)language-([^\s]+)/

/**
 * 语言特征提示: 命中即采用对应语言(需 highlight.js 已注册该语言)。
 *
 * 短代码片段单靠相关度打分并不可靠(例如 Rust 的 `let x: i32 = 1;` 会被判成 ini,
 * PowerShell 的一行命令会被判成别的语言), 这些特征模式可以稳定认出本站常见语言。
 * 顺序即优先级: 同时命中时取靠前的规则。
 */
const LANG_HINTS: Array<[RegExp, string]> = [
  // C++: 命名空间 / 标准库 / 模板
  [/\bstd::|\bcout\b|\bcin\b|#include\s*[<"]iostream[>"]|\btemplate\s*</, 'cpp'],
  // C: 预处理指令 / 标准库函数
  [/^\s*#\s*(include|define|ifdef|ifndef|pragma|undef|error|line|elif|endif)\b/m, 'c'],
  [/\b(printf|scanf|malloc|calloc|realloc|memcpy|strcmp|strcpy|strlen|puts|gets|sizeof)\s*\(/, 'c'],
  // Rust: 带类型的 let 绑定 / 特征宏 / 特征关键字
  [/\blet\s+\w+\s*:\s*(i8|i16|i32|i64|i128|u8|u16|u32|u64|usize|isize|f32|f64|bool|String|&str|Vec|Option|Result)\b|\bimpl\s+\w|\btrait\s+\w|\bmut\s+\w|println!|vec!|\.unwrap\(\)/, 'rust'],
  // PowerShell: 别名与常见 cmdlet
  [/\b(irm|iex)\b|Invoke-(Expression|WebRequest|RestMethod)|\b(Get|Set|New|Test|Remove)-(Item|Content|ChildItem|Command|Process|Service|Value|Variable|Object)\b/, 'powershell'],
]

/**
 * 用 highlight.js 给代码块挑一个最可能的语言。
 *
 * 不能直接用 hljs.highlightAuto: 它内部按 `ignoreIllegals: false` 打分, 命中非法词法的
 * 语言会被直接丢弃, 于是短小的 C 片段(例如带未闭合字符串的示例)常被误判成 swift /
 * perl / maxima 之类的语言。这里改为逐个候选语言打分(允许非法词法), 取相关度最高者;
 * 相关度为 0 时视为无法识别, 保持纯文本, 避免给普通文字套上乱七八糟的颜色。
 */
function detectLanguage(instance: HljsLike, code: string): string | undefined {
  for (const [pattern, lang] of LANG_HINTS) {
    if (pattern.test(code) && instance.getLanguage(lang)) return lang
  }
  let best: string | undefined
  let bestScore = 0
  AUTO_LANGS.forEach((lang) => {
    if (!instance.getLanguage(lang)) return
    let score = 0
    try {
      score = instance.highlight(code, { language: lang, ignoreIllegals: true }).relevance
    } catch {
      score = 0
    }
    if (score > bestScore) {
      bestScore = score
      best = lang
    }
  })
  return best
}

/**
 * 让所有代码块都带上语法高亮。
 *
 * Vditor 只会高亮带 `language-*` 标注的代码块, 未标注的(例如从 WordPress 导入的
 * 缩进代码块)会被当成 plaintext, 完全没有配色。这里先用 highlight.js 自动识别这些
 * 代码块的语言, 再统一调用 Vditor.highlightRender 重新渲染, 配色与行号一次到位。
 *
 * 注意: Vditor 取语言用的是 `code.className.replace("language-", "")`, 所以重新渲染前
 * 必须先摘掉上一次渲染留下的 `hljs` / `vditor-linenumber` 类, 否则语言名会解析失败并
 * 退化成 plaintext(表现就是"完全没有高亮")。
 */
async function highlightCode(root: HTMLDivElement) {
  const instance = await waitForHljs()
  if (!instance) return
  root.querySelectorAll<HTMLElement>('pre > code').forEach((code) => {
    // 清理上一次渲染的类名与行号节点, 保证语言解析正确、行号不重复
    code.classList.remove('hljs', 'vditor-linenumber')
    code
      .querySelectorAll('.vditor-linenumber__rows, .vditor-linenumber__temp')
      .forEach((node) => node.remove())
    if (LANGUAGE_RE.test(code.className)) return
    const language = detectLanguage(instance, code.textContent || '')
    if (language) code.classList.add(`language-${language}`)
  })
  Vditor.highlightRender(
    { enable: true, lineNumber: true, defaultLang: '', style: codeStyle() },
    root,
    '/vditor',
  )
}

/** 超过该行数的代码块默认折叠 */
const CODE_FOLD_LINES = 20

/**
 * 已展开的代码块(按代码块序号记录; 主题切换会重新渲染, 借此保持展开状态)。
 *
 * 必须在组件作用域内: 以前它定义在模块顶层, 是**跨实例共享**的隐藏状态。
 * 首页的 README 区与文章详情会同时渲染 MarkdownView, 两处都会读写同一个 Set,
 * 于是"展开第 3 个代码块"会同时影响另一个实例。
 */
const expandedBlocks = new Set<number>()

/** 点击正文图片时预览的地址(空字符串表示不展示) */
const previewSrc = ref('')

/**
 * 长代码块折叠: 超过 20 行的代码块只展示前 20 行, 点击按钮展开/收起。
 * 折叠时用 max-height 裁剪并隐藏纵向溢出, 不出现滚动条。
 */
function applyCodeFold(root: HTMLDivElement) {
  root.querySelectorAll<HTMLElement>('pre').forEach((pre, index) => {
    if (pre.parentElement?.classList.contains('code-block')) return
    const code = pre.querySelector('code')
    if (!code) return
    const lineCount = (code.textContent || '').replace(/\n+$/, '').split('\n').length
    if (lineCount <= CODE_FOLD_LINES) return

    // 按实际行高算出"前 20 行"的高度, 避免出现半行
    const styles = getComputedStyle(pre)
    const codeStyles = getComputedStyle(code)
    const codePadding =
      (parseFloat(codeStyles.paddingTop) || 0) + (parseFloat(codeStyles.paddingBottom) || 0)
    // 用实测高度反推行高, 比读 line-height 更可靠(不受字号/字体影响)
    const lineHeight = (code.getBoundingClientRect().height - codePadding) / lineCount
    const border =
      (parseFloat(styles.borderTopWidth) || 0) + (parseFloat(styles.borderBottomWidth) || 0)
    const paddingTop = parseFloat(styles.paddingTop) || 0
    // 项目全局 box-sizing: border-box; 让边框盒正好等于"上内边距 + 20 行",
    // 裁剪边界(内边距盒)就落在第 20 行末尾, 不会露出第 21 行
    const collapsedHeight = Math.round(paddingTop + lineHeight * CODE_FOLD_LINES + border)

    const wrapper = document.createElement('div')
    wrapper.className = 'code-block'
    wrapper.style.setProperty('--code-fold-height', `${collapsedHeight}px`)
    if (!expandedBlocks.has(index)) wrapper.classList.add('is-collapsed')
    pre.replaceWith(wrapper)
    wrapper.appendChild(pre)

    const toggle = document.createElement('button')
    toggle.type = 'button'
    toggle.className = 'code-fold-toggle'
    const sync = () => {
      toggle.textContent = wrapper.classList.contains('is-collapsed')
        ? `展开全部 (共 ${lineCount} 行)`
        : '收起'
    }
    toggle.addEventListener('click', () => {
      if (wrapper.classList.toggle('is-collapsed')) expandedBlocks.delete(index)
      else expandedBlocks.add(index)
      sync()
    })
    sync()
    wrapper.appendChild(toggle)
  })
}

/**
 * 标题文本转锚点片段: 保留中英文与数字, 空格与标点统一压成连字符。
 *
 * @param text 标题纯文本
 * @return 可作为 id 的片段; 全部字符都被过滤掉时返回空串, 由调用方兜底
 */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/**
 * 给正文标题编锚点并收集目录。
 *
 * Vditor 渲染出来的标题没有 id, 目录需要的锚点只能自己补。同一篇文章里出现同名标题时
 * 追加 -2 / -3 保证唯一, 否则后一个同名标题的锚点会失效(点击目录跳到第一个)。
 *
 * @param root 正文根节点
 * @return 按文档顺序排列的标题列表
 */
function buildHeadings(root: HTMLDivElement): MarkdownHeading[] {
  const headings: MarkdownHeading[] = []
  const used = new Map<string, number>()
  root.querySelectorAll<HTMLElement>('h1, h2, h3, h4, h5, h6').forEach((node) => {
    const text = (node.textContent || '').trim()
    if (!text) return
    const base = slugify(text) || 'section'
    const seen = used.get(base) || 0
    used.set(base, seen + 1)
    node.id = seen === 0 ? base : `${base}-${seen + 1}`
    headings.push({ id: node.id, text, level: Number(node.tagName.slice(1)) })
  })
  return headings
}

async function render() {
  if (!el.value) return
  const currentTheme = theme.isDark ? 'dark' : 'light'
  el.value.innerHTML = ''
  await Vditor.preview(el.value, props.content || '', {
    // 本地资源, 避免依赖 CDN(同时保证 hljs 样式从 /vditor 加载)
    cdn: '/vditor',
    mode: currentTheme,
    theme: { current: currentTheme },
    hljs: { lineNumber: true, style: codeStyle() },
  })
  // 代码块一键复制按钮
  Vditor.codeRender(el.value)
  // 视频/音频/iframe 渲染
  Vditor.mediaRender(el.value)
  // 代码块语法高亮(未标注语言的自动识别)
  await highlightCode(el.value)
  // 长代码块折叠
  applyCodeFold(el.value)
  // 图片点击预览: 用 Element Plus 看图器(自适应窗口居中显示, 支持滚轮缩放与拖拽平移)
  el.value.querySelectorAll('img').forEach((img) => {
    img.addEventListener('click', () => {
      previewSrc.value = img.src
    })
  })
  // 标题锚点与目录(必须在 DOM 完整之后, 否则收集不到标题)
  emit('headings', buildHeadings(el.value))
}

onMounted(render)
watch(
  () => props.content,
  () => {
    // 换了文章就不保留上一篇文章的展开状态
    expandedBlocks.clear()
    render()
  },
)

/*
 * 主题变化需要重新渲染: 代码高亮的配色是 Vditor 按主题名(vs / vs2015)加载的,
 * 只切 CSS 变量不会让 <code> 里的 hljs token 换色。
 * 用 200ms 去抖合并"连点主题/深浅色"产生的多次触发 —— 每次 render 都会
 * 清空 innerHTML 再整篇重排, 连续触发既浪费又会闪。
 */
let themeRenderTimer: number | undefined
watch(
  () => theme.isDark,
  () => {
    if (themeRenderTimer !== undefined) window.clearTimeout(themeRenderTimer)
    themeRenderTimer = window.setTimeout(() => {
      themeRenderTimer = undefined
      render()
    }, 200)
  },
)

// 组件卸载时清掉待执行的定时器, 避免在已销毁的实例上重渲染
onBeforeUnmount(() => {
  if (themeRenderTimer !== undefined) window.clearTimeout(themeRenderTimer)
})
</script>

<template>
  <div ref="el" class="markdown-body vditor-reset" />
  <el-image-viewer
    v-if="previewSrc"
    :url-list="[previewSrc]"
    teleported
    hide-on-click-modal
    @close="previewSrc = ''"
  />
</template>
