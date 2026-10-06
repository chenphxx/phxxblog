<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star } from '@element-plus/icons-vue'
import { postApi } from '@/api'
import type { MarkdownHeading, PostDetail, PostItem } from '@/types'
import MarkdownView from '@/components/MarkdownView.vue'
import CommentSection from '@/components/CommentSection.vue'
import HotPostsCard from '@/components/HotPostsCard.vue'
import MetaIcon from '@/components/MetaIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { useModulesStore } from '@/stores/modules'
import { chipStyle, LIKES_COLOR, VIEWS_COLOR } from '@/utils/chipColor'
import { formatDateTime } from '@/utils/datetime'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const modules = useModulesStore()
const post = ref<PostDetail | null>(null)
const liked = ref(false)
const loading = ref(true)
/** 右侧栏内容: 正文目录(上方)与热门文章(下方) */
const toc = ref<MarkdownHeading[]>([])
const hotPosts = ref<PostItem[]>([])
const activeHeading = ref('')
/** 站点顶栏是 sticky 的, 判断"标题是否已滚过顶栏"要把它的高度算进去 */
const HEADER_OFFSET = 96

/** 返回上一页(优先返回来源页并恢复滚动位置) */
function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

/** 当前用户是否可编辑该文章(作者本人或管理员/编辑) */
const canEdit = computed(() => {
  if (!auth.user || !post.value) return false
  const roles = auth.user.role_codes
  return roles.includes('admin') || roles.includes('editor') || post.value.author?.id === auth.user.id
})

/**
 * 加载右侧栏的热门文章
 * 属于辅助模块, 失败时保持空列表即可(请求拦截器已经提示过错误)
 */
async function loadHotPosts() {
  try {
    hotPosts.value = await postApi.hot(7)
  } catch {
    hotPosts.value = []
  }
}

/**
 * 同步目录高亮: 取最后一个已经滚过顶栏的标题
 * 不用"视口内第一个", 否则滚动到两个标题之间时高亮会来回跳
 */
function syncActiveHeading() {
  if (!toc.value.length) return
  let current = toc.value[0].id
  for (const heading of toc.value) {
    const node = document.getElementById(heading.id)
    if (!node) continue
    if (node.getBoundingClientRect().top <= HEADER_OFFSET) current = heading.id
    else break
  }
  activeHeading.value = current
}

/** 滚动监听用 rAF 合并, 避免高频滚动里反复读 DOM 位置 */
let scrollFrame = 0
function onScroll() {
  if (scrollFrame) return
  scrollFrame = window.requestAnimationFrame(() => {
    scrollFrame = 0
    syncActiveHeading()
  })
}

/**
 * 点击目录跳转到对应标题
 * 用 scrollIntoView 而不是改 location.hash - 本项目用 hash 路由, 改 hash 会被当成路由跳转
 */
function scrollToHeading(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  activeHeading.value = id
}

// 正文重新渲染(换文章/切主题)后标题会换一批, 重新同步一次高亮
watch(toc, () => syncActiveHeading())

async function load() {
  loading.value = true
  // 先清空目录: 新正文渲染完会通过 MarkdownView 的 headings 事件重新填充
  toc.value = []
  try {
    post.value = await postApi.detail(Number(route.params.id))
  } finally {
    loading.value = false
  }
}

async function toggleLike() {
  if (!post.value) return
  try {
    const result = await postApi.like(post.value.id)
    liked.value = result.liked
    post.value.likes_count = result.likes_count
    ElMessage.success(result.liked ? '点赞成功' : '已取消点赞')
  } catch {
    // 拦截器已提示
  }
}

watch(() => route.params.id, load)
onMounted(() => {
  // 先拿模块开关: 评论模块被禁用时不再挂载评论区(避免发出注定 404 的请求)
  modules.load().then(() => {
    load()
    loadHotPosts()
  })
  window.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  if (scrollFrame) window.cancelAnimationFrame(scrollFrame)
})
</script>

