<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { statsApi } from '@/api'
import type { ContributionPoint } from '@/types'
import ContributionsChart from '@/components/ContributionsChart.vue'

/**
 * @brief 首页的"文章发布记录"区块
 *
 * 自己取数与切换年份, 取数期间只让本区块转圈: 这个接口要按 52 周聚合, 比首页的其它
 * 请求慢, 以前它没回来整页都停在加载态。
 */
const points = ref<ContributionPoint[]>([])
const year = ref<number | null>(null)
const loading = ref(false)

/** 可筛选年份(近 6 年) */
const years = computed(() => {
  const current = new Date().getFullYear()
  return Array.from({ length: 6 }, (_, i) => current - i)
})

/** @brief 按当前年份重新取记录; 也供首页在 keep-alive 重新激活时调用 */
async function refresh() {
  loading.value = true
  try {
    points.value = await statsApi.contributions({
      source: 'post',
      weeks: 52,
      year: year.value || undefined,
    })
  } catch {
    points.value = []
  } finally {
    loading.value = false
  }
}

watch(year, refresh)

onMounted(refresh)

defineExpose({ refresh })
</script>

<template>
  <section v-loading="loading" class="card section-card">
    <p class="eyebrow" style="margin-bottom: 12px">activity — 文章发布记录</p>
    <ContributionsChart :points="points" :years="years" :year="year" @update:year="year = $event" />
  </section>
</template>

<style scoped>
/* 取数期间给足占位高度, 避免区块从一条细线跳成完整热力图 */
.section-card {
  min-height: 150px;
}
</style>
