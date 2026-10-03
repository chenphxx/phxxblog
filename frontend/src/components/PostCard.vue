<script setup lang="ts">
import type { PostItem } from '@/types'
import MetaIcon from '@/components/MetaIcon.vue'
import { chipStyle } from '@/utils/chipColor'
import { formatDateTime } from '@/utils/datetime'

/**
 * @brief 文章列表行
 *
 * 列表页(首页/全部文章/搜索)共用: 一条文章就是一行, 由外层面板的细分隔线组织,
 * 不再每篇文章单独套一张浮起的卡片
 *
 * 视觉权重: 标题 > 摘要 > 元信息; 阅读量/点赞只作为弱化的辅助信息, 不抢标题
 *
 * @param post 文章列表项
 */
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
  <article class="post-card">
    <div class="post-head">
      <h3 class="post-title">
        <router-link :to="`/post/${post.id}`">{{ post.title }}</router-link>
      </h3>
      <el-tag v-if="post.status !== 2" size="small" type="warning" class="status-tag">
        {{ STATUS_TEXT[post.status] }}
      </el-tag>
    </div>
    <p v-if="post.summary" class="post-summary">{{ post.summary }}</p>

    <div class="post-meta">
      <span class="num post-date">{{ formatDateTime(post.published_at || post.created_at) }}</span>

      <router-link
        v-for="cat in post.categories"
        :key="cat.id"
        :to="`/search?category=${cat.id}`"
        class="chip chip-icon"
        :style="chipStyle(cat.name, cat.color)"
      >
        <MetaIcon name="folder" />
        <span>{{ cat.name }}</span>
      </router-link>

      <span class="meta-item">
        <MetaIcon name="clock" />
        <span>{{ post.reading_minutes }} 分钟</span>
      </span>

      <router-link
        v-for="tag in post.tags"
        :key="tag.id"
        :to="`/search?tag=${tag.id}`"
        class="chip chip-icon"
        :style="chipStyle(tag.name, tag.color)"
      >
        <MetaIcon name="hash" />
        <span>{{ tag.name }}</span>
      </router-link>

      <span class="meta-item post-stat">
        <MetaIcon name="eye" />
        <span>{{ post.views }}</span>
      </span>
      <span class="meta-item post-stat">
        <MetaIcon name="thumb" />
        <span>{{ post.likes_count }}</span>
      </span>
    </div>
  </article>
</template>

<style scoped>
/* 行本身不带背景与边框: 分隔线由相邻行的 border-top 提供, 贴合外层面板 */
.post-card {
  padding: var(--space-5) var(--space-3);
  border-radius: var(--radius-control);
  transition: background-color var(--dur) var(--ease);
}

.post-card + .post-card {
  border-top: 1px solid var(--border);
}

.post-card:hover {
  background: var(--code-bg);
}

.post-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.post-title {
  margin: 0;
  font-size: 19px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.45;
}

.post-title a {
  color: var(--text);
  transition: color var(--dur) var(--ease);
}

.post-title a:hover {
  color: var(--link);
  text-decoration: none;
}

.status-tag {
  flex-shrink: 0;
  margin-top: 3px;
}

.post-summary {
  margin: 8px 0 12px;
  color: var(--muted);
  font-size: 14.5px;
  line-height: 1.75;
  /* 摘要最多两行, 保证列表节奏一致 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 12.5px;
}

.post-date {
  color: var(--muted);
}

/* 阅读量/点赞: 不加底色, 权重低于分类与标签 */
.post-stat {
  gap: 4px;
}

.post-stat .meta-icon {
  opacity: 0.75;
}
</style>
