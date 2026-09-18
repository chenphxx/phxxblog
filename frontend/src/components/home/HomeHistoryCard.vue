<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { miscApi } from '@/api'
import type { HistoryEvent } from '@/types'
import MetaIcon from '@/components/MetaIcon.vue'

/**
 * @brief 首页的"程序员历史上的今天"卡片
 *
 * 自己取数与刷新, 取数失败按"暂无数据"展示: 这个数据来自第三方接口, 它不稳定时
 * 不该让首页其它内容跟着停在加载态。
 */
const events = ref<HistoryEvent[]>([])
const date = ref('')
const loading = ref(false)

/** @brief 重新取今日事件; 也供首页在 keep-alive 重新激活时调用 */
async function refresh() {
  loading.value = true
  try {
    const data = await miscApi.historyToday()
    date.value = data.date
    events.value = data.events || []
  } catch {
    events.value = []
  } finally {
    loading.value = false
  }
}

onMounted(refresh)

defineExpose({ refresh })
</script>

<template>
  <section class="card history-card">
    <div class="history-head">
      <p class="eyebrow">history — 程序员历史上的今天</p>
      <el-button size="small" circle :loading="loading" :icon="Refresh" title="刷新" @click="refresh" />
    </div>
    <template v-if="events.length">
      <p class="muted history-date">
        <MetaIcon name="calendar" />
        <span>{{ date || '今日' }}</span>
      </p>
      <div v-for="(event, index) in events" :key="index" class="history-event">
        <span class="history-year">{{ event.year }}</span>
        <div class="history-body">
          <div class="history-title">{{ event.title }}</div>
          <div class="history-desc">{{ event.description }}</div>
          <div class="history-tags">
            <span v-if="event.category" class="code-token">
              <MetaIcon name="folder" />
              <span>{{ event.category }}</span>
            </span>
            <span v-for="tag in event.tags || []" :key="tag" class="code-token">
              <MetaIcon name="hash" />
              <span>{{ tag }}</span>
            </span>
          </div>
        </div>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="暂无历史上的今天数据" :image-size="60" />
  </section>
</template>

<style scoped>
.history-card {
  margin-bottom: 20px;
}
.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.history-head .eyebrow {
  margin: 0;
}
.history-date {
  margin: 0 0 8px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.history-event {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}
.history-event:last-child {
  border-bottom: none;
}
.history-year {
  flex-shrink: 0;
  width: 54px;
  font-weight: 700;
  color: var(--primary);
  font-size: 15px;
}
.history-body {
  min-width: 0;
}
.history-title {
  font-size: 14.5px;
  font-weight: 600;
}
.history-desc {
  font-size: 13px;
  color: var(--muted);
  margin: 4px 0 6px;
  line-height: 1.6;
}
.history-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.code-token {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--primary);
  background: var(--primary-weak);
  border-radius: 4px;
  padding: 1px 7px;
}
</style>
