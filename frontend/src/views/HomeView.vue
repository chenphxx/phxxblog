<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Refresh } from '@element-plus/icons-vue'
import { categoryApi, mediaApi, miscApi, postApi, settingsApi, statsApi } from '@/api'
import type { Category, ContributionPoint, HistoryEvent, PostItem, PublicSettings, TrackingResult } from '@/types'
import PostCard from '@/components/PostCard.vue'
import MarkdownView from '@/components/MarkdownView.vue'
import ContributionsChart from '@/components/ContributionsChart.vue'
import { useAuthStore } from '@/stores/auth'

const settings = ref<PublicSettings | null>(null)
const posts = ref<PostItem[]>([])
const totalPosts = ref(0)
const categories = ref<Category[]>([])
const contributions = ref<ContributionPoint[]>([])
const loading = ref(true)
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))
const contributionYear = ref<number | null>(null)
const saying = ref('')
const sayingLoading = ref(false)
const historyEvents = ref<HistoryEvent[]>([])
const historyDate = ref('')
const historyLoading = ref(false)
const trackingForm = ref({ number: '', phone: '' })
const trackingLoading = ref(false)
const trackingResult = ref<TrackingResult | null>(null)
/** 可筛选年份(近 6 年) */
const contributionYears = computed(() => {
  const current = new Date().getFullYear()
  return Array.from({ length: 6 }, (_, i) => current - i)
})

// 头像查看/更换
const avatarDialog = ref(false)
const avatarUrl = ref('')
const uploadingAvatar = ref(false)

function openAvatar() {
  avatarUrl.value = settings.value?.site_avatar || ''
  avatarDialog.value = true
}

async function uploadAvatar(options: { file: File }) {
  uploadingAvatar.value = true
  try {
    const media = await mediaApi.upload(options.file)
    avatarUrl.value = media.url
    ElMessage.success('头像已上传, 点击保存生效')
  } finally {
    uploadingAvatar.value = false
  }
}

async function saveAvatar() {
  await settingsApi.update({ site_avatar: avatarUrl.value })
  ElMessage.success('头像已更新')
  settings.value = await settingsApi.public()
  avatarDialog.value = false
}

function favicon(url: string) {
  try {
    return `https://www.google.com/s2/favicons?domain=${new URL(url).hostname}&sz=64`
  } catch {
    return ''
  }
}

function fallbackIcon(event: Event, url: string) {
  const img = event.target as HTMLImageElement
  try {
    img.src = `https://${new URL(url).hostname}/favicon.ico`
  } catch {
    img.style.visibility = 'hidden'
  }
}

function linkName(link: { name?: string; url: string }) {
  if (link.name) return link.name
  try {
    return new URL(link.url).hostname
  } catch {
    return link.url
  }
}

async function loadContributions() {
  contributions.value = await statsApi.contributions({
    source: 'post',
    weeks: 52,
    year: contributionYear.value || undefined,
  })
}

async function loadSaying() {
  sayingLoading.value = true
  try {
    const data = await miscApi.saying()
    saying.value = data.text
  } catch {
    saying.value = '一言暂时走神了, 点击右侧刷新重试'
  } finally {
    sayingLoading.value = false
  }
}

