<script setup lang="ts">
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
    <div class="post-head">
      <h2 class="post-title">
        <router-link :to="`/post/${post.id}`">{{ post.title }}</router-link>
      </h2>
      <el-tag v-if="post.status !== 2" size="small" type="warning" class="status-tag">
        {{ STATUS_TEXT[post.status] }}
      </el-tag>
    </div>
    <p v-if="post.summary" class="post-summary">{{ post.summary }}</p>
    <div class="post-meta">
      <span class="meta-item">{{ (post.published_at || post.created_at).slice(0, 10) }}</span>
      <span class="meta-item">views {{ post.views }}</span>
      <span class="meta-item">likes {{ post.likes_count }}</span>
      <router-link v-if="post.category" :to="`/search?category=${post.category.id}`" class="cat-chip">
        {{ post.category.name }}/
      </router-link>
      <router-link v-for="tag in post.tags" :key="tag.id" :to="`/search?tag=${tag.id}`" class="tag-token">
        #{{ tag.name }}
      </router-link>
    </div>
  </article>
</template>

<style scoped>
.post-card {
  margin-bottom: 14px;
  padding: 18px 20px;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.post-card:hover {
  border-color: var(--border-strong);
  transform: translateY(-1px);
}
.post-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.post-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1.45;
}
.post-title a {
  color: var(--text);
}
.post-title a:hover {
  color: var(--primary);
  text-decoration: none;
}
.status-tag {
  flex-shrink: 0;
  margin-top: 2px;
}
.post-summary {
  margin: 6px 0 10px;
  color: var(--muted);
  font-size: 13.5px;
  line-height: 1.65;
}
.post-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--muted);
}
.meta-item {
  white-space: nowrap;
}
.cat-chip {
  color: var(--muted);
}
.cat-chip:hover {
  color: var(--primary);
  text-decoration: none;
}
.tag-token {
  color: var(--primary);
  background: var(--primary-weak);
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 11px;
}
.tag-token:hover {
  color: var(--primary-strong);
  text-decoration: none;
}
</style>
