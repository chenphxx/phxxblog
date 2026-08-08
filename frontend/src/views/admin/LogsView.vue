<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { logApi } from '@/api'
import type { OperationLog } from '@/types'

const logs = ref<OperationLog[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const moduleFilter = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await logApi.list({
      page: page.value,
      page_size: pageSize,
      module: moduleFilter.value || undefined,
    })
    logs.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2 style="margin: 0">操作日志</h2>
      <el-input v-model="moduleFilter" placeholder="按模块筛选(post/user/comment...)" style="max-width: 240px" clearable @keyup.enter="page = 1; load()" @clear="page = 1; load()" />
    </div>

    <div class="card" style="margin-top: 16px">
      <el-table :data="logs" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="操作人" width="120">
          <template #default="{ row }">{{ row.username || '游客/系统' }}</template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="100" />
        <el-table-column prop="action" label="动作" width="120" />
        <el-table-column label="目标" min-width="120">
          <template #default="{ row }">
            <span v-if="row.target_type">{{ row.target_type }} #{{ row.target_id }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.detail ? JSON.stringify(row.detail) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="120" />
        <el-table-column prop="location" label="省市区" width="120">
          <template #default="{ row }">{{ row.location || '-' }}</template>
        </el-table-column>
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ row.created_at.replace('T', ' ') }}</template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        style="justify-content: center; margin-top: 16px"
        @current-change="load"
      />
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
