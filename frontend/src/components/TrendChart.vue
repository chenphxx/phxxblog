<script setup lang="ts">
import { computed } from 'vue'
import type { TrendPoint } from '@/types'

const props = defineProps<{
  points: TrendPoint[]
  type: 'line' | 'bar'
}>()

const W = 720
const H = 240
const PAD = { top: 16, right: 16, bottom: 28, left: 40 }

const maxValue = computed(() => Math.max(...props.points.map((p) => Math.max(p.pv, p.uv)), 1))

const innerW = W - PAD.left - PAD.right
const innerH = H - PAD.top - PAD.bottom

function x(index: number) {
  const n = Math.max(props.points.length - 1, 1)
  return PAD.left + (innerW * index) / n
}

function y(value: number) {
  return PAD.top + innerH - (innerH * value) / maxValue.value
}

const linePv = computed(() => props.points.map((p, i) => `${x(i)},${y(p.pv)}`).join(' '))
const lineUv = computed(() => props.points.map((p, i) => `${x(i)},${y(p.uv)}`).join(' '))

const xTicks = computed(() => {
  const n = Math.min(props.points.length, 8)
  const step = Math.floor(props.points.length / n) || 1
  return props.points.map((p, i) => ({ label: p.label, i })).filter((_, i) => i % step === 0)
})

const yTicks = computed(() => {
  const ticks = 4
  return Array.from({ length: ticks + 1 }, (_, i) => Math.round((maxValue.value * i) / ticks))
})

const barWidth = computed(() => Math.max(3, (innerW / props.points.length) * 0.32))
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="trend-svg" preserveAspectRatio="xMidYMid meet">
    <!-- 网格与 Y 轴 -->
    <line v-for="t in yTicks" :key="t" :x1="PAD.left" :x2="W - PAD.right" :y1="y(t)" :y2="y(t)" class="grid-line" />
    <text v-for="t in yTicks" :key="t" :x="PAD.left - 6" :y="y(t) + 4" class="axis-text" text-anchor="end">{{ t }}</text>

    <!-- X 轴标签 -->
    <text v-for="tick in xTicks" :key="tick.label" :x="x(tick.i)" :y="H - 8" class="axis-text" text-anchor="middle">
      {{ tick.label }}
    </text>

    <!-- 柱状图 -->
    <template v-if="type === 'bar'">
      <g v-for="(p, i) in points" :key="p.label">
        <rect
          :x="x(i) - barWidth"
          :y="y(p.pv)"
          :width="barWidth"
          :height="Math.max(innerH - y(p.pv) + PAD.top, 0)"
          class="bar bar-pv"
        >
          <title>{{ p.label }} PV: {{ p.pv }}</title>
        </rect>
        <rect
          :x="x(i)"
          :y="y(p.uv)"
          :width="barWidth"
          :height="Math.max(innerH - y(p.uv) + PAD.top, 0)"
          class="bar bar-uv"
        >
          <title>{{ p.label }} UV: {{ p.uv }}</title>
        </rect>
      </g>
    </template>

    <!-- 折线图 -->
    <template v-else>
      <polyline :points="linePv" class="line line-pv" fill="none" />
      <polyline :points="lineUv" class="line line-uv" fill="none" />
      <circle v-for="(p, i) in points" :key="p.label + 'pv'" :cx="x(i)" :cy="y(p.pv)" r="2.5" class="dot dot-pv">
        <title>{{ p.label }} PV: {{ p.pv }}</title>
      </circle>
      <circle v-for="(p, i) in points" :key="p.label + 'uv'" :cx="x(i)" :cy="y(p.uv)" r="2.5" class="dot dot-uv">
        <title>{{ p.label }} UV: {{ p.uv }}</title>
      </circle>
    </template>
  </svg>
</template>

<style scoped>
.trend-svg {
  width: 100%;
  height: auto;
}
.grid-line {
  stroke: var(--border);
  stroke-width: 0.5;
  stroke-dasharray: 3 3;
}
.axis-text {
  fill: var(--muted);
  font-size: 10px;
}
.bar-pv {
  fill: #0969da;
}
.bar-uv {
  fill: #54aeff;
}
.line-pv {
  stroke: #0969da;
  stroke-width: 2;
}
.line-uv {
  stroke: #54aeff;
  stroke-width: 2;
}
.dot-pv {
  fill: #0969da;
}
.dot-uv {
  fill: #54aeff;
}
</style>
