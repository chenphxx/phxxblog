<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { chronicleApi } from '@/api'
import ListPager from '@/components/ListPager.vue'
import { usePagedList } from '@/composables/usePagedList'
import type { ChronicleItem } from '@/types'
import { formatDateTime } from '@/utils/datetime'

const router = useRouter()
const keyword = ref('')

const { items, total, page, pageSize, loading, load, reset } = usePagedList<ChronicleItem>({
  fetch: (currentPage, currentPageSize) =>
    chronicleApi.list({
      page: currentPage,
      page_size: currentPageSize,
      keyword: keyword.value.trim() || undefined,
    }),
  pageSize: 12,
})

async function remove(item: ChronicleItem) {
  await ElMessageBox.confirm(`确定删除《${item.title}》吗? 该操作不可恢复。`, '删除纪事', {
    type: 'warning',
    confirmButtonText: '删除',
  })
  await chronicleApi.remove(item.id)
  ElMessage.success('已删除')
  load()
}
</script>

<template>
  <div>
    <h2>互联网纪事管理</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <span class="muted">共 {{ total }} 则纪事</span>
      </div>
      <div class="admin-toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索标题或概览" clearable @keyup.enter="reset()" @clear="reset()" />
        <el-button @click="reset()">搜索</el-button>
        <el-button type="primary" @click="router.push('/admin/chronicles/new')">新增纪事</el-button>
      </div>
    </div>

    <div class="card">
      <el-table v-loading="loading" :data="items">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="封面" width="112">
          <template #default="{ row }">
            <div class="cover-thumb">
              <img v-if="row.cover_image" :src="row.cover_image" :alt="row.title" />
              <span v-else>纪</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="190" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link :to="`/admin/chronicles/${row.id}/edit`">{{ row.title }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="概览" min-width="260" show-overflow-tooltip />
        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="op-row">
              <el-button size="small" @click="router.push(`/admin/chronicles/${row.id}/edit`)">编辑</el-button>
              <el-button size="small" type="danger" @click="remove(row as ChronicleItem)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <ListPager v-model:page="page" :page-size="pageSize" :total="total" />
    </div>
  </div>
</template>

<style scoped>
.cover-thumb {
  display: flex;
  width: 82px;
  height: 52px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 8px;
  background: var(--primary-weak);
  color: var(--primary-strong);
  font-family: serif;
  font-size: 24px;
}

.cover-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.op-row {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.op-row :deep(.el-button + .el-button) {
  margin-left: 0;
}
</style>
