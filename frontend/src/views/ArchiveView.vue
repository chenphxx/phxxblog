<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { postApi } from '@/api'
import type { ArchiveGroup } from '@/types'

const groups = ref<ArchiveGroup[]>([])
const loading = ref(true)

/** 按年份二次分组, 生成侧边栏锚点 */
const yearGroups = computed(() => {
  const map = new Map<number, ArchiveGroup[]>()
  for (const group of groups.value) {
    const list = map.get(group.year) || []
    list.push(group)
    map.set(group.year, list)
  }
  return Array.from(map.entries())
})

const totalPosts = computed(() => groups.value.reduce((sum, g) => sum + g.count, 0))

function anchor(year: number, month: number) {
  return `archive-${year}-${String(month).padStart(2, '0')}`
}

/** 修复 hash 路由下锚点跳转: 使用滚动而非 location.hash */
function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(async () => {
  try {
    groups.value = await postApi.archive()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container archive-page" v-loading="loading">
    <h1>归档 <span class="muted">共 {{ totalPosts }} 篇文章</span></h1>

    <div class="archive-body">
      <!-- 侧边栏: 年份/月份跳转 -->
      <aside class="archive-nav card">
        <div v-for="[year, months] in yearGroups" :key="year" class="nav-year">
          <a href="#" class="nav-year-title" @click.prevent="scrollToId(`archive-${year}`)">{{ year }}</a>
          <a
            v-for="month in months"
            :key="month.month"
            class="nav-month"
            href="#"
            @click.prevent="scrollToId(anchor(year, month.month))"
          >
            {{ month.month }} 月 ({{ month.count }})
          </a>
        </div>
      </aside>

      <!-- 时间轴 -->
      <main class="timeline">
        <template v-for="[year, months] in yearGroups" :key="year">
          <h2 :id="`archive-${year}`" class="year-title">{{ year }}</h2>
          <div v-for="month in months" :key="month.month" class="month-block">
            <h3 :id="anchor(year, month.month)" class="month-title">
              {{ month.month }} 月 · {{ month.count }} 篇
            </h3>
            <div class="timeline">
              <div v-for="post in month.posts" :key="post.id" class="timeline-item">
                <div class="timeline-date muted">
                  {{ (post.published_at || post.created_at).slice(0, 10) }}
                </div>
                <router-link :to="`/post/${post.id}`" class="timeline-title">
                  {{ post.title }}
                </router-link>
              </div>
            </div>
          </div>
        </template>
        <el-empty v-if="!loading && groups.length === 0" description="暂无归档文章" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.archive-body {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 24px;
  align-items: start;
}
.archive-nav {
  position: sticky;
  top: 76px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}
.nav-year {
  margin-bottom: 12px;
}
.nav-year-title {
  display: block;
  font-weight: 700;
  margin-bottom: 6px;
}
.nav-month {
  display: block;
  padding: 3px 0 3px 12px;
  color: var(--muted);
  font-size: 13px;
}
.year-title {
  border-bottom: 2px solid var(--border);
  padding-bottom: 8px;
}
.month-title {
  color: var(--primary);
}
.timeline-date {
  font-size: 12px;
}
.timeline-title {
  font-size: 15px;
  font-weight: 600;
}
@media (max-width: 768px) {
  .archive-body {
    grid-template-columns: 1fr;
  }
  .archive-nav {
    position: static;
  }
}
</style>
