<script setup lang="ts">
import { postApi } from '@/api'
import type { PostItem } from '@/types'
import PostCard from '@/components/PostCard.vue'
import ListPager from '@/components/ListPager.vue'
import { usePagedList } from '@/composables/usePagedList'

const {
  items: posts,
  total,
  page,
  pageSize,
  loading,
} = usePagedList<PostItem>({
  fetch: (page, pageSize) => postApi.list({ page, page_size: pageSize }),
})
</script>

<template>
  <div class="page-container">
    <div class="page-head">
      <div>
        <h1 class="page-title">全部文章</h1>
        <p class="page-subtitle">按发布时间排序, 每页 10 篇</p>
      </div>
      <span class="count-label num">共 {{ total }} 篇</span>
    </div>

    <section class="panel">
      <div v-loading="loading" class="posts-list">
        <PostCard v-for="post in posts" :key="post.id" :post="post" />
        <el-empty v-if="!loading && posts.length === 0" description="暂无文章" />
      </div>
      <ListPager v-model:page="page" :page-size="pageSize" :total="total" />
    </section>
  </div>
</template>

<style scoped>
.count-label {
  font-size: 13px;
  color: var(--muted);
}
.posts-list {
  min-height: 200px;
}
</style>
