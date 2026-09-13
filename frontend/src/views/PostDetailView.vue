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
import { chipStyle, LIKES_COLOR, VIEWS_COLOR } from '@/utils/chipColor'
import { formatDateTime } from '@/utils/datetime'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
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
 * 加载右侧栏的热门文章。
 * 属于辅助模块, 失败时保持空列表即可(请求拦截器已经提示过错误)。
 */
async function loadHotPosts() {
  try {
    hotPosts.value = await postApi.hot(7)
  } catch {
    hotPosts.value = []
  }
}

/**
 * 同步目录高亮: 取最后一个已经滚过顶栏的标题。
 * 不用"视口内第一个", 否则滚动到两个标题之间时高亮会来回跳。
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
 * 点击目录跳转到对应标题。
 * 用 scrollIntoView 而不是改 location.hash —— 本项目用 hash 路由, 改 hash 会被当成路由跳转。
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
  load()
  loadHotPosts()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  if (scrollFrame) window.cancelAnimationFrame(scrollFrame)
})
</script>

<template>
  <div class="page-container" v-loading="loading">
    <template v-if="post">
      <div class="post-column">
        <div class="post-main">
          <article class="post-detail">
            <div class="post-topbar">
              <button class="back-link" @click="goBack">← 返回</button>
              <el-button v-if="canEdit" size="small" @click="$router.push(`/write/${post.id}`)">编辑</el-button>
            </div>
            <h1 class="post-detail-title">{{ post.title }}</h1>
            <div class="post-detail-meta">
              <router-link
                v-if="post.category"
                :to="`/search?category=${post.category.id}`"
                class="chip chip-icon"
                :style="chipStyle(post.category.name, post.category.color)"
              >
                <MetaIcon name="folder" />
                <span>{{ post.category.name }}</span>
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
                <router-link
                  v-if="post.prev_post"
                  class="post-nav-card is-prev"
                  :to="`/post/${post.prev_post.id}`"
                >
                  <span class="post-nav-label"><MetaIcon name="back" />上一篇</span>
                  <span class="post-nav-title">{{ post.prev_post.title }}</span>
                </router-link>
                <router-link
                  v-if="post.next_post"
                  class="post-nav-card is-next"
                  :to="`/post/${post.next_post.id}`"
                >
                  <span class="post-nav-label">下一篇<MetaIcon name="external" /></span>
                  <span class="post-nav-title">{{ post.next_post.title }}</span>
                </router-link>
              </nav>
            </footer>
          </article>

          <CommentSection :post-id="post.id" />
        </div>

        <aside class="post-aside">
          <nav v-if="toc.length" class="card toc-card" aria-label="文章目录">
            <p class="eyebrow">toc — 目录</p>
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
  /* 正文列 + 右侧栏(目录/热门文章); minmax(0, 1fr) 防止长代码/长链接把正文列撑宽 */
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 24px;
  max-width: 1180px;
  margin: 0 auto;
  align-items: start;
}
.post-main {
  min-width: 0;
}
/* 右侧栏跟随滚动: 目录在正文上方, 热门文章在下方 */
.post-aside {
  position: sticky;
  top: 76px;
  display: flex;
  flex-direction: column;
  gap: 20px;
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
.toc-card {
  padding: 16px 18px;
}
.toc-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 10px;
  /* 目录过长时在卡片内滚动, 否则 sticky 的右栏会被撑出视野、底部永远够不到 */
  max-height: min(52vh, 420px);
  overflow-y: auto;
}
.toc-link {
  display: block;
  width: 100%;
  padding: 4px 8px;
  border: none;
  border-left: 2px solid transparent;
  border-radius: 0 4px 4px 0;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.15s ease, background-color 0.15s ease, border-color 0.15s ease;
}
.toc-link:hover {
  color: var(--primary);
  background: var(--primary-weak);
}
.toc-link.is-active {
  border-left-color: var(--primary);
  background: var(--primary-weak);
  color: var(--primary);
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
  margin-bottom: 14px;
}
.back-link {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 5px 12px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}
.back-link:hover {
  color: var(--primary);
  border-color: var(--primary);
}
.post-detail-title {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.3;
  margin: 0 0 16px;
}
.post-detail-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 22px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
}
.meta-item {
  white-space: nowrap;
}
/* 正文上方的摘要(仅当作者填写摘要时展示) */
.post-detail-summary {
  margin: 0 0 20px;
  padding: 10px 16px;
  border-left: 3px solid var(--primary);
  background: var(--primary-weak);
  border-radius: 0 var(--radius) var(--radius) 0;
  color: var(--muted);
  font-size: 14.5px;
  line-height: 1.75;
}
.like-btn {
  margin-left: auto;
}
.post-cover {
  width: 100%;
  border-radius: var(--radius);
  margin-bottom: 20px;
  max-height: 400px;
  object-fit: cover;
  border: 1px solid var(--border);
}
.post-footer {
  margin-top: 28px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.post-updated {
  margin: 0 0 14px;
  text-align: right;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
}
.post-nav {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.post-nav-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card-bg);
  transition: border-color 0.15s ease;
}
.post-nav-card:hover {
  border-color: var(--primary);
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
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--muted);
}
.post-nav-card.is-next .post-nav-label {
  justify-content: flex-end;
}
.post-nav-title {
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.post-nav-card:hover .post-nav-title {
  color: var(--primary);
}
</style>