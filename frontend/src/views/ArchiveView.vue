<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { postApi } from '@/api'
import type { ArchiveGroup } from '@/types'
import { formatDate } from '@/utils/datetime'

/**
 * @brief 归档页(书签式时间轴)
 *
 * 一年一张面板: 年份作标题, 下面按月份分组, 每条记录是"定宽日期 + 标题"的一行,
 * 悬停时行首浮出一小段书签色条. 左侧保留年份/月份锚点, 但改成轻量列表(不套卡片)
 */

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

/** 行首日期只显示 MM.DD, 年份由分组标题承担 */
function shortDate(value?: string | null) {
  return formatDate(value).slice(5).replace('-', '.')
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
  <div v-loading="loading" class="page-container archive-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">归档</h1>
        <p class="page-subtitle">按时间倒序排列的全部文章</p>
      </div>
      <span class="count-label num">共 {{ totalPosts }} 篇</span>
    </div>

    <div class="archive-body">
      <!-- 年份/月份锚点: 轻量列表, 不占用卡片外观 -->
      <aside class="archive-nav" aria-label="归档导航">
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

      <main class="archive-main">
        <section v-for="[year, months] in yearGroups" :key="year" class="panel archive-year">
          <h2 :id="`archive-${year}`" class="year-title">{{ year }}</h2>

          <div v-for="month in months" :key="month.month" class="month-block">
            <h3 :id="anchor(year, month.month)" class="month-title">{{ month.month }} 月 · {{ month.count }} 篇</h3>
            <ul class="bookmark-list">
              <li v-for="post in month.posts" :key="post.id" class="bookmark-item">
                <router-link :to="`/post/${post.id}`" class="bookmark-row">
                  <span class="bookmark-date num">{{ shortDate(post.published_at || post.created_at) }}</span>
                  <span class="bookmark-title">{{ post.title }}</span>
                </router-link>
              </li>
            </ul>
          </div>
        </section>

        <el-empty v-if="!loading && groups.length === 0" description="暂无归档文章" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.archive-body {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: var(--space-8);
  align-items: start;
}

.archive-nav {
  position: sticky;
  top: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  max-height: calc(100vh - var(--space-12));
  overflow-y: auto;
}

.nav-year-title {
  display: block;
  margin-bottom: 4px;
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
}

.nav-month {
  display: block;
  padding: 3px 0 3px 12px;
  border-left: 1px solid var(--border);
  color: var(--muted);
  font-size: 12.5px;
}

.nav-month:hover,
.nav-year-title:hover {
  color: var(--link);
  text-decoration: none;
}

.archive-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.year-title {
  margin: 0;
  font-size: 26px;
  font-weight: 650;
  letter-spacing: -0.03em;
  scroll-margin-top: var(--space-6);
}

.month-block {
  margin-top: var(--space-6);
}

.month-title {
  margin: 0 0 var(--space-2);
  color: var(--muted);
  font-size: 13px;
  font-weight: 500;
  scroll-margin-top: var(--space-6);
}

/* ---------- 书签式条目 ---------- */
.bookmark-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.bookmark-item + .bookmark-item {
  border-top: 1px solid var(--border);
}

.bookmark-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-3) var(--space-3) var(--space-3) var(--space-5);
  border-radius: var(--radius-control);
  transition: background-color var(--dur) var(--ease);
}

.bookmark-row:hover {
  background: var(--code-bg);
  text-decoration: none;
}

/* 悬停时行首浮出一小段书签色条 */
.bookmark-row::before {
  content: '';
  position: absolute;
  left: 0;
  top: 7px;
  bottom: 7px;
  width: 2px;
  border-radius: 2px;
  background: var(--primary);
  transform: scaleY(0);
  transition: transform var(--dur) var(--ease);
}

.bookmark-row:hover::before {
  transform: scaleY(1);
}

.bookmark-date {
  flex: 0 0 52px;
  color: var(--muted);
  font-size: 12.5px;
}

.bookmark-title {
  flex: 1;
  min-width: 0;
  color: var(--text);
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bookmark-row:hover .bookmark-title {
  color: var(--link);
}

.count-label {
  font-size: 13px;
  color: var(--muted);
}

@media (max-width: 900px) {
  .archive-body {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-6);
  }

  .archive-nav {
    position: static;
    max-height: none;
  }
}
</style>
