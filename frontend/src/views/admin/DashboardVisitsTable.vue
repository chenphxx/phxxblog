<script setup lang="ts">
import { ref, watch } from 'vue'
import { statsApi } from '@/api'
import type { VisitItem } from '@/types'
import ListPager from '@/components/ListPager.vue'

/**
 * @brief 仪表盘的访问记录区块
 *
 * 自带分页状态与取数; 首屏统一加载由页面通过 refresh() 触发,
 * 卡片上的"刷新"按钮同样回到第 1 页
 */
const visits = ref<VisitItem[]>([])
const visitsTotal = ref(0)
const visitsPage = ref(1)
const visitsPageSize = 10
const visitsLoading = ref(false)

async function loadVisits() {
  visitsLoading.value = true
  try {
    const data = await statsApi.visits({ page: visitsPage.value, page_size: visitsPageSize })
    visits.value = data.items
    visitsTotal.value = data.total
  } finally {
    visitsLoading.value = false
  }
}

/** 刷新访问记录: 回到第 1 页再取数(分页不变时 watch 不会触发) */
async function refreshVisits() {
  visitsPage.value = 1
  await loadVisits()
}

watch(visitsPage, loadVisits)

defineExpose({ refresh: refreshVisits })
</script>

<template>
  <div id="visits-section" class="card">
    <div class="trend-header">
      <h3 style="margin: 0">访问记录</h3>
      <el-button size="small" @click="refreshVisits()">刷新</el-button>
    </div>
    <el-table v-loading="visitsLoading" :data="visits" size="small">
      <el-table-column prop="visit_time" label="时间" width="150">
        <template #default="{ row }">{{ (row.visit_time || '').replace('T', ' ').slice(0, 16) }}</template>
      </el-table-column>
      <el-table-column prop="ip" label="IP" width="120" />
      <el-table-column prop="location" label="省市区" width="110" />
      <el-table-column label="设备" width="90">
        <template #default="{ row }">{{ row.device || '-' }}</template>
      </el-table-column>
      <el-table-column prop="browser" label="浏览器" width="90" />
      <el-table-column prop="os" label="系统" width="90" />
      <el-table-column label="文章" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">
          <router-link v-if="row.post_id" :to="`/post/${row.post_id}`">{{
            row.post_title || `#${row.post_id}`
          }}</router-link>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="referer" label="来源" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.referer || '-' }}</template>
      </el-table-column>
    </el-table>
    <ListPager v-model:page="visitsPage" :page-size="visitsPageSize" :total="visitsTotal" />
  </div>
</template>