<template>
  <div v-loading="loading" class="page-container">
    <template v-if="post">
      <div class="post-column">
        <div class="post-main">
          <!-- 窄屏放不下右侧目录: 折叠一份放在正文上方 -->
          <details v-if="toc.length" class="toc-inline">
            <summary>目录</summary>
            <div class="toc-nav">
              <button
                v-for="heading in toc"
                :key="heading.id"
                type="button"
                class="toc-link"
                :class="[`toc-lv${heading.level}`, { 'is-active': heading.id === activeHeading }]"
                @click="scrollToHeading(heading.id)"
              >
                {{ heading.text }}
              </button>
            </div>
          </details>

          <article class="panel post-detail">
            <div class="post-topbar">
              <button class="back-link" @click="goBack">← 返回</button>
              <el-button v-if="canEdit" size="small" @click="$router.push(`/write/${post.id}`)">编辑</el-button>
            </div>
            <h1 class="post-detail-title">{{ post.title }}</h1>
            <div class="post-detail-meta">
              <router-link
                v-for="cat in post.categories"
                :key="cat.id"
                :to="`/search?category=${cat.id}`"
                class="chip chip-icon"
                :style="chipStyle(cat.name, cat.color)"
              >
                <MetaIcon name="folder" />
                <span>{{ cat.name }}</span>
              </router-link>
              <span class="meta-item">
                <MetaIcon name="file" />
                <span>约 {{ post.word_count }} 字</span>
              </span>
              <span class="meta-item">
                <MetaIcon name="clock" />
                <span>{{ post.reading_minutes }} 分钟</span>
              </span>
              <router-link
                v-for="tag in post.tags"
                :key="tag.id"
                :to="`/search?tag=${tag.id}`"
                class="chip chip-icon"
                :style="chipStyle(tag.name, tag.color)"
              >
                <MetaIcon name="hash" />
                <span>{{ tag.name }}</span>
              </router-link>
              <span class="meta-item">
                <MetaIcon name="calendar" />
                <span>{{ formatDateTime(post.published_at || post.created_at) }}</span>
              </span>
              <span class="meta-item">
                <MetaIcon name="user" />
                <span>{{ post.author?.nickname || post.author?.username || '匿名' }}</span>
              </span>
              <span class="chip chip-icon" :style="chipStyle('views', VIEWS_COLOR)">
                <MetaIcon name="eye" />
                <span>{{ post.views }}</span>
              </span>
              <span class="chip chip-icon" :style="chipStyle('likes', LIKES_COLOR)">
                <MetaIcon name="thumb" />
                <span>{{ post.likes_count }}</span>
              </span>
              <el-button
                class="like-btn"
                size="small"
                :type="liked ? 'warning' : 'default'"
                :icon="Star"
                circle
                :title="liked ? '取消点赞' : '点赞'"
                @click="toggleLike"
              />
            </div>

            <p v-if="post.summary" class="post-detail-summary">{{ post.summary }}</p>
            <img v-if="post.cover_image" :src="post.cover_image" class="post-cover" alt="封面" />
            <MarkdownView :content="post.content_md" @headings="toc = $event" />

            <!-- 文章末尾: 右下角更新时间 + 上一篇/下一篇(没有相邻文章的一侧留空) -->
            <footer class="post-footer">
              <p class="post-updated">最后更新于 {{ formatDateTime(post.updated_at) }}</p>
              <nav class="post-nav" aria-label="相邻文章">
                <router-link v-if="post.prev_post" class="post-nav-card is-prev" :to="`/post/${post.prev_post.id}`">
                  <span class="post-nav-label"><MetaIcon name="back" />上一篇</span>
                  <span class="post-nav-title">{{ post.prev_post.title }}</span>
                </router-link>
                <router-link v-if="post.next_post" class="post-nav-card is-next" :to="`/post/${post.next_post.id}`">
                  <span class="post-nav-label">下一篇<MetaIcon name="external" /></span>
                  <span class="post-nav-title">{{ post.next_post.title }}</span>
                </router-link>
              </nav>
            </footer>
          </article>

          <CommentSection v-if="modules.isEnabled('comments')" :post-id="post.id" />
        </div>

        <aside class="post-aside">
          <nav v-if="toc.length" class="card toc-card" aria-label="文章目录">
            <p class="eyebrow">目录</p>
            <div class="toc-nav">
              <button
                v-for="heading in toc"
                :key="heading.id"
                type="button"
                class="toc-link"
                :class="[`toc-lv${heading.level}`, { 'is-active': heading.id === activeHeading }]"
                :title="heading.text"
                @click="scrollToHeading(heading.id)"
              >
                {{ heading.text }}
              </button>
            </div>
          </nav>
          <HotPostsCard :posts="hotPosts" />
        </aside>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="文章不存在或未发布" />
  </div>
