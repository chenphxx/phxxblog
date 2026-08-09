<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { postApi } from '@/api'
import type { PostItem } from '@/types'

const router = useRouter()
const statusFilter = ref<number | undefined>(undefined)
const keyword = ref('')
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
    const data = await postApi.adminList({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value,
      keyword: keyword.value || undefined,
    })
    posts.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function changeStatus(post: PostItem, status: number, message: string) {
  await ElMessageBox.confirm(`确定${message}《${post.title}》吗?`, '确认', { type: 'warning' })
  await postApi.changeStatus(post.id, status)
  ElMessage.success('操作成功')
  load()
}

async function trash(post: PostItem) {
  await ElMessageBox.confirm(`确定删除《${post.title}》吗? 将移入回收站。`, '确认', { type: 'warning' })
  await postApi.trash(post.id)
  ElMessage.success('已移入回收站')
  load()
}

async function restore(post: PostItem) {
  await postApi.restore(post.id)
  ElMessage.success('已恢复')
  load()
}

async function forceDelete(post: PostItem) {
  await ElMessageBox.confirm(`彻底删除《${post.title}》? 该操作不可恢复!`, '危险操作', {
    type: 'error',
    confirmButtonText: '彻底删除',
  })
  await postApi.forceDelete(post.id)
  ElMessage.success('已彻底删除')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2 style="margin: 0">文章管理</h2>
      <el-button type="primary" @click="router.push('/admin/posts/new')">新建文章</el-button>
    </div>

    <div class="toolbar" style="margin-top: 12px">
      <el-radio-group v-model="statusFilter" @change="page = 1; load()">
        <el-radio-button :value="undefined">全部</el-radio-button>
        <el-radio-button v-for="(text, index) in STATUS_TEXT" :key="index" :value="index">{{ text }}</el-radio-button>
      </el-radio-group>
      <el-input v-model="keyword" placeholder="搜索标题" style="max-width: 220px" clearable @keyup.enter="page = 1; load()" @clear="page = 1; load()" />
      <el-button @click="page = 1; load()">搜索</el-button>
    </div>

    <div class="card" style="margin-top: 16px">
      <el-table :data="posts" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link :to="row.status === 2 || row.status === 3 ? `/post/${row.id}` : `/admin/posts/${row.id}/edit`">
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="STATUS_TYPE[row.status]">{{ STATUS_TEXT[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="views" label="阅读" width="70" />
        <el-table-column prop="likes_count" label="点赞" width="70" />
        <el-table-column label="作者" width="100">
          <template #default="{ row }">{{ row.author?.nickname || row.author?.username || '-' }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="110">
          <template #default="{ row }">{{ row.updated_at.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="router.push(`/admin/posts/${row.id}/edit`)">编辑</el-button>
            <el-button v-if="row.status === 4" size="small" type="success" @click="restore(row)">恢复</el-button>
            <el-button v-if="row.status === 4" size="small" type="danger" @click="forceDelete(row)">彻底删除</el-button>
            <template v-else>
              <el-button v-if="row.status !== 2" size="small" type="primary" @click="changeStatus(row, 2, '发布')">发布</el-button>
              <el-button v-if="row.status === 0" size="small" type="warning" @click="changeStatus(row, 1, '提交审核')">审核</el-button>
              <el-button size="small" type="danger" @click="trash(row)">删除</el-button>
            </template>
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
  gap: 12px;
  justify-content: space-between;
  flex-wrap: wrap;
}
</style>
