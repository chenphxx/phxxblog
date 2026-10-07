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
import PostAdjacentNav from '@/components/post/PostAdjacentNav.vue'
import PostTocNav from '@/components/post/PostTocNav.vue'
import BackToTopBar from '@/components/reading/BackToTopBar.vue'
import ReadingFontSizeControl from '@/components/reading/ReadingFontSizeControl.vue'
import { useAuthStore } from '@/stores/auth'
import { useModulesStore } from '@/stores/modules'
import { chipStyle, LIKES_COLOR, VIEWS_COLOR } from '@/utils/chipColor'
import { formatDateTime } from '@/utils/datetime'
import {
  clampStep,
  readStoredStep,
  READING_FONT_FALLBACK_STEP,
  stepToCodeSize,
  stepToFontSize,
  writeStoredStep,
} from '@/utils/readingFont'

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

/** 文章正文节点: 回到顶部按钮据此计算阅读进度 */
const articleEl = ref<HTMLElement | null>(null)
/** 正文字号的允许范围与默认档(来自 fontsize 模块的公开配置) */
const fontRange = ref({ minStep: 1, maxStep: 5, defaultStep: READING_FONT_FALLBACK_STEP })
/** 当前正文字号档位 */
const fontStep = ref(READING_FONT_FALLBACK_STEP)

/**
 * 读取字号模块的公开配置, 并把访客已有的偏好夹进取值区间
 *
 * 配置拿不到(模块被禁用或接口失败)时用前端兜底值, 保证正文仍是默认观感
 */
function syncFontConfig() {
  const config = modules.moduleConfig('fontsize')
  const minStep = clampStep(Number(config.min_step) || 1, 1, 5)
  const maxStep = clampStep(Math.max(Number(config.max_step) || 5, minStep), 1, 5)
  const defaultStep = clampStep(Number(config.default_step) || READING_FONT_FALLBACK_STEP, minStep, maxStep)
  fontRange.value = { minStep, maxStep, defaultStep }
  fontStep.value = clampStep(readStoredStep() ?? defaultStep, minStep, maxStep)
}

/** 访客改档位: 先夹进取值区间, 再写在浏览器本地 */
function applyFontStep(step: number) {
  fontStep.value = clampStep(step, fontRange.value.minStep, fontRange.value.maxStep)
  writeStoredStep(fontStep.value)
}

/** 正文字号与代码块字号: 由档位换算成 CSS 变量, 由 theme.css 应用(见 .reading-body) */
const readingStyle = computed(() => {
  if (!modules.isEnabled('fontsize')) return {}
  return {
    '--reading-font-size': `${stepToFontSize(fontStep.value)}px`,
    '--reading-code-size': `${stepToCodeSize(fontStep.value)}px`,
  }
})

/** 回到顶部模块的公开配置(阈值与是否显示进度) */
const backToTop = computed(() => {
  const config = modules.moduleConfig('backtotop')
  const threshold = Number(config.threshold_px ?? 600)
  return {
    threshold: Number.isFinite(threshold) ? threshold : 600,
    showProgress: config.show_progress !== false,
  }
})

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
    syncFontConfig()
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
            <PostTocNav :headings="toc" :active-id="activeHeading" @select="scrollToHeading" />
          </details>

          <article ref="articleEl" class="panel post-detail">
            <div class="post-topbar">
              <button class="back-link" @click="goBack">← 返回</button>
              <div class="post-topbar-actions">
                <ReadingFontSizeControl
                  v-if="modules.isEnabled('fontsize')"
                  :step="fontStep"
                  :min-step="fontRange.minStep"
                  :max-step="fontRange.maxStep"
                  @update:step="applyFontStep"
                />
                <el-button v-if="canEdit" size="small" @click="$router.push(`/write/${post.id}`)">编辑</el-button>
              </div>
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
            <!-- 阅读增强: 字号由档位换算成 CSS 变量, 代码块字体由外层类提高选择器特异性 -->
            <div
              class="reading-body"
              :class="{ 'reading-code-font': modules.isEnabled('codefont') }"
              :style="readingStyle"
            >
              <MarkdownView :content="post.content_md" @headings="toc = $event" />
            </div>

            <!-- 文章末尾: 右下角更新时间 + 上一篇/下一篇(没有相邻文章的一侧留空) -->
            <footer class="post-footer">
              <p class="post-updated">最后更新于 {{ formatDateTime(post.updated_at) }}</p>
              <PostAdjacentNav :prev="post.prev_post" :next="post.next_post" />
            </footer>
          </article>

          <CommentSection v-if="modules.isEnabled('comments')" :post-id="post.id" />
        </div>

        <aside class="post-aside">
          <nav v-if="toc.length" class="card toc-card" aria-label="文章目录">
            <p class="eyebrow">目录</p>
            <PostTocNav :headings="toc" :active-id="activeHeading" with-title @select="scrollToHeading" />
          </nav>
          <HotPostsCard :posts="hotPosts" />
        </aside>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="文章不存在或未发布" />

    <BackToTopBar
      v-if="modules.isEnabled('backtotop')"
      :target="articleEl"
      :threshold="backToTop.threshold"
      :show-progress="backToTop.showProgress"
    />
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
.post-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}
.post-topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
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
</style>
