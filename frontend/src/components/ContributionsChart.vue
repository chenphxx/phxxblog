<script setup lang="ts">
import { computed } from 'vue'
import type { ContributionPoint } from '@/types'

const props = defineProps<{
  points: ContributionPoint[]
  years: number[]
  year: number | null
}>()
const emit = defineEmits<{ (e: 'update:year', year: number | null): void }>()

const CELL = 11
const GAP = 3
const WEEKDAY_LABELS = ['一', '三', '五']

const countMap = computed(() => {
  const map = new Map<string, number>()
  for (const point of props.points) {
    map.set(point.date, point.count)
  }
  return map
})

/** 起始日期对齐到周一(GitHub 布局) */
const gridStart = computed(() => {
  const first = props.points.length ? new Date(props.points[0].date + 'T00:00:00') : new Date()
  const day = first.getDay() // 0=周日
  const offset = day === 0 ? -6 : 1 - day
  first.setDate(first.getDate() + offset)
  return first
})

/** 周数: 需包含周一对齐的偏移, 否则尾部数据会被裁掉 */
const weeks = computed(() => {
  if (!props.points.length) return 0
  const last = new Date(props.points[props.points.length - 1].date + 'T00:00:00')
  const days = Math.round((last.getTime() - gridStart.value.getTime()) / 86400000) + 1
  return Math.ceil(days / 7)
})

const gridDates = computed(() => {
  const dates: { date: string; count: number }[] = []
  for (let i = 0; i < weeks.value * 7; i++) {
    const d = new Date(gridStart.value)
    d.setDate(d.getDate() + i)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    dates.push({ date: key, count: countMap.value.get(key) || 0 })
  }
  return dates
})

/** 月份标签(在月份切换的周列上方) */
const monthLabels = computed(() => {
  const labels: { x: number; text: string }[] = []
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  let lastMonth = -1
  for (let i = 0; i < gridDates.value.length; i++) {
    const month = Number(gridDates.value[i].date.slice(5, 7))
    if (month !== lastMonth) {
      const col = Math.floor(i / 7)
      labels.push({ x: col * (CELL + GAP), text: MONTHS[month - 1] })
      lastMonth = month
    }
  }
  return labels
})

function color(count: number): string {
  if (count <= 0) return 'var(--cell-0, #ebedf0)'
  if (count <= 2) return 'var(--cell-1, #9be9a8)'
  if (count <= 5) return 'var(--cell-2, #40c463)'
  if (count <= 9) return 'var(--cell-3, #30a14e)'
  return 'var(--cell-4, #216e39)'
}
</script>

<template>
  <div class="contributions">
    <div class="contributions-header">
      <el-select
        :model-value="year"
        size="small"
        style="width: 130px"
        placeholder="筛选年份"
        @update:model-value="emit('update:year', ($event as number) || null)"
      >
        <el-option label="近一年" :value="null" />
        <el-option v-for="y in years" :key="y" :label="`${y} 年`" :value="y" />
      </el-select>
    </div>

    <svg :width="WEEKDAY_LABELS.length * 8 + weeks * (CELL + GAP)" :height="7 * (CELL + GAP) + 18">
      <!-- 星期标签 -->
      <text v-for="(label, index) in WEEKDAY_LABELS" :key="label" :x="2" :y="18 + index * 2 * (CELL + GAP) + 8" class="weekday-text">
        {{ label }}
      </text>

      <!-- 月份标签 -->
      <text
        v-for="label in monthLabels"
        :key="label.x"
        :x="14 + label.x"
        :y="10"
        class="month-text"
      >
        {{ label.text }}
      </text>

      <!-- 贡献格子 -->
      <g v-for="(cell, i) in gridDates" :key="cell.date">
        <rect
          :x="14 + Math.floor(i / 7) * (CELL + GAP)"
          :y="18 + (i % 7) * (CELL + GAP)"
          :width="CELL"
          :height="CELL"
          rx="2"
          :fill="color(cell.count)"
        >
          <title>{{ cell.date }}: {{ cell.count }} 次发布</title>
        </rect>
      </g>
    </svg>

    <div class="legend muted">
      <span>少</span>
      <span v-for="level in 5" :key="level" :style="{ background: color([0, 2, 5, 9, 100][level - 1]) }" class="legend-cell" />
      <span>多</span>
    </div>
  </div>
</template>

<style scoped>
.contributions {
  overflow-x: auto;
}
.contributions-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.weekday-text,
.month-text {
  fill: var(--muted);
  font-size: 9px;
}
.legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
}
.legend-cell {
  width: 11px;
  height: 11px;
  border-radius: 2px;
}
</style>
