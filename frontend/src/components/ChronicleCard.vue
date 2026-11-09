<script setup lang="ts">
import { ref, watch } from 'vue'
import LazyImage from '@/components/LazyImage.vue'
import type { ChronicleItem } from '@/types'
import { formatDateTime } from '@/utils/datetime'

const props = withDefaults(
  defineProps<{
    item: ChronicleItem
    index?: number
    featured?: boolean
  }>(),
  {
    index: 0,
    featured: false,
  },
)

const imageFailed = ref(false)

watch(
  () => props.item.cover_image,
  () => {
    imageFailed.value = false
  },
)

/** 卡片只展示日期, 详情页再展示完整更新时间 */
function displayDate(value: string): string {
  return formatDateTime(value).slice(0, 10).replaceAll('-', '.')
}
</script>

<template>
  <router-link
    :to="`/chronicles/${item.id}`"
    class="chronicle-card"
    :class="{ 'is-featured': featured }"
    :aria-label="`阅读互联网纪事: ${item.title}`"
  >
    <div class="chronicle-cover">
      <LazyImage
        v-if="item.cover_image && !imageFailed"
        :src="item.cover_image"
        :alt="item.title"
        @error="imageFailed = true"
      />
      <div v-else class="chronicle-cover-placeholder" aria-hidden="true">
        <span>INTERNET CHRONICLE</span>
        <strong>纪</strong>
      </div>
      <span class="chronicle-number">{{ String(index + 1).padStart(2, '0') }}</span>
    </div>

    <div class="chronicle-card-body">
      <div class="chronicle-meta">
        <time :datetime="item.created_at">{{ displayDate(item.created_at) }}</time>
        <span>人物与事件档案</span>
      </div>
      <h2 class="chronicle-title">{{ item.title }}</h2>
      <p class="chronicle-summary">{{ item.summary }}</p>
      <span class="chronicle-read-more">阅读纪事 <span aria-hidden="true">→</span></span>
    </div>
  </router-link>
</template>

<style scoped>
.chronicle-card {
  display: flex;
  min-width: 0;
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: var(--radius-card);
  background: var(--card-bg);
  box-shadow: var(--shadow-panel);
  color: var(--text);
  transition:
    transform var(--dur) var(--ease),
    border-color var(--dur) var(--ease),
    box-shadow var(--dur) var(--ease);
}

.chronicle-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-float);
  transform: translateY(-4px);
  text-decoration: none;
}

.chronicle-card.is-featured {
  grid-column: span 2;
  flex-direction: row;
}

.chronicle-cover {
  position: relative;
  flex-shrink: 0;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: var(--code-bg);
}

.chronicle-card.is-featured .chronicle-cover {
  width: 56%;
  min-height: 350px;
  aspect-ratio: auto;
}

.chronicle-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 500ms var(--ease);
}

.chronicle-card:hover .chronicle-cover img {
  transform: scale(1.035);
}

.chronicle-cover-placeholder {
  display: flex;
  height: 100%;
  min-height: 210px;
  flex-direction: column;
  justify-content: space-between;
  padding: var(--space-5);
  background:
    radial-gradient(circle at 82% 18%, color-mix(in srgb, var(--primary) 45%, transparent), transparent 34%),
    linear-gradient(145deg, var(--primary-strong), var(--primary) 48%, var(--grad-to));
  color: var(--on-primary, #fff);
}

.chronicle-cover-placeholder span {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.chronicle-cover-placeholder strong {
  align-self: flex-end;
  font-family: serif;
  font-size: clamp(74px, 10vw, 138px);
  font-weight: 400;
  line-height: 0.8;
  opacity: 0.28;
}

.chronicle-number {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  display: inline-flex;
  min-width: 34px;
  height: 26px;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  border: 1px solid color-mix(in srgb, #fff 52%, transparent);
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, #111 46%, transparent);
  color: #fff;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  backdrop-filter: blur(8px);
}

.chronicle-card-body {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  padding: var(--space-5) var(--space-5) var(--space-6);
}

.chronicle-card.is-featured .chronicle-card-body {
  width: 44%;
  justify-content: center;
  padding: var(--space-8);
}

.chronicle-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-bottom: var(--space-3);
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 0.07em;
}

.chronicle-meta time {
  color: var(--primary-strong);
  font-weight: 700;
}

.chronicle-title {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  color: var(--text);
  font-size: 21px;
  font-weight: 650;
  letter-spacing: -0.025em;
  line-height: 1.38;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
}

.chronicle-card.is-featured .chronicle-title {
  font-size: clamp(28px, 3vw, 38px);
  line-height: 1.2;
}

.chronicle-summary {
  display: -webkit-box;
  margin: var(--space-3) 0 var(--space-5);
  overflow: hidden;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.75;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-clamp: 3;
}

.chronicle-card.is-featured .chronicle-summary {
  font-size: 15px;
  -webkit-line-clamp: 4;
  line-clamp: 4;
}

.chronicle-read-more {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  color: var(--primary-strong);
  font-size: 12.5px;
  font-weight: 650;
}

.chronicle-read-more span {
  transition: transform var(--dur) var(--ease);
}

.chronicle-card:hover .chronicle-read-more span {
  transform: translateX(4px);
}

@media (max-width: 900px) {
  .chronicle-card.is-featured {
    grid-column: auto;
    flex-direction: column;
  }

  .chronicle-card.is-featured .chronicle-cover,
  .chronicle-card.is-featured .chronicle-card-body {
    width: 100%;
  }

  .chronicle-card.is-featured .chronicle-cover {
    min-height: 0;
    aspect-ratio: 16 / 10;
  }

  .chronicle-card.is-featured .chronicle-card-body {
    padding: var(--space-5) var(--space-5) var(--space-6);
  }

  .chronicle-card.is-featured .chronicle-title {
    font-size: 23px;
  }
}
</style>
