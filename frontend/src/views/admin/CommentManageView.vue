<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { commentApi } from '@/api'
import type { CommentItem } from '@/types'

const statusFilter = ref<number | undefined>(undefined)
const comments = ref<CommentItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)

const STATUS_TEXT: Record<number, string> = { 1: '正常', 0: '隐藏', 2: '回收站' }
const STATUS_TYPE: Record<number, string> = { 1: 'success', 0: 'warning', 2: 'info' }

async function load() {
  loading.value = true
  try {
    const data = await commentApi.adminList({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value,
    })
    comments.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function setStatus(comment: CommentItem, status: number) {
  await commentApi.updateStatus(comment.id, status)
  ElMessage.success('状态已更新')
  load()
}

async function remove(comment: CommentItem) {
  await ElMessageBox.confirm('确定删除该评论及其回复吗?', '确认', { type: 'warning' })
  await commentApi.remove(comment.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2 style="margin: 0">评论管理</h2>
      <el-radio-group v-model="statusFilter" @change="page = 1; load()">
        <el-radio-button :value="undefined">全部</el-radio-button>
        <el-radio-button :value="1">正常</el-radio-button>
        <el-radio-button :value="0">隐藏</el-radio-button>
        <el-radio-button :value="2">回收站</el-radio-button>
      </el-radio-group>
    </div>

    <div class="card" style="margin-top: 16px">
      <el-table :data="comments" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="评论人" width="120">
          <template #default="{ row }">
            {{ row.author_name || '匿名' }}
            <div class="muted" style="font-size: 12px">{{ row.location || '未知地区' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="130">
          <template #default="{ row }">
            <span class="muted" style="font-size: 12px">{{ row.ip || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="220" show-overflow-tooltip />
        <el-table-column prop="post_id" label="文章ID" width="90" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="STATUS_TYPE[row.status]">{{ STATUS_TEXT[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="110">
          <template #default="{ row }">{{ row.created_at.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button v-if="row.status !== 1" size="small" type="success" @click="setStatus(row, 1)">显示</el-button>
            <el-button v-if="row.status === 1" size="small" type="warning" @click="setStatus(row, 0)">隐藏</el-button>
            <el-button v-if="row.status !== 2" size="small" type="info" @click="setStatus(row, 2)">回收站</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
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
