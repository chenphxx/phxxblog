<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { commentApi } from '@/api'
import type { CommentItem } from '@/types'
import { usePagedList } from '@/composables/usePagedList'

const statusFilter = ref<number | undefined>(undefined)
/** 列表分页与取数; 换筛选条件时调 reset() 回到第 1 页 */
const { items: comments, total, page, pageSize, loading, load, reset } = usePagedList<CommentItem>({
  fetch: (page, pageSize) =>
    commentApi.adminList({ page, page_size: pageSize, status: statusFilter.value }),
})

const STATUS_TEXT: Record<number, string> = { 1: '正常', 0: '隐藏', 2: '回收站' }
/**
 * 状态 -> el-tag 的 type。
 * 用字面量联合而不是 `Record<number, string>`: el-tag 的 type 只接受
 * 'primary' | 'success' | 'warning' | 'info' | 'danger', 宽泛的 string 会在
 * 模板类型检查时报错(按需引入后组件有了精确类型, 这类问题会暴露出来)。
 */
type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'
const STATUS_TYPE: Record<number, TagType> = { 1: 'success', 0: 'warning', 2: 'info' }

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
</script>

<template>
  <div>
    <h2>评论管理</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <el-radio-group v-model="statusFilter" @change="reset()">
          <el-radio-button :value="undefined">全部</el-radio-button>
          <el-radio-button :value="1">正常</el-radio-button>
          <el-radio-button :value="0">隐藏</el-radio-button>
          <el-radio-button :value="2">回收站</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="card">
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
        <el-table-column prop="content" label="内容" min-width="220">
          <template #default="{ row }">
            <!-- 用 router-link 而不是裸 <a> + click: 前者可 Tab 聚焦、可回车触发,
                 并且语义上就是"链接"(屏幕阅读器不会把它当普通文本) -->
            <router-link
              class="comment-link"
              :to="`/post/${row.post_id}`"
              :title="`查看文章 #${row.post_id}`"
            >
              {{ row.content }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="post_id" label="文章ID" width="90">
          <template #default="{ row }">
            <router-link class="comment-link" :to="`/post/${row.post_id}`" :title="`查看文章 #${row.post_id}`">
              #{{ row.post_id }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="STATUS_TYPE[row.status]">{{ STATUS_TEXT[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="110">
          <template #default="{ row }">{{ row.created_at.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <div class="op-row">
              <!-- el-table 插槽的 row 是 DefaultRow, 显式断言成实际行类型 -->
              <el-button v-if="row.status !== 1" size="small" type="success" @click="setStatus(row as CommentItem, 1)">显示</el-button>
              <el-button v-if="row.status === 1" size="small" type="warning" @click="setStatus(row as CommentItem, 0)">隐藏</el-button>
              <el-button v-if="row.status !== 2" size="small" type="info" @click="setStatus(row as CommentItem, 2)">回收站</el-button>
              <el-button size="small" type="danger" @click="remove(row as CommentItem)">删除</el-button>
            </div>
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
      />
    </div>
  </div>
</template>

<style scoped>
.comment-link {
  color: var(--text);
  cursor: pointer;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.comment-link:hover {
  color: var(--primary);
  text-decoration: underline;
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
