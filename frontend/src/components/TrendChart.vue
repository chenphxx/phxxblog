<script setup lang="ts">
/**
 * 访问趋势图(纯 SVG, 不依赖第三方图表库)。
 *
 * 与旧实现的区别:
 *   1. 配色改用主题令牌(PV = --primary, UV = --grad-to), 换主题时线条与图例同步;
 *   2. 宽度由 ResizeObserver 实测, 不再用固定 viewBox 等比放大(宽屏下坐标文字会跟着变大);
 *   3. PV 画成带渐变填充的面积, UV 用虚线区分 —— 序列不只用颜色区分, 色觉障碍下也能分辨;
 *   4. 悬停/键盘左右键出现十字准线与数值浮层, 取代原生 <title> 的系统提示框。
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { TrendPoint } from '@/types'

const props = defineProps<{
  points: TrendPoint[]
  type: 'line' | 'bar'
}>()

/** 图表高度固定; 宽度实测容器, 因此这里不再需要 preserveAspectRatio 缩放 */
const H = 260
const PAD = { top: 18, right: 18, bottom: 28, left: 46 }
const Y_TICKS = 4

/** 渐变 id 必须唯一, 否则同页多个趋势图会互相覆盖填充色 */
let gradientSeq = 0
const gradientId = `trend-area-${++gradientSeq}`

const wrap = ref<HTMLElement | null>(null)
const width = ref(720)
let observer: ResizeObserver | null = null

