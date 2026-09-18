<script setup lang="ts">
import { ref } from 'vue'
import { logApi } from '@/api'
import type { OperationLog } from '@/types'
import { usePagedList } from '@/composables/usePagedList'

const moduleFilter = ref('')
/** 列表分页与取数; 换筛选条件时调 reset() 回到第 1 页 */
const { items: logs, total, page, pageSize, loading, reset } = usePagedList<OperationLog>({
  pageSize: 20,
  fetch: (page, pageSize) =>
    logApi.list({ page, page_size: pageSize, module: moduleFilter.value || undefined }),
})
</script>

<template>
  <div>
    <h2>操作日志</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <el-input
          v-model="moduleFilter"
          placeholder="按模块筛选(post/user/comment...)"
          clearable
          @keyup.enter="reset()"
          @clear="reset()"
        />
      </div>
    </div>

    <div class="card">
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
      />
    </div>
  </div>
</template>
