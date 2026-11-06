<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chronicleApi } from '@/api'
import MarkdownView from '@/components/MarkdownView.vue'
import { useAuthStore } from '@/stores/auth'
import type { ChronicleDetail } from '@/types'
import { formatDateTime } from '@/utils/datetime'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const chronicle = ref<ChronicleDetail | null>(null)
const loading = ref(true)
const canManage = computed(() => auth.user?.role_codes.includes('admin') ?? false)

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/chronicles')
}

async function load() {
  loading.value = true
  chronicle.value = null
  try {
    chronicle.value = await chronicleApi.detail(Number(route.params.id))
  } finally {
    loading.value = false
  }
}

watch(() => route.params.id, load, { immediate: true })
</script>

<template>
  <div v-loading="loading" class="page-container chronicle-detail-page">
    <template v-if="chronicle">
      <div class="detail-actions">
        <button class="back-link" type="button" @click="goBack">← 返回纪事</button>
        <el-button v-if="canManage" size="small" @click="router.push(`/admin/chronicles/${chronicle.id}/edit`)">
          编辑纪事
        </el-button>
      </div>

      <article class="chronicle-detail">
        <div v-if="chronicle.cover_image" class="detail-cover">
          <img :src="chronicle.cover_image" :alt="chronicle.title" />
        </div>

        <header class="detail-header">
          <p class="eyebrow">INTERNET CHRONICLE / 档案 {{ String(chronicle.id).padStart(3, '0') }}</p>
          <h1>{{ chronicle.title }}</h1>
          <p class="detail-summary">{{ chronicle.summary }}</p>
          <div class="detail-meta">
            <span>记录于 {{ formatDateTime(chronicle.created_at) }}</span>
          </div>
        </header>

        <div class="detail-divider" />

        <div class="reading-body chronicle-content">
          <MarkdownView :content="chronicle.content_md" />
        </div>
      </article>
    </template>

    <el-empty v-else-if="!loading" description="这篇纪事不存在或已关闭" />
  </div>
</template>

<style scoped>
.chronicle-detail-page {
  max-width: 1020px;
}

.detail-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.back-link {
  padding: 6px 13px;
  border: 1px solid var(--border);
  border-radius: var(--radius-chip);
  background: transparent;
  color: var(--muted);
  font-family: inherit;
  font-size: 13px;
  cursor: pointer;
}

.back-link:hover {
  border-color: var(--border-strong);
  color: var(--text);
}

.chronicle-detail {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: var(--radius-panel);
  background: var(--card-bg);
  box-shadow: var(--shadow-panel);
}

.detail-cover {
  width: 100%;
  max-height: 570px;
  overflow: hidden;
  background: var(--code-bg);
}

.detail-cover img {
  display: block;
  width: 100%;
  max-height: 570px;
  object-fit: cover;
}

.detail-header {
  max-width: 800px;
  margin: 0 auto;
  padding: clamp(32px, 6vw, 64px) clamp(24px, 7vw, 76px) var(--space-8);
}

.detail-header h1 {
  margin: var(--space-4) 0;
  color: var(--text);
  font-size: clamp(34px, 5.6vw, 62px);
  font-weight: 680;
  letter-spacing: -0.05em;
  line-height: 1.13;
}

.detail-summary {
  margin: 0;
  color: var(--muted);
  font-size: 17px;
  line-height: 1.8;
}

.detail-meta {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
  margin-top: var(--space-5);
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.04em;
}

.detail-divider {
  width: min(800px, calc(100% - 48px));
  height: 1px;
  margin: 0 auto;
  background: var(--border);
}

.chronicle-content {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-8) clamp(24px, 7vw, 76px) var(--space-16);
  font-size: 16px;
  line-height: 1.95;
}

.chronicle-content :deep(.markdown-body > :first-child) {
  margin-top: 0;
}

.chronicle-content :deep(.markdown-body > :last-child) {
  margin-bottom: 0;
}

@media (max-width: 600px) {
  .chronicle-detail {
    border-radius: var(--radius-card);
  }

  .detail-header h1 {
    font-size: 34px;
  }

  .detail-summary {
    font-size: 15.5px;
  }
}
</style>