async function copySaying() {
  if (!saying.value) return
  try {
    await navigator.clipboard.writeText(saying.value)
    ElMessage.success('一言已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const data = await miscApi.historyToday()
    historyDate.value = data.date
    historyEvents.value = data.events || []
  } catch {
    historyEvents.value = []
  } finally {
    historyLoading.value = false
  }
}

async function queryTracking() {
  const number = trackingForm.value.number.trim()
  if (!number) {
    ElMessage.warning('请输入快递单号')
    return
  }
  trackingLoading.value = true
  trackingResult.value = null
  try {
    trackingResult.value = await miscApi.trackingQuery({
      tracking_number: number,
      phone: trackingForm.value.phone.trim() || undefined,
    })
  } finally {
    trackingLoading.value = false
  }
}

watch(contributionYear, loadContributions)

// keep-alive 缓存下, 从后台修改设置返回后刷新首页信息(头像/简介/链接等)
onActivated(async () => {
  try {
    settings.value = await settingsApi.public()
  } catch {
    // 忽略刷新失败
  }
})

onMounted(async () => {
  try {
    const [settingData, postData, categoryData] = await Promise.all([
      settingsApi.public(),
      postApi.list({ page: 1, page_size: 8 }),
      categoryApi.list(),
    ])
    settings.value = settingData
    posts.value = postData.items
    totalPosts.value = postData.total
    categories.value = categoryData
    await Promise.all([loadContributions(), loadSaying(), loadHistory()])
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container home-page" v-loading="loading">
    <div class="home-grid">
      <!-- 左侧: 个人资料 + 常用网站 -->
      <div class="home-left">
        <aside class="profile-card card">
          <el-avatar :size="96" :src="settings?.site_avatar || undefined" class="profile-avatar clickable-avatar" @click="openAvatar">
            {{ (settings?.site_name || 'B')[0] }}
          </el-avatar>
          <h1 class="profile-name">{{ settings?.site_name || 'chenphxx' }}</h1>
          <p class="profile-bio">{{ settings?.site_bio || '' }}</p>

          <div class="profile-social">
            <a
              v-for="link in settings?.social_links || []"
              :key="link.url"
              :href="link.url"
              target="_blank"
              rel="noopener noreferrer"
              class="social-link"
              :title="linkName(link)"
            >
              <img v-if="favicon(link.url)" :src="favicon(link.url)" alt="" class="social-icon" @error="fallbackIcon($event, link.url)" />
              <span>{{ linkName(link) }}</span>
            </a>
          </div>

          <div class="profile-tags">
            <el-tag v-for="tag in settings?.tech_tags || []" :key="tag" size="small" effect="plain" round>{{ tag }}</el-tag>
          </div>

          <div class="profile-categories">
            <router-link v-for="cat in categories" :key="cat.id" :to="`/search?category=${cat.id}`" class="category-chip">
              {{ cat.name }} ({{ cat.post_count }})
            </router-link>
          </div>
        </aside>

        <!-- 常用网站(仅管理员可见, 位于个人信息下方) -->
        <aside v-if="isAdmin && settings?.website_links?.length" class="card site-links-card">
          <h3>常用网站</h3>
          <a
            v-for="link in settings.website_links"
            :key="link.url"
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer"
            class="site-link"
          >
            <img v-if="favicon(link.url)" :src="favicon(link.url)" alt="" class="site-link-icon" @error="fallbackIcon($event, link.url)" />
            <span>{{ linkName(link) }}</span>
          </a>
        </aside>
      </div>

      <!-- 右侧: 终端会话 + 内容区块 -->
      <main class="home-main">
        <section class="term-card">
          <div class="term-head">
            <span class="term-dot term-dot-red" />
            <span class="term-dot term-dot-amber" />
            <span class="term-dot term-dot-green" />
            <span class="term-title">session — {{ settings?.site_name || 'blog' }}</span>
            <div class="term-actions">
              <el-button size="small" circle :disabled="!saying" :icon="CopyDocument" title="复制一言" @click="copySaying" />
              <el-button size="small" circle :loading="sayingLoading" :icon="Refresh" title="换一句" @click="loadSaying" />
            </div>
          </div>
          <div class="term-body">
            <p class="term-line"><span class="term-prompt">$</span> whoami</p>
            <p class="term-out">{{ settings?.site_name || 'chenphxx' }}<span v-if="settings?.site_bio"> — {{ settings.site_bio }}</span></p>
            <p class="term-line"><span class="term-prompt">$</span> ls posts | wc -l</p>
            <p class="term-out">{{ totalPosts }}</p>
            <p class="term-line"><span class="term-prompt">$</span> tail -n 1 posts/latest</p>
            <p v-if="posts.length" class="term-out">
              <router-link :to="`/post/${posts[0].id}`" class="term-link">
                {{ (posts[0].published_at || posts[0].created_at).slice(0, 10) }} · {{ posts[0].title }}
              </router-link>
            </p>
            <p v-else class="term-out">暂无文章</p>
            <p class="term-line"><span class="term-prompt">$</span> say</p>
            <p class="term-out">{{ saying || '一言加载中...' }}</p>
            <p class="term-line"><span class="term-prompt">$</span><span class="term-cursor" aria-hidden="true" /></p>
          </div>
        </section>

        <section class="card history-card">
          <div class="history-head">
            <p class="eyebrow">history — 程序员历史上的今天</p>
            <el-button size="small" circle :loading="historyLoading" :icon="Refresh" title="刷新" @click="loadHistory" />
          </div>
          <template v-if="historyEvents.length">
            <p class="muted history-date">{{ historyDate || '今日' }}</p>
            <div v-for="(event, index) in historyEvents" :key="index" class="history-event">
              <span class="history-year">{{ event.year }}</span>
              <div class="history-body">
                <div class="history-title">{{ event.title }}</div>
                <div class="history-desc">{{ event.description }}</div>
                <div class="history-tags">
                  <span v-if="event.category" class="code-token">{{ event.category }}</span>
                  <span v-for="tag in event.tags || []" :key="tag" class="code-token">#{{ tag }}</span>
                </div>
              </div>
            </div>
          </template>
          <el-empty v-else-if="!historyLoading" description="暂无历史上的今天数据" :image-size="60" />
        </section>

        <section v-if="settings?.site_readme" class="card section-card">
          <p class="eyebrow" style="margin-bottom: 10px">readme — 关于</p>
          <MarkdownView :content="settings.site_readme" />
        </section>

        <section v-if="isAdmin" class="card tracking-card">
          <p class="eyebrow" style="margin-bottom: 12px">tracking — 快递查询</p>
          <div class="tracking-form">
            <el-input v-model="trackingForm.number" placeholder="输入快递单号" clearable @keyup.enter="queryTracking" />
            <el-input v-model="trackingForm.phone" placeholder="手机尾号(选填)" maxlength="4" clearable @keyup.enter="queryTracking" />
            <el-button type="primary" :loading="trackingLoading" @click="queryTracking">查询</el-button>
          </div>
          <div v-if="trackingResult" class="tracking-result">
            <div class="tracking-meta">
              <strong>{{ trackingResult.carrier_name || trackingResult.carrier_code || '快递' }}</strong>
              <span class="muted">{{ trackingResult.tracking_number }}</span>
            </div>
            <el-timeline v-if="trackingResult.tracks?.length">
              <el-timeline-item v-for="(track, index) in trackingResult.tracks" :key="index" :timestamp="track.time">
                {{ track.context }}
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无物流信息" :image-size="60" />
          </div>
        </section>

        <section class="card section-card">
          <p class="eyebrow" style="margin-bottom: 12px">activity — 文章发布记录</p>
          <ContributionsChart
            :points="contributions"
            :years="contributionYears"
            :year="contributionYear"
            @update:year="contributionYear = $event"
          />
        </section>

        <section style="margin-top: 28px">
          <div class="posts-head">
            <div>
              <p class="eyebrow" style="margin-bottom: 4px">posts — 最新文章</p>
              <h2 class="posts-title">最新文章</h2>
            </div>
            <el-button size="small" @click="$router.push('/posts')">全部文章</el-button>
          </div>
          <PostCard v-for="post in posts" :key="post.id" :post="post" />
          <el-empty v-if="!loading && posts.length === 0" description="还没有发布文章" />
        </section>
      </main>
    </div>

    <!-- 头像大图/更换 -->
    <el-dialog v-model="avatarDialog" title="头像" width="420px" align-center>
      <div style="text-align: center">
        <el-image
          :src="avatarUrl || undefined"
          :preview-src-list="avatarUrl ? [avatarUrl] : []"
          fit="contain"
          style="width: 220px; height: 220px; border-radius: 12px"
        >
          <template #error>
            <div style="width: 220px; height: 220px; display: flex; align-items: center; justify-content: center" class="muted">
              暂无头像
            </div>
          </template>
        </el-image>
      </div>

      <template v-if="isAdmin">
        <el-divider>更换头像</el-divider>
        <div style="display: flex; gap: 10px; align-items: center">
          <el-input v-model="avatarUrl" placeholder="头像 URL" style="flex: 1" />
          <el-upload :show-file-list="false" :http-request="uploadAvatar" accept="image/*">
            <el-button :loading="uploadingAvatar">本地上传</el-button>
          </el-upload>
        </div>
      </template>
      <template #footer>
        <el-button @click="avatarDialog = false">关闭</el-button>
        <el-button v-if="isAdmin" type="primary" @click="saveAvatar">保存头像</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.home-grid {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
  align-items: start;
}
.home-left {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 76px;
}
.profile-card {
  text-align: center;
  padding: 26px 18px 20px;
}
.profile-avatar {
  margin-bottom: 12px;
}
.clickable-avatar {
  cursor: pointer;
}
.profile-name {
  margin: 0 0 6px;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.profile-bio {
  font-family: var(--font-mono);
  color: var(--muted);
  font-size: 12px;
  margin: 0 0 16px;
}
.profile-social {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.social-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 11.5px;
  text-decoration: none;
}
.social-link:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.social-icon {
  width: 16px;
  height: 16px;
}
.site-links-card {
  padding: 16px;
  text-align: left;
}
.site-links-card h3 {
  margin: 0 0 12px;
  font-size: 15px;
}
.site-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  color: var(--text);
  font-size: 14px;
  text-decoration: none;
}
.site-link:hover {
  color: var(--primary);
}
.site-link-icon {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  flex-shrink: 0;
}
.profile-tags {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}
.profile-categories {
  border-top: 1px solid var(--border);
  padding-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
.category-chip {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 10px;
}
.category-chip:hover {
  color: var(--primary);
  border-color: var(--primary);
  text-decoration: none;
}
.home-main {
  min-width: 0;
}
.posts-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.posts-title {
  margin: 0;
  font-size: 20px;
  letter-spacing: -0.01em;
}
.section-card {
  margin-top: 20px;
}

/* ---------- 终端会话卡片(招牌元素) ---------- */
.term-card {
  margin-bottom: 20px;
  background: var(--term-bg);
  border: 1px solid var(--term-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.term-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--term-border);
  background: color-mix(in srgb, var(--term-bg) 82%, #0d1b22);
}
.term-dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  flex-shrink: 0;
}
.term-dot-red {
  background: #f87171;
}
.term-dot-amber {
  background: #fbbf24;
}
.term-dot-green {
  background: #34d399;
}
.term-title {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--term-dim);
  flex: 1;
  text-align: center;
  margin-right: 58px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.term-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.term-actions .el-button {
  --el-button-bg-color: transparent;
  --el-button-border-color: var(--term-border);
  --el-button-text-color: var(--term-dim);
  --el-button-hover-bg-color: #16222b;
  --el-button-hover-border-color: var(--term-dim);
  --el-button-hover-text-color: var(--term-text);
}
.term-body {
  padding: 16px 20px 18px;
  font-family: var(--font-mono);
  font-size: 13.5px;
  line-height: 1.75;
}
.term-line {
  margin: 8px 0 0;
  color: var(--term-prompt);
}
.term-prompt {
  color: var(--term-accent);
  margin-right: 8px;
  user-select: none;
}
.term-out {
  margin: 0 0 2px 20px;
  color: var(--term-text);
  overflow-wrap: anywhere;
}
.term-link {
  color: var(--term-text);
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-color: color-mix(in srgb, var(--term-text) 45%, transparent);
}
.term-link:hover {
  color: #ffffff;
}
.term-cursor {
  display: inline-block;
  width: 8px;
  height: 15px;
  margin-left: 2px;
  vertical-align: -2px;
  background: var(--term-accent);
  animation: term-blink 1.1s steps(2, start) infinite;
}
@keyframes term-blink {
  0%,
  49% {
    opacity: 1;
  }
  50%,
  100% {
    opacity: 0;
  }
}
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
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--primary);
  background: var(--primary-weak);
  border-radius: 4px;
  padding: 1px 7px;
}
.tracking-card {
  margin-top: 20px;
  margin-bottom: 20px;
}
.tracking-form {
  display: flex;
  gap: 10px;
}
.tracking-form .el-input:first-child {
  flex: 1;
}
.tracking-form .el-input:nth-child(2) {
  width: 150px;
}
.tracking-result {
  margin-top: 16px;
}
.tracking-meta {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 12px;
}
@media (max-width: 900px) {
  .home-grid {
    grid-template-columns: 1fr;
  }
  .home-left {
    position: static;
  }
}
@media (prefers-reduced-motion: reduce) {
  .term-cursor {
    animation: none;
    opacity: 1;
  }
}
</style>
