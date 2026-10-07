<script setup lang="ts">
import type { PostItem } from '@/types'
import MetaIcon from '@/components/MetaIcon.vue'

/**
 * @brief 文章底部的上一篇/下一篇导航
 *
 * 没有相邻文章的一侧不渲染卡片, 由 .post-nav-card.is-next 的 grid-column
 * 保证"下一篇"始终落在右侧
 */
defineProps<{
  /** 更早的一篇 */
  prev?: PostItem | null
  /** 更晚的一篇 */
  next?: PostItem | null
}>()
</script>

<template>
  <nav class="post-nav" aria-label="相邻文章">
    <router-link v-if="prev" class="post-nav-card is-prev" :to="`/post/${prev.id}`">
      <span class="post-nav-label"><MetaIcon name="back" />上一篇</span>
      <span class="post-nav-title">{{ prev.title }}</span>
    </router-link>
    <router-link v-if="next" class="post-nav-card is-next" :to="`/post/${next.id}`">
      <span class="post-nav-label">下一篇<MetaIcon name="external" /></span>
      <span class="post-nav-title">{{ next.title }}</span>
    </router-link>
  </nav>
</template>

<style scoped>
.post-nav {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}
.post-nav-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: var(--space-4);
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  background: var(--code-bg);
  transition: background-color var(--dur) var(--ease);
}
.post-nav-card:hover {
  background: var(--primary-weak);
  text-decoration: none;
}
/* 没有相邻文章的一侧不渲染卡片, 用 grid-column 保证"下一篇"始终落在右侧 */
.post-nav-card.is-next {
  grid-column: 2;
  text-align: right;
}
.post-nav-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--muted);
}
.post-nav-card.is-next .post-nav-label {
  justify-content: flex-end;
}
.post-nav-title {
  color: var(--text);
  font-size: 14.5px;
  font-weight: 500;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.post-nav-card:hover .post-nav-title {
  color: var(--link);
}
</style>
