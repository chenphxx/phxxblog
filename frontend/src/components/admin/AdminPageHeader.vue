<script setup lang="ts">
/**
 * @brief 管理后台统一页面标题
 *
 * 标题与右侧操作在同一个信息层级中展示; 列表页的筛选与批量操作仍由
 * 页面下方的工具栏承载, 避免标题行堆叠过多控件
 */
defineProps
<{
    /** 页面标题 */
    title: string
    /** 标题上方的小标签 */
    eyebrow?: string
}>()
</script>

<template>
    <header class="admin-page-header">
        <div class="admin-page-heading">
            <span v-if="eyebrow" class="admin-page-eyebrow">{{ eyebrow }}</span>
            <h2>{{ title }}</h2>
        </div>
        <div v-if="$slots.actions" class="admin-page-actions">
            <slot name="actions" />
        </div>
    </header>
</template>
