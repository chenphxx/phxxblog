<!--
  看板娘本体: 一块固定定位的 canvas, 由 kanbanniang/live2d.js 在其上渲染 Live2D 模型。

  五条约束:
    1. 运行时(151 KB)与模型都等首屏之后再加载, 不与页面自身的请求抢带宽
    2. 窄屏不展示: 这块浮层在手机上会盖住正文, 也白白多下载一份模型
    3. 容器 pointer-events: none —— 运行时是在 window 上监听鼠标的, 不需要命中 canvas,
       因此不必让浮层挡住正文的点击
    4. 拖动直接抓模型本体, 不额外摆一个把手: 命中判定用一张模型轮廓掩膜(见 captureMask),
       按在透明处照旧把点击透给下面的正文
    5. 命中模型的那次按下会被拦下, 否则运行时会把拖动当成"点击模型"而播放摸头动作;
       只在按一下没拖动时补发一次事件, 让点击互动照旧
-->
<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { loadRuntime, render, supportsWebgl } from '@/kanbanniang/loader'
import { useKanbanniangStore, type KanbanniangPosition } from '@/stores/kanbanniang'

/** canvas 的 id 固定: 运行时按 id 取元素并初始化 WebGL */
const CANVAS_ID = 'kanbanniang-canvas'
/** 窄于这个宽度不展示 */
const NARROW_QUERY = '(max-width: 900px)'
/** 默认画布尺寸, 与下面 canvas 的样式一致; 形象可以在 registry 里单独指定(如全身像) */
const DEFAULT_CANVAS = { width: 280, height: 250 }
/** 位移小于它算点击不算拖动, 这样模型原本的点击互动还在 */
const DRAG_THRESHOLD = 4
/** 掩膜里 alpha 大于它才算模型本体(边缘抗锯齿的半透明像素不算) */
const MASK_ALPHA_MIN = 16
/** 模型有闲置动作, 轮廓会缓慢变化, 隔一段时间重新取一张掩膜 */
const MASK_REFRESH_MS = 1000

const kb = useKanbanniangStore()
const narrow = ref(window.matchMedia(NARROW_QUERY).matches)
/** 环境不支持(无 WebGL / 运行时加载失败)时彻底放弃, 不再反复重试 */
const broken = ref(false)
const visible = computed(() => kb.allowed && kb.enabled && !narrow.value && !broken.value)

/** 当前形象的画布尺寸 */
const canvasSize = computed(() => kb.current.canvas ?? DEFAULT_CANVAS)
const canvasStyle = computed(() => ({ width: `${canvasSize.value.width}px`, height: `${canvasSize.value.height}px` }))

const root = ref<HTMLElement | null>(null)
/** 当前浮层坐标, null 表示未拖动过, 停在 CSS 的默认位置(左下角) */
const pos = ref<KanbanniangPosition | null>(kb.position)
const dragging = ref(false)
/** 浮层被拖走后由内联样式接管定位, 同时把 CSS 的 bottom 让出来 */
const posStyle = computed(() =>
  pos.value ? { left: `${pos.value.x}px`, top: `${pos.value.y}px`, bottom: 'auto' } : undefined,
)

/** 候选拖动: 按下的鼠标位置 + 浮层当时的左上角 */
let pending: { x: number; y: number; left: number; top: number } | null = null
/** 拖动结束后紧跟的那次 click 要拦掉, 否则会点到浮层下面的链接 */
let swallowClick = false
/** 拖动期间临时禁掉选区, 松手后还原 */
let selectBackup: string | null = null
/** 正在补发点击(补发出来的事件不能再被自己的监听拦一次) */
let replaying = false

/** 模型轮廓掩膜: 每像素一个字节的 alpha, 用来判断指针是不是按在模型身上 */
let mask: Uint8Array | null = null
let maskW = 0
let maskH = 0

let maskTimer: number | undefined
let unsubscribe: (() => void) | undefined
let stopResize: (() => void) | undefined
let disposed = false

/** 顶栏是 sticky 且层级高于浮层, 浮层顶到那里就再也抓不回来, 这里给它让出这段高度 */
function headerHeight(): number {
  return document.querySelector('.site-header')?.getBoundingClientRect().height || 0
}

/** 把坐标收进可视范围, 免得浮层被拖到抓不回来的地方(窗口缩小后同样靠它拉回来) */
function clamp(x: number, y: number): KanbanniangPosition {
  const width = root.value?.offsetWidth || canvasSize.value.width
  const height = root.value?.offsetHeight || canvasSize.value.height
  const maxX = Math.max(0, window.innerWidth - width)
  const minY = Math.min(headerHeight(), Math.max(0, window.innerHeight - height))
  const maxY = Math.max(minY, window.innerHeight - height)
  return { x: Math.round(Math.min(Math.max(0, x), maxX)), y: Math.round(Math.min(Math.max(minY, y), maxY)) }
}

/** 窗口尺寸变化后把浮层重新收进视口 */
function reclamp() {
  if (!pos.value) return
  const next = clamp(pos.value.x, pos.value.y)
  pos.value = next
  kb.setPosition(next)
}

