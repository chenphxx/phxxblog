<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { linkApi } from '@/api'
import type { LinkPreview } from '@/types'

const props = defineProps<{ url: string }>()
const preview = ref<LinkPreview | null>(null)
const hostname = computed(() => {
  try {
    return new URL(preview.value?.url || props.url).hostname
  } catch {
    return ''
  }
})

onMounted(async () => {
  try {
    preview.value = await linkApi.preview(props.url)
  } catch {
    // 预览失败时不展示卡片
  }
})
</script>

<template>
  <a v-if="preview" :href="preview.url" target="_blank" rel="noopener noreferrer" class="link-card">
    <img v-if="preview.image" :src="preview.image" class="link-card-img" alt="" />
    <div class="link-card-body">
      <div class="link-card-title">{{ preview.title || preview.url }}</div>
      <div v-if="preview.description" class="link-card-desc">{{ preview.description }}</div>
      <div class="link-card-url muted">{{ hostname }}</div>
    </div>
  </a>
</template>

<style scoped>
.link-card {
  display: flex;
  gap: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
  margin: 8px 0;
  color: var(--text);
  text-decoration: none;
  max-width: 480px;
}
.link-card-img {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
}
.link-card-body {
  min-width: 0;
}
.link-card-title {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.link-card-desc {
  font-size: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.link-card-url {
  font-size: 12px;
}
</style>
