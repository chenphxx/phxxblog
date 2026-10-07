<script setup lang="ts">
import type { MarkdownHeading } from '@/types'

/**
 * @brief 文章目录导航
 *
 * 宽屏放在右侧栏的目录卡片里, 窄屏放在正文上方的折叠块里, 两处共用同一份渲染与样式;
 * 点击只把目标 id 抛给页面, 滚动与高亮计算仍由页面负责
 */
withDefaults(
  defineProps<{
    /** 正文标题, 由 MarkdownView 渲染完成后抛出 */
    headings: MarkdownHeading[]
    /** 当前高亮的标题 id */
    activeId: string
    /** 是否给每一项加 title 提示(窄屏的折叠目录不需要) */
    withTitle?: boolean
  }>(),
  { withTitle: false },
)

defineEmits<{ (e: 'select', id: string): void }>()
</script>

<template>
  <div class="toc-nav">
    <button
      v-for="heading in headings"
      :key="heading.id"
      type="button"
      class="toc-link"
      :class="[`toc-lv${heading.level}`, { 'is-active': heading.id === activeId }]"
      :title="withTitle ? heading.text : undefined"
      @click="$emit('select', heading.id)"
    >
      {{ heading.text }}
    </button>
  </div>
</template>

<style scoped>
.toc-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: var(--space-3);
  /* 目录过长时在卡片内滚动, 否则 sticky 的右栏会被撑出视野, 底部永远够不到 */
  max-height: min(52vh, 420px);
  overflow-y: auto;
}
.toc-link {
  display: block;
  width: 100%;
  padding: 5px 9px;
  border: none;
  border-radius: var(--radius-chip);
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition:
    color 0.15s ease,
    background-color 0.15s ease,
    border-color 0.15s ease;
}
.toc-link:hover {
  color: var(--text);
  background: var(--code-bg);
}
.toc-link.is-active {
  background: var(--code-bg);
  color: var(--text);
  font-weight: 600;
}
/* 按标题层级缩进(h1/h2 不缩进) */
.toc-lv3 {
  padding-left: 20px;
}
.toc-lv4 {
  padding-left: 32px;
}
.toc-lv5 {
  padding-left: 44px;
}
.toc-lv6 {
  padding-left: 56px;
}
</style>
