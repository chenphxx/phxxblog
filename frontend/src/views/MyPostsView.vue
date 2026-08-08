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

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="mine-header">
      <h1 style="margin: 0">我的文章</h1>
      <el-button type="primary" @click="router.push('/write')">写文章</el-button>
    </div>

    <div class="card" style="margin-top: 16px">
      <el-table :data="posts" v-loading="loading">
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
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button v-if="row.status === 2" size="small" @click="router.push(`/post/${row.id}`)">查看</el-button>
            <el-button size="small" type="primary" @click="router.push(`/write/${row.id}`)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
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
</style>