/**
 * @brief 重新生成模型轮廓掩膜。
 *
 * 运行时的绘制循环跑在 requestAnimationFrame 上, 它这一帧的回调排在前面, 因此我们排进去的
 * 回调跑完时画面还在, 此时把 canvas 拷进 2D canvas 就能读到像素(WebGL 的绘制缓冲默认在合成后清空)
 */
function captureMask() {
  const canvasEl = document.getElementById(CANVAS_ID) as HTMLCanvasElement | null
  if (!canvasEl) return
  requestAnimationFrame(() => {
    if (disposed || !canvasEl.isConnected) return
    const offscreen = document.createElement('canvas')
    offscreen.width = canvasEl.width
    offscreen.height = canvasEl.height
    const ctx = offscreen.getContext('2d')
    if (!ctx) return
    try {
      ctx.drawImage(canvasEl, 0, 0)
      const { data } = ctx.getImageData(0, 0, offscreen.width, offscreen.height)
      const next = new Uint8Array(offscreen.width * offscreen.height)
      let opaque = 0
      for (let i = 0; i < next.length; i++) {
        next[i] = data[i * 4 + 3]
        if (next[i] > MASK_ALPHA_MIN) opaque++
      }
      // 一像素都没读到说明浏览器留不住画面, 交给 hitsModel 的兜底逻辑
      mask = opaque ? next : null
      maskW = offscreen.width
      maskH = offscreen.height
    } catch {
      mask = null
    }
  })
}

/**
 * @brief 判断指针是否落在模型身上。
 * @param x 指针相对浮层左上角的横坐标
 * @param y 指针相对浮层左上角的纵坐标
 * @return 落在模型本体上返回 true; 掩膜取不到时退化成整块浮层都算命中, 保证模型挪得动
 */
function hitsModel(x: number, y: number): boolean {
  if (!mask || !maskW || !maskH) return true
  const el = root.value
  if (!el) return false
  const px = Math.floor((x / el.offsetWidth) * maskW)
  const py = Math.floor((y / el.offsetHeight) * maskH)
  if (px < 0 || py < 0 || px >= maskW || py >= maskH) return false
  return mask[py * maskW + px] > MASK_ALPHA_MIN
}

/** 按在模型上但没拖动: 补一次按下与抬起, 让运行时的点击互动照常触发 */
function replayTap(event: MouseEvent) {
  const init = { bubbles: true, clientX: event.clientX, clientY: event.clientY, button: 0 }
  replaying = true
  try {
    window.dispatchEvent(new MouseEvent('mousedown', init))
    window.dispatchEvent(new MouseEvent('mouseup', init))
  } finally {
    replaying = false
  }
}

function setCursor(cursor: string) {
  // 浮层整体 pointer-events: none, 光标只能借 body 表达"这里能拖"
  if (document.body.style.cursor === cursor) return
  document.body.style.cursor = cursor
}

/** 按下: 命中模型就记下候选拖动, 并拦下这次事件(见文件头的第 5 条) */
function onMouseDown(event: MouseEvent) {
  if (replaying || event.button !== 0 || dragging.value || !visible.value) return
  const el = root.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  // 先做便宜的矩形判断, 再做掩膜判断: 这个监听挂在 window 上, 页面上每次按下都会经过
  if (x < 0 || y < 0 || x >= rect.width || y >= rect.height) return
  if (!hitsModel(x, y)) return
  // 补发进来的事件不该再被拦一次, 这里顺带把上一次的拖动状态清干净
  swallowClick = false
  event.stopPropagation()
  pending = { x: event.clientX, y: event.clientY, left: rect.left, top: rect.top }
}

/** 移动: 超过阈值才真的开始拖, 拖动期间只改视图, 松手才落盘 */
function onMouseMove(event: MouseEvent) {
  if (!pending) {
    // 悬停在模型上时给出"可拖动"的光标
    const el = root.value
    if (!el || !visible.value) return
    const rect = el.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    const over = x >= 0 && y >= 0 && x < rect.width && y < rect.height && hitsModel(x, y)
    setCursor(over && !dragging.value ? 'grab' : '')
    return
  }
  const dx = event.clientX - pending.x
  const dy = event.clientY - pending.y
  if (!dragging.value) {
    if (Math.abs(dx) < DRAG_THRESHOLD && Math.abs(dy) < DRAG_THRESHOLD) return
    dragging.value = true
    selectBackup = document.body.style.userSelect
    document.body.style.userSelect = 'none'
    setCursor('grabbing')
  }
  pos.value = clamp(pending.left + dx, pending.top + dy)
}

/** 抬起: 拖动过就落盘并吃掉紧随其后的 click, 没拖动则补发一次点击 */
function onMouseUp(event: MouseEvent) {
  const start = pending
  pending = null
  const moved = dragging.value
  dragging.value = false
  setCursor('')
  if (selectBackup !== null) {
    document.body.style.userSelect = selectBackup
    selectBackup = null
  }
  if (!start) return
  if (moved) {
    kb.setPosition(pos.value)
    swallowClick = true
  } else {
    replayTap(event)
  }
}

