<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { postApi } from '@/api'
import type { PostItem } from '@/types'

const router = useRouter()
const posts = ref<PostItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const selected = ref<PostItem[]>([])

const STATUS_TEXT = ['草稿', '审核中', '已发布', '私密', '回收站']
const STATUS_TYPE: Record<number, string> = { 0: 'info', 1: 'warning', 2: 'success', 3: 'danger', 4: 'info' }

async function load() {
  loading.value = true
  try {
    const data = await postApi.adminList({ page: page.value, page_size: pageSize })
    posts.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function remove(post: PostItem) {
  await ElMessageBox.confirm(`确定删除《${post.title}》吗? 将移入回收站。`, '确认', { type: 'warning' })
  await postApi.trash(post.id)
  ElMessage.success('已移入回收站')
  load()
}

function onSelectionChange(rows: PostItem[]) {
  selected.value = rows
}

async function togglePrivate(post: PostItem) {
  const target = post.status === 2 ? 3 : 2
  await postApi.changeStatus(post.id, target)
  ElMessage.success(target === 3 ? '已设为私密(仅管理员可见)' : '已设为公开可见')
  load()
}

async function batchSetPrivate() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`将选中的 ${selected.value.length} 篇文章设为私密(仅管理员可见)吗?`, '确认', { type: 'warning' })
  for (const post of selected.value) {
    try {
      await postApi.changeStatus(post.id, 3)
    } catch {
      // 单篇失败继续处理其余文章
    }
  }
  ElMessage.success('批量设为私密完成')
  selected.value = []
  load()
}

async function batchTrash() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`将选中的 ${selected.value.length} 篇文章移入回收站吗?`, '确认', { type: 'warning' })
  for (const post of selected.value) {
    try {
      await postApi.trash(post.id)
    } catch {
      // 忽略单篇失败
    }
  }
  ElMessage.success('批量移入回收站完成')
  selected.value = []
  load()
}

async function batchForceDelete() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`彻底删除选中的 ${selected.value.length} 篇文章? 该操作不可恢复!`, '危险操作', {
    type: 'error',
    confirmButtonText: '彻底删除',
  })
  for (const post of selected.value) {
    try {
      await postApi.forceDelete(post.id)
    } catch {
      // 忽略单篇失败
    }
  }
  ElMessage.success('批量彻底删除完成')
  selected.value = []
  load()
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="mine-header">
      <h1 style="margin: 0">我的文章</h1>
      <el-button type="primary" @click="router.push('/write')">写文章</el-button>
    </div>

    <div class="card" style="margin-top: 16px">
      <div v-if="selected.length" class="batch-bar">
        <span class="muted">已选 {{ selected.length }} 篇</span>
        <el-button size="small" type="warning" @click="batchSetPrivate">设为私密</el-button>
        <el-button size="small" type="info" @click="batchTrash">移入回收站</el-button>
        <el-button size="small" type="danger" @click="batchForceDelete">彻底删除</el-button>
      </div>
      <el-table :data="posts" v-loading="loading" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link :to="`/write/${row.id}`">{{ row.title }}</router-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="STATUS_TYPE[row.status]">{{ STATUS_TEXT[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="views" label="阅读" width="80" />
        <el-table-column prop="likes_count" label="点赞" width="80" />
        <el-table-column label="更新时间" width="110">
          <template #default="{ row }">{{ row.updated_at.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <div class="op-row">
              <el-button v-if="row.status === 2 || row.status === 3" size="small" @click="router.push(`/post/${row.id}`)">查看</el-button>
              <el-button v-if="row.status === 2" size="small" type="warning" @click="togglePrivate(row)">私密</el-button>
              <el-button v-else-if="row.status === 3" size="small" type="success" @click="togglePrivate(row)">公开</el-button>
              <el-button size="small" type="primary" @click="router.push(`/write/${row.id}`)">编辑</el-button>
              <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && posts.length === 0" description="还没有文章, 点击右上角开始创作吧">
        <el-button type="primary" @click="router.push('/write')">写第一篇</el-button>
      </el-empty>
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
.mine-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
}
.op-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  white-space: nowrap;
}
.op-row .el-button {
  margin-left: 0;
}
</style>
