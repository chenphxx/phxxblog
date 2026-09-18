<script setup lang="ts">
import { postApi } from '@/api'
import type { PostItem } from '@/types'
import PostCard from '@/components/PostCard.vue'
import { usePagedList } from '@/composables/usePagedList'

const { items: posts, total, page, pageSize, loading } = usePagedList<PostItem>({
  fetch: (page, pageSize) => postApi.list({ page, page_size: pageSize }),
})
</script>

<template>
  <div class="page-container">
    <div class="posts-header">
      <div>
        <p class="eyebrow" style="margin: 0 0 4px">posts — 全部文章</p>
        <h1 style="margin: 0">全部文章</h1>
      </div>
      <span class="count-label">共 {{ total }} 篇</span>
    </div>

    <div v-loading="loading" style="margin-top: 16px; min-height: 200px">
      <PostCard v-for="post in posts" :key="post.id" :post="post" />
      <el-empty v-if="!loading && posts.length === 0" description="暂无文章" />
      <div v-if="total > pageSize" class="pagination-row">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, total"
          background
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.posts-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.count-label {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
}
.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