/** 拖动那一下的 click 是"松手"留下的, 不该落到浮层下面的链接上 */
function onClickCapture(event: MouseEvent) {
  if (!swallowClick) return
  swallowClick = false
  event.stopPropagation()
  event.preventDefault()
}

/** 指针移出窗口时把光标还原 */
function onMouseLeave() {
  setCursor('')
  if (!dragging.value) pending = null
}

/** 首屏之后再干重活: 没有 requestIdleCallback 的浏览器退化成 200ms 后执行 */
function whenIdle(task: () => void) {
  if (typeof window.requestIdleCallback === 'function') window.requestIdleCallback(task, { timeout: 2000 })
  else window.setTimeout(task, 200)
}

/** 加载运行时并在 canvas 上渲染当前形象 */
async function show() {
  if (!visible.value) return
  // 先探测 WebGL: 缺了它运行时只会往控制台打一行错误, 这里更早退出
  if (!supportsWebgl()) {
    broken.value = true
    console.warn('[kanbanniang] 当前浏览器不支持 WebGL, 不展示看板娘')
    return
  }
  try {
    await loadRuntime()
    // canvas 一直在 DOM 里(靠 CSS 隐藏而不是销毁), 这里再等一轮渲染, 确保挂载已经完成
    await nextTick()
    // 等待期间可能被关掉(访客开关或后台开关), 那就别再请求模型
    if (!visible.value) return
    render(CANVAS_ID, kb.current.path)
    // 模型与纹理是异步加载的, 掩膜靠下面的定时器反复刷新, 这里先排一次
    window.setTimeout(captureMask, 300)
  } catch (err) {
    broken.value = true
    console.warn('[kanbanniang] 看板娘加载失败, 不再展示', err)
  }
}

/** 切形象: 运行时与 canvas 都已就绪, 用同一块 canvas 重新加载模型即可 */
async function switchModel() {
  if (!visible.value || typeof window.loadlive2d !== 'function') return
  // 换形象可能同时换画布尺寸(见 registry 的 canvas), 等新尺寸落到 DOM 上再渲染
  await nextTick()
  render(CANVAS_ID, kb.current.path)
  window.setTimeout(captureMask, 300)
}

/** 拖动靠 window 上的鼠标事件: 浮层整体 pointer-events: none, 事件本来就不经过它 */
function bindMouse() {
  window.addEventListener('mousedown', onMouseDown, true)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('click', onClickCapture, true)
  document.addEventListener('mouseleave', onMouseLeave)
}

function unbindMouse() {
  window.removeEventListener('mousedown', onMouseDown, true)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
  window.removeEventListener('click', onClickCapture, true)
  document.removeEventListener('mouseleave', onMouseLeave)
}

onMounted(() => {
  const query = window.matchMedia(NARROW_QUERY)
  const sync = () => {
    narrow.value = query.matches
  }
  query.addEventListener('change', sync)
  unsubscribe = () => query.removeEventListener('change', sync)

  window.addEventListener('resize', reclamp)
  stopResize = () => window.removeEventListener('resize', reclamp)

  bindMouse()
})

onBeforeUnmount(() => {
  disposed = true
  unsubscribe?.()
  stopResize?.()
  unbindMouse()
  if (maskTimer !== undefined) window.clearInterval(maskTimer)
  setCursor('')
})

// 打开时才加载; 关闭时只是隐藏 canvas, 不销毁 —— 运行时持有它的 WebGL 上下文,
// 反复销毁重建会消耗浏览器的 WebGL 上下文配额
watch(visible, (on) => {
  if (maskTimer !== undefined) {
    window.clearInterval(maskTimer)
    maskTimer = undefined
  }
  if (!on) return
  // 关掉看板娘期间窗口可能变小过, 重新展示时先把浮层拉回视口
  reclamp()
  // 轮廓会随闲置动作缓慢变化, 隔一段时间重新取一张
  maskTimer = window.setInterval(captureMask, MASK_REFRESH_MS)
  whenIdle(() => {
    if (!disposed) void show()
  })
}, { immediate: true })

watch(() => kb.modelId, switchModel)
</script>

<template>
  <div ref="root" class="kanbanniang" :class="{ 'is-hidden': !visible }" :style="posStyle">
    <canvas
      :id="CANVAS_ID"
      class="kanbanniang-canvas"
      :width="canvasSize.width"
      :height="canvasSize.height"
      :style="canvasStyle"
      aria-hidden="true"
    />
  </div>
</template>

<style scoped>
.kanbanniang {
  position: fixed;
  left: 0;
  bottom: 0;
  /* 低于顶栏(100)与 Element Plus 的浮层(2000+), 高于正文 */
  z-index: 90;
  line-height: 0;
  /* 运行时在 window 上监听鼠标, 不需要命中 canvas: 不让这块浮层挡住正文的点击与选区 */
  pointer-events: none;
}

.kanbanniang.is-hidden {
  display: none;
}

.kanbanniang-canvas {
  display: block;
}
</style>
