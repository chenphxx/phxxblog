<script setup lang="ts">
import type { CommentItem } from '@/types'
import LinkCard from './LinkCard.vue'

defineProps<{ comment: CommentItem; depth: number }>()

const emit = defineEmits<{
  (e: 'reply', comment: CommentItem): void
  (e: 'edit', comment: CommentItem): void
  (e: 'delete', comment: CommentItem): void
}>()

function extractUrl(content: string): string {
  const match = content.match(/https?:\/\/[^\s<>"']+/)
  return match ? match[0] : ''
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}
</script>

<template>
  <div class="comment-item" :style="{ marginLeft: depth > 0 ? '28px' : '0' }">
    <div class="comment-head">
      <el-avatar :size="depth > 0 ? 24 : 28">{{ (comment.author_name || '匿')[0] }}</el-avatar>
      <span class="comment-name">{{ comment.author_name || '匿名' }}</span>
      <span class="muted">{{ formatDate(comment.created_at) }}</span>
      <el-tag size="small" effect="plain" type="info">{{ comment.location || '未知地区' }}</el-tag>
      <span class="head-actions">
        <el-button v-if="comment.can_edit" size="small" text type="primary" @click="emit('edit', comment)">编辑</el-button>
        <el-button size="small" text type="primary" @click="emit('reply', comment)">回复</el-button>
        <el-button v-if="comment.can_delete" size="small" text type="danger" @click="emit('delete', comment)">删除</el-button>
      </span>
    </div>
    <div class="comment-content">{{ comment.content }}</div>
    <LinkCard v-if="extractUrl(comment.content)" :url="extractUrl(comment.content)" />

    <CommentNode
      v-for="reply in comment.replies"
      :key="reply.id"
      :comment="reply"
      :depth="depth + 1"
      @reply="emit('reply', $event)"
      @edit="emit('edit', $event)"
      @delete="emit('delete', $event)"
    />
  </div>
</template>

<style scoped>
.comment-item {
  border-top: 1px solid var(--border);
  padding: 12px 0;
}
.comment-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.head-actions {
  margin-left: auto;
  display: inline-flex;
  gap: 4px;
}
.comment-name {
  font-weight: 600;
  font-size: 14px;
}
.comment-content {
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
