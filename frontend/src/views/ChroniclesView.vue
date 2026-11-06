<script setup lang="ts">
import { chronicleApi } from '@/api'
import ChronicleCard from '@/components/ChronicleCard.vue'
import ListPager from '@/components/ListPager.vue'
import { usePagedList } from '@/composables/usePagedList'
import type { ChronicleItem } from '@/types'

const { items, total, page, pageSize, loading } = usePagedList<ChronicleItem>({
  fetch: (currentPage, currentPageSize) =>
    chronicleApi.list({
      page: currentPage,
      page_size: currentPageSize,
    }),
  pageSize: 12,
})
</script>

<template>
  <div v-loading="loading" class="page-container chronicles-page">
    <header class="chronicles-header">
      <div class="chronicles-heading">
        <p class="eyebrow">INTERNET CHRONICLE / 人物与事件档案</p>
        <h1 class="page-title">互联网纪事</h1>
        <p class="page-subtitle">记录在互联网世界里遇见的人、发生的事, 以及值得留下的片刻</p>
      </div>
      <div class="chronicles-count" aria-label="纪事总数">
        <strong>{{ total }}</strong>
        <span>则记录</span>
      </div>
    </header>

    <div v-if="items.length" class="chronicle-grid" :class="{ 'is-single': items.length === 1 }">
      <ChronicleCard
        v-for="(item, index) in items"
        :key="item.id"
        :item="item"
        :index="index"
        :featured="index === 0 && items.length > 1"
      />
    </div>
    <el-empty v-else-if="!loading" description="还没有纪事, 从一段值得记住的故事开始吧" />

    <ListPager v-model:page="page" :page-size="pageSize" :total="total" />
  </div>
</template>

<style scoped>
.chronicles-page {
  max-width: 1240px;
}

.chronicles-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-8);
  margin-bottom: var(--space-8);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--border);
}

.chronicles-heading {
  min-width: 0;
}

.chronicles-heading .page-title {
  margin-bottom: var(--space-2);
  font-size: clamp(34px, 5vw, 56px);
  letter-spacing: -0.05em;
}

.chronicles-heading .page-subtitle {
  max-width: 680px;
  font-size: 15px;
}

.chronicles-count {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
  padding-left: var(--space-6);
  border-left: 1px solid var(--border);
}

.chronicles-count strong {
  color: var(--primary-strong);
  font-family: var(--font-mono);
  font-size: 34px;
  line-height: 1;
}

.chronicles-count span {
  margin-top: 5px;
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.chronicle-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-6);
  align-items: stretch;
}

.chronicle-grid.is-single {
  grid-template-columns: minmax(0, 760px);
  justify-content: center;
}

@media (max-width: 1100px) {
  .chronicle-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .chronicles-header {
    align-items: flex-start;
  }

  .chronicle-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 600px) {
  .chronicles-header {
    flex-direction: column;
    gap: var(--space-4);
  }

  .chronicles-count {
    align-items: flex-start;
    padding: 0;
    border-left: 0;
  }

  .chronicles-heading .page-title {
    font-size: 36px;
  }
}
</style>