</template>

<style scoped>
.post-column {
  display: grid;
  /* 阅读列收窄到 820px(正文实际宽度约 760px), 右侧是目录与热门文章 */
  grid-template-columns: minmax(0, 820px) 260px;
  gap: var(--space-6);
  max-width: 1140px;
  margin: 0 auto;
  align-items: start;
}
.post-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
/* 右侧栏跟随滚动: 目录在正文上方, 热门文章在下方 */
.post-aside {
  position: sticky;
  top: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
/* 窄屏放不下两栏: 收成单列并隐藏右侧栏, 正文本身不依赖它 */
@media (max-width: 1100px) {
  .post-column {
    grid-template-columns: 1fr;
  }
  .post-aside {
    display: none;
  }
}

/* 窄屏的折叠目录: 宽屏由右侧栏承担, 这里整体不渲染 */
.toc-inline {
  display: none;
  padding: var(--space-4) var(--space-5);
  border: 1px solid color-mix(in srgb, var(--border) 65%, transparent);
  border-radius: var(--radius-card);
  background: var(--card-bg);
}
.toc-inline summary {
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
@media (max-width: 1100px) {
  .toc-inline {
    display: block;
  }
}
.toc-card {
  padding: var(--space-4) var(--space-5);
}
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
.post-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}
.back-link {
  font-size: 13px;
  color: var(--muted);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-chip);
  padding: 5px 12px;
  cursor: pointer;
  transition:
    color 0.15s ease,
    border-color 0.15s ease;
}
.back-link:hover {
  color: var(--text);
  border-color: var(--border-strong);
}
.post-detail-title {
  font-size: clamp(28px, 3.4vw, 34px);
  font-weight: 650;
  letter-spacing: -0.03em;
  line-height: 1.25;
  margin: 0 0 var(--space-4);
}
.post-detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
  font-size: 12.5px;
  color: var(--muted);
}
.meta-item {
  white-space: nowrap;
}
/* 正文上方的摘要(仅当作者填写摘要时展示) */
.post-detail-summary {
  margin: 0 0 var(--space-6);
  padding: var(--space-4) var(--space-5);
  background: var(--code-bg);
  border-radius: var(--radius-control);
  color: var(--muted);
  font-size: 15px;
  line-height: 1.8;
}
.like-btn {
  margin-left: auto;
}
.post-cover {
  width: 100%;
  border-radius: var(--radius-control);
  margin-bottom: var(--space-6);
  max-height: 420px;
  object-fit: cover;
}
.post-footer {
  margin-top: var(--space-8);
  padding-top: var(--space-5);
  border-top: 1px solid var(--border);
}
.post-updated {
  margin: 0 0 var(--space-4);
  text-align: right;
  font-size: 12.5px;
  color: var(--muted);
}
.post-nav {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}
.post-nav-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: var(--space-4);
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  background: var(--code-bg);
  transition: background-color var(--dur) var(--ease);
}
.post-nav-card:hover {
  background: var(--primary-weak);
  text-decoration: none;
}
/* 没有相邻文章的一侧不渲染卡片, 用 grid-column 保证"下一篇"始终落在右侧 */
.post-nav-card.is-next {
  grid-column: 2;
  text-align: right;
}
.post-nav-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--muted);
}
.post-nav-card.is-next .post-nav-label {
  justify-content: flex-end;
}
.post-nav-title {
  color: var(--text);
  font-size: 14.5px;
  font-weight: 500;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.post-nav-card:hover .post-nav-title {
  color: var(--link);
}
</style>
