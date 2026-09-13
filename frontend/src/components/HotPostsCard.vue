<script setup lang="ts">
import type { PostItem } from '@/types'
import MetaIcon from '@/components/MetaIcon.vue'
import { chipStyle, VIEWS_COLOR } from '@/utils/chipColor'

/**
 * @brief 热门文章榜单
 *
 * 首页(个人信息与常用网站之间)与文章详情页右侧栏共用。排序完全由后端
 * `/posts/hot` 决定(按浏览量倒序), 组件只负责展示, 保证两处口径一致。
 *
 * @param posts 热门文章列表, 由调用方按需要的条数取好后传入
 */
defineProps<{ posts: PostItem[] }>()
</script>

<template>
  <aside v-if="posts.length" class="card hot-card">
    <p class="eyebrow">hot — 热门文章</p>
    <ol class="hot-list">
      <li v-for="(item, index) in posts" :key="item.id" class="hot-item">
        <span class="hot-rank" :class="{ 'is-top': index < 3 }">{{ index + 1 }}</span>
        <router-link class="hot-link" :to="`/post/${item.id}`" :title="item.title">
          {{ item.title }}
        </router-link>
        <span class="chip chip-icon hot-views" :style="chipStyle('views', VIEWS_COLOR)">
          <MetaIcon name="eye" />
          <span>{{ item.views }}</span>
        </span>
      </li>
    </ol>
  </aside>
</template>

<style scoped>
.hot-list {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
}
.hot-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
}
.hot-item:last-child {
  border-bottom: none;
}
.hot-rank {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: var(--code-bg);
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 11px;
}
/* 前三名给一点强调, 与站内彩色标签用同一套配色语言 */
.hot-rank.is-top {
  background: var(--primary-weak);
  color: var(--primary);
  font-weight: 700;
}
.hot-link {
  flex: 1;
  min-width: 0;
  color: var(--text);
  font-size: 13.5px;
  line-height: 1.5;
  /* 标题过长时截断, 保证右侧阅读量始终对齐 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hot-link:hover {
  color: var(--primary);
  text-decoration: none;
}
.hot-views {
  flex-shrink: 0;
  padding: 1px 7px;
  font-size: 10.5px;
}
</style>