onMounted(() => {
  if (typeof ResizeObserver === 'undefined' || !wrap.value) return
  observer = new ResizeObserver((entries) => {
    const measured = Math.round(entries[0].contentRect.width)
    if (measured > 0) width.value = measured
  })
  observer.observe(wrap.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})

const W = computed(() => Math.max(width.value, 320))
const innerW = computed(() => W.value - PAD.left - PAD.right)
const innerH = H - PAD.top - PAD.bottom
const baseY = PAD.top + innerH

/** 全部为 0 时不画线, 只给空状态文案 */
const isEmpty = computed(() => props.points.every((p) => p.pv === 0 && p.uv === 0))

/**
 * 取一个"好看"的 Y 轴上限: 保证上限能被 4 整除, 四个刻度都是整数。
 * 直接用原始最大值会出现 2.5 / 7.5 这类刻度, 原始值取整又会丢掉顶部留白。
 */
function niceMax(raw: number): number {
  if (raw <= Y_TICKS) return Y_TICKS
  for (let decade = 1; decade <= 1e9; decade *= 10) {
    for (const step of [1, 2, 3, 4, 5, 6, 8, 10]) {
      const candidate = step * decade
      if (candidate * Y_TICKS >= raw) return candidate * Y_TICKS
    }
  }
  return Math.ceil(raw / Y_TICKS) * Y_TICKS
}

const maxValue = computed(() => niceMax(Math.max(...props.points.map((p) => Math.max(p.pv, p.uv)), 0)))

/** 点间距: 只有一个点时不除零, 直接放在绘图区中间 */
const step = computed(() => (props.points.length > 1 ? innerW.value / (props.points.length - 1) : 0))

function x(index: number): number {
  if (props.points.length <= 1) return PAD.left + innerW.value / 2
  return PAD.left + step.value * index
}

function y(value: number): number {
  const ratio = maxValue.value > 0 ? value / maxValue.value : 0
  return baseY - innerH * ratio
}

const yTicks = computed(() =>
  Array.from({ length: Y_TICKS + 1 }, (_, i) => {
    const value = (maxValue.value * i) / Y_TICKS
    return { value, y: y(value) }
  }),
)

/** X 轴最多显示 8 个标签, 按数据量自动抽稀, 并保证末尾一定有标签 */
const xTicks = computed(() => {
  const total = props.points.length
  if (!total) return []
  const stepIndex = Math.max(1, Math.ceil(total / 8))
  const ticks = props.points
    .map((p, i) => ({ label: p.label, i }))
    .filter((tick) => tick.i % stepIndex === 0)
  const last = total - 1
  if (ticks[ticks.length - 1]?.i !== last) ticks.push({ label: props.points[last].label, i: last })
  return ticks
})

const linePv = computed(() => props.points.map((p, i) => `${x(i)},${y(p.pv)}`).join(' '))
const lineUv = computed(() => props.points.map((p, i) => `${x(i)},${y(p.uv)}`).join(' '))

/** 面积路径: 折线两端落到基线上闭合成面 */
const areaPv = computed(() => {
  if (!props.points.length) return ''
  const line = props.points.map((p, i) => `L ${x(i)},${y(p.pv)}`).join(' ')
  return `M ${x(0)},${baseY} ${line} L ${x(props.points.length - 1)},${baseY} Z`
})

/*
 * 柱宽与柱间距都按分组宽度等比收缩: 数据点很多(如自定义 365 天)时,
 * 固定 2px 间距会让相邻两组的柱子叠在一起。
 */
const barWidth = computed(() => Math.max(1, Math.min(14, (innerW.value / Math.max(props.points.length, 1)) * 0.34)))

const barGap = computed(() => Math.min(1.5, (innerW.value / Math.max(props.points.length, 1)) * 0.06))

/* ---------- 悬停/键盘交互 ---------- */
const hoverIndex = ref<number | null>(null)

const hovered = computed(() => (hoverIndex.value === null ? null : props.points[hoverIndex.value] ?? null))

/** 浮层高度上限(标签 + PV/UV/阅读 四行)与它到数据点的间距, 用于判断上方是否放得下 */
const TOOLTIP_HEIGHT = 96
const TOOLTIP_GAP = 12

/** 浮层横向位置: 贴边时向内收, 避免超出卡片 */
const tooltipLeft = computed(() => {
  if (hoverIndex.value === null) return 0
  return Math.min(Math.max(x(hoverIndex.value), 64), Math.max(W.value - 64, 64))
})

const pointY = computed(() =>
  hovered.value ? y(Math.max(hovered.value.pv, hovered.value.uv)) : 0,
)

/**
 * 数据点靠上(数值高)时把浮层画到点的下方。
 *
 * 容器纵向是 overflow: hidden(横向需要能滚动), 而浮层默认画在数据点上方:
 * 指向数值最高的那几个点时, 浮层上半部分会被容器顶部裁掉(只剩最后一行可见)。
 * 上方放不下就翻到下方, 两种摆法在 260px 高的图里都不会被裁。
 */
const tooltipBelow = computed(() => pointY.value - TOOLTIP_GAP < TOOLTIP_HEIGHT)

const tooltipTop = computed(() => {
  if (!hovered.value) return 0
  return tooltipBelow.value ? pointY.value + TOOLTIP_GAP : pointY.value - TOOLTIP_GAP
})

function onPointerMove(event: PointerEvent) {
  const total = props.points.length
  if (!total) return
  // 监听挂在 <svg> 上, 因此 currentTarget 就是 SVG 根节点(它的 ownerSVGElement 是 null)
  const rect = (event.currentTarget as SVGSVGElement).getBoundingClientRect()
  const offset = event.clientX - rect.left - PAD.left
  const index = total > 1 ? Math.round(offset / step.value) : 0
  hoverIndex.value = Math.min(Math.max(index, 0), total - 1)
}

function moveHover(delta: number) {
  const total = props.points.length
  if (!total) return
  const next = (hoverIndex.value ?? total - 1) + delta
  hoverIndex.value = Math.min(Math.max(next, 0), total - 1)
}

const chartLabel = computed(() => {
  if (!props.points.length) return '访问趋势图(暂无数据)'
  const first = props.points[0]
  const last = props.points[props.points.length - 1]
  const pv = props.points.reduce((sum, p) => sum + p.pv, 0)
  return `访问趋势图: ${first.label} 至 ${last.label}, 累计 PV ${pv}`
})
</script>

<template>
  <div ref="wrap" class="trend-chart">
    <svg
      :width="W"
      :height="H"
      :viewBox="`0 0 ${W} ${H}`"
      class="trend-svg"
      role="img"
      tabindex="0"
      :aria-label="chartLabel"
      @pointermove="onPointerMove"
      @pointerleave="hoverIndex = null"
      @keydown.left.prevent="moveHover(-1)"
      @keydown.right.prevent="moveHover(1)"
      @keydown.esc="hoverIndex = null"
      @blur="hoverIndex = null"
    >
      <defs>
        <linearGradient :id="gradientId" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" class="area-stop-from" />
          <stop offset="100%" class="area-stop-to" />
        </linearGradient>
      </defs>

      <!-- 网格与 Y 轴刻度 -->
      <g>
        <line
          v-for="tick in yTicks"
          :key="`grid-${tick.value}`"
          :x1="PAD.left"
          :x2="W - PAD.right"
          :y1="tick.y"
          :y2="tick.y"
          class="grid-line"
          :class="{ 'is-base': tick.value === 0 }"
        />
        <text
          v-for="tick in yTicks"
          :key="`ylabel-${tick.value}`"
          :x="PAD.left - 8"
          :y="tick.y + 4"
          class="axis-text"
          text-anchor="end"
        >
          {{ tick.value }}
        </text>
      </g>

      <!-- X 轴刻度 -->
      <text
        v-for="tick in xTicks"
        :key="`xlabel-${tick.i}`"
        :x="x(tick.i)"
        :y="H - 8"
        class="axis-text"
        text-anchor="middle"
      >
        {{ tick.label }}
      </text>

      <template v-if="!isEmpty">
        <!-- 柱状图 -->
        <template v-if="type === 'bar'">
          <g v-for="(p, i) in points" :key="`bar-${p.label}-${i}`" :class="{ 'is-dim': hoverIndex !== null && hoverIndex !== i }">
            <rect
              :x="x(i) - barWidth - barGap"
              :y="y(p.pv)"
              :width="barWidth"
              :height="Math.max(baseY - y(p.pv), 0)"
              rx="2"
              class="bar bar-pv"
            />
            <rect
              :x="x(i) + barGap"
              :y="y(p.uv)"
              :width="barWidth"
              :height="Math.max(baseY - y(p.uv), 0)"
              rx="2"
              class="bar bar-uv"
            />
          </g>
        </template>

        <!-- 折线图: PV 面积 + UV 虚线 -->
        <template v-else>
          <path :d="areaPv" :fill="`url(#${gradientId})`" stroke="none" />
          <polyline :points="linePv" class="line line-pv" fill="none" />
          <polyline :points="lineUv" class="line line-uv" fill="none" />
        </template>
      </template>

      <!-- 悬停: 十字准线 + 数值锚点 -->
      <g v-if="hovered && hoverIndex !== null" class="cursor">
        <line :x1="x(hoverIndex)" :x2="x(hoverIndex)" :y1="PAD.top" :y2="baseY" class="cursor-line" />
        <circle v-if="type === 'line'" :cx="x(hoverIndex)" :cy="y(hovered.pv)" r="4" class="cursor-dot dot-pv" />
        <circle v-if="type === 'line'" :cx="x(hoverIndex)" :cy="y(hovered.uv)" r="3.5" class="cursor-dot dot-uv" />
      </g>

      <!-- 最后一个数据点: 当前锚点 -->
      <circle
        v-if="!isEmpty && type === 'line'"
        :cx="x(points.length - 1)"
        :cy="y(points[points.length - 1].pv)"
        r="3.5"
        class="anchor-dot"
      />

      <text v-if="isEmpty" :x="W / 2" :y="PAD.top + innerH / 2" class="empty-text" text-anchor="middle">
        暂无访问数据
      </text>
    </svg>

    <!-- 数值浮层用 HTML 而不是 SVG <text>, 便于用主题令牌排版且不受坐标系影响 -->
    <div
      v-if="hovered"
      class="chart-tooltip"
      :class="{ 'is-below': tooltipBelow }"
      :style="{ left: `${tooltipLeft}px`, top: `${tooltipTop}px` }"
    >
      <div class="tooltip-label">{{ hovered.label }}</div>
      <div class="tooltip-row"><i class="swatch swatch-pv" />PV <b>{{ hovered.pv }}</b></div>
      <div class="tooltip-row"><i class="swatch swatch-uv" />UV <b>{{ hovered.uv }}</b></div>
      <div v-if="hovered.post_views" class="tooltip-row"><i class="swatch swatch-post" />阅读 <b>{{ hovered.post_views }}</b></div>
    </div>
  </div>
</template>

<style scoped>
/* 序列色统一取自主题令牌: PV 用主色, UV 用主题渐变的末端色, 与图例同源 */
.trend-chart {
  position: relative;
  width: 100%;
  /* 窄屏(容器不足 320px)时横向滚动, 而不是压缩 SVG —— 压缩会让坐标与鼠标位置对不上 */
  overflow-x: auto;
  overflow-y: hidden;
  --series-pv: var(--primary);
  --series-uv: var(--grad-to);
}

.trend-svg {
  display: block;
  outline: none;
}

.trend-svg:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

.grid-line {
  stroke: var(--border);
  stroke-width: 1;
  stroke-dasharray: 3 4;
}

.grid-line.is-base {
  stroke: var(--border-strong);
  stroke-dasharray: none;
}

.axis-text {
  fill: var(--muted);
  font-family: var(--font-mono);
  font-size: 11px;
}

.bar {
  transition: opacity var(--dur) var(--ease);
}

.bar-pv {
  fill: var(--series-pv);
}

.bar-uv {
  fill: var(--series-uv);
}

.is-dim {
  opacity: 0.45;
}

.line {
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.line-pv {
  stroke: var(--series-pv);
}

/* UV 用虚线: 不只靠颜色区分两条序列 */
.line-uv {
  stroke: var(--series-uv);
  stroke-width: 1.8;
  stroke-dasharray: 5 4;
}

.area-stop-from {
  stop-color: var(--series-pv);
  stop-opacity: 0.22;
}

.area-stop-to {
  stop-color: var(--series-pv);
  stop-opacity: 0.02;
}

.cursor-line {
  stroke: var(--border-strong);
  stroke-width: 1;
}

.cursor-dot {
  stroke: var(--card-bg);
  stroke-width: 2;
}

.dot-pv {
  fill: var(--series-pv);
}

.dot-uv {
  fill: var(--series-uv);
}

.anchor-dot {
  fill: var(--series-pv);
  stroke: var(--card-bg);
  stroke-width: 2;
  animation: trend-pulse 2.4s ease-in-out infinite;
}

@keyframes trend-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.45;
  }
}

.empty-text {
  fill: var(--muted);
  font-size: 13px;
}

.chart-tooltip {
  position: absolute;
  z-index: 2;
  transform: translate(-50%, -100%);
  padding: 8px 10px;
  min-width: 108px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--card-bg);
  box-shadow: var(--shadow-hover);
  font-size: 12px;
  line-height: 1.6;
  pointer-events: none;
  white-space: nowrap;
}

/* 画在数据点下方时不向上偏移(默认是 translate(-50%, -100%) 贴在点上方) */
.chart-tooltip.is-below {
  transform: translate(-50%, 0);
}

.tooltip-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted);
  margin-bottom: 2px;
}

.tooltip-row {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
}

.tooltip-row b {
  margin-left: auto;
  color: var(--text);
  font-family: var(--font-mono);
}

.swatch {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.swatch-pv {
  background: var(--series-pv);
}

.swatch-uv {
  background: var(--series-uv);
}

.swatch-post {
  background: var(--border-strong);
}

@media (prefers-reduced-motion: reduce) {
  .anchor-dot {
    animation: none;
  }
}
</style>
