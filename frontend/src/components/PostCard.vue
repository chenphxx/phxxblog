<script setup lang="ts">
import { View, Star } from '@element-plus/icons-vue'
import type { PostItem } from '@/types'

defineProps<{ post: PostItem }>()

const STATUS_TEXT: Record<number, string> = {
  0: '草稿',
  1: '审核中',
  2: '已发布',
  3: '私密',
  4: '回收站',
}
</script>

<template>
  <article class="card post-card">
    <h2 class="post-title">
      <router-link :to="`/post/${post.id}`">{{ post.title }}</router-link>
      <el-tag v-if="post.status !== 2" size="small" type="warning" class="status-tag">
        {{ STATUS_TEXT[post.status] }}
      </el-tag>
    </h2>
    <p v-if="post.summary" class="post-summary muted">{{ post.summary }}</p>
    <div class="post-meta muted">
      <span>{{ post.author?.nickname || post.author?.username || '匿名' }}</span>
      <span>· {{ (post.published_at || post.created_at).slice(0, 10) }}</span>
      <router-link v-if="post.category" :to="`/search?category=${post.category.id}`">
        <el-tag size="small" effect="plain">{{ post.category.name }}</el-tag>
      </router-link>
      <el-tag v-for="tag in post.tags" :key="tag.id" size="small" type="info" effect="plain">
        #{{ tag.name }}
      </el-tag>
      <span class="post-stats">
        <el-icon><View /></el-icon> {{ post.views }}
        <el-icon><Star /></el-icon> {{ post.likes_count }}
      </span>
    </div>
  </article>
</template>

<style scoped>
.post-card {
  margin-bottom: 16px;
}
.post-title {
  margin: 0 0 8px;
  font-size: 20px;
}
.status-tag {
  margin-left: 8px;
  vertical-align: middle;
}
.post-summary {
  margin: 0 0 8px;
}
.post-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.post-stats {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>
