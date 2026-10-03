<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { categoryApi, mediaApi, postApi, settingsApi, tagApi } from '@/api'
import type { Category, PostItem, PublicSettings, Tag } from '@/types'
import PostCard from '@/components/PostCard.vue'
import ListPager from '@/components/ListPager.vue'
import MarkdownView from '@/components/MarkdownView.vue'
import HomeProfileCard from '@/components/home/HomeProfileCard.vue'
import HomeSiteLinksCard from '@/components/home/HomeSiteLinksCard.vue'
import HomeHotPostsCard from '@/components/home/HomeHotPostsCard.vue'
import HomeSessionCard from '@/components/home/HomeSessionCard.vue'
import HomeHistoryCard from '@/components/home/HomeHistoryCard.vue'
import HomeContributionsSection from '@/components/home/HomeContributionsSection.vue'
import { useAuthStore } from '@/stores/auth'
import { usePagedList } from '@/composables/usePagedList'

/**
 * @brief 前台首页
 *
 * 信息层级: 个人介绍(含文章/分类/标签三个指标) → 终端会话 → 关于 → 最新文章 → 发布记录,
 * 右侧栏放次级模块(热门文章/常用网站/历史上的今天); 文章列表始终是页面的主体
 *
 * 只持有页面级数据与布局: 站点设置(含头像弹窗), 分类/标签, 文章列表与分页
 * 辅助模块(热门文章, 终端会话, 历史上的今天, 发布记录)各自取数与转圈,
 * 因此任何一个慢接口都不会再把整页按在加载态; 模块开关只在模板里判断一处, 关掉的模块
 * 不挂载也就不会发请求. 模块实例通过模板 ref 暴露 refresh(), 由 onActivated 统一重取
 */

const settings = ref<PublicSettings | null>(null)
const latestPost = ref<PostItem | null>(null)
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])
const loading = ref(true)
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))

/**
 * 首页文章分页: 每页 10 篇, 第 1 页即最近 10 篇
 * autoLoad 关掉是因为要与站点设置的请求一起发(见 onMounted), 便于统一收尾
 */
const {
  items: posts,
  total: totalPosts,
  page,
  pageSize,
  loading: postsLoading,
  load: loadPosts,
  reset: resetPosts,
} = usePagedList<PostItem>({
  autoLoad: false,
  fetch: (page, pageSize) => postApi.list({ page, page_size: pageSize }),
  // 终端卡片里的"最新一篇"始终取第 1 页的第一条
  onLoaded: (items) => {
    if (page.value === 1) latestPost.value = items[0] || null
  },
})

const postsAnchor = ref<HTMLElement>()
/** 辅助模块实例: 关掉开关时组件不挂载, 这里就是 null */
const hotPostsRef = ref<InstanceType<typeof HomeHotPostsCard> | null>(null)
const sessionRef = ref<InstanceType<typeof HomeSessionCard> | null>(null)
const historyRef = ref<InstanceType<typeof HomeHistoryCard> | null>(null)
const contributionsRef = ref<InstanceType<typeof HomeContributionsSection> | null>(null)

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

/** 翻页后回到文章列表顶部, 便于查看更早的文章(首次加载不滚动) */
watch(page, () => {
  postsAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
})

// keep-alive 缓存下, 从后台修改设置/发布文章后返回首页要刷新
// 注意: 以前这里只重取 settings, 文章列表/totalPosts/latestPost 仍是旧数据
// 而终端卡片里的文章总数与"最新一篇"恰恰是首页要用到的数据
let firstActivate = true
onActivated(async () => {
  // onMounted 会先跑一次, 首次激活不必重复请求
  if (firstActivate) {
    firstActivate = false
    return
  }
  try {
    const [settingData, categoryData, tagData] = await Promise.all([
      settingsApi.public(),
      categoryApi.list(),
      tagApi.list(),
    ])
    settings.value = settingData
    categories.value = categoryData
    tags.value = tagData
    await Promise.all([
      // 回到第 1 页, 保证能看到最新文章
      resetPosts(),
      // 各模块的数据也随访问变化(阅读量, 一言, 发布记录), 一并重取
      hotPostsRef.value?.refresh(),
      sessionRef.value?.refresh(),
      historyRef.value?.refresh(),
      contributionsRef.value?.refresh(),
    ])
  } catch {
    // 忽略刷新失败
  }
})

onMounted(async () => {
  try {
    const [settingData, categoryData, tagData] = await Promise.all([
      settingsApi.public(),
      categoryApi.list(),
      tagApi.list(),
    ])
    settings.value = settingData
    categories.value = categoryData
    tags.value = tagData
    await loadPosts()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading" class="page-container home-page">
    <div class="home-layout">
      <div class="home-main">
        <!-- 个人介绍 + 内容概览(参考稿里"概览面板"的位置) -->
        <section class="panel">
          <HomeProfileCard :settings="settings" :categories="categories" @open-avatar="openAvatar" />

          <div class="home-metrics">
            <div class="metric">
              <p class="metric-label">文章</p>
              <p class="metric-value">{{ totalPosts }}</p>
              <p class="metric-hint">已发布内容</p>
            </div>
            <div class="metric">
              <p class="metric-label">分类</p>
              <p class="metric-value">{{ categories.length }}</p>
              <p class="metric-hint">内容分类</p>
            </div>
            <div class="metric">
              <p class="metric-label">标签</p>
              <p class="metric-value">{{ tags.length }}</p>
              <p class="metric-hint">主题标签</p>
            </div>
          </div>
        </section>

        <!-- 终端会话: 个性化模块, 缩短后放在个人介绍下方 -->
        <HomeSessionCard
          v-if="settings && settings.show_session !== false"
          ref="sessionRef"
          :settings="settings"
          :total-posts="totalPosts"
          :latest-post="latestPost"
        />

        <!-- 主页 README(关于) -->
        <section v-if="settings?.show_readme !== false && settings?.site_readme" class="panel">
          <div class="panel-head">
            <h2 class="panel-title">关于</h2>
          </div>
          <MarkdownView :content="settings.site_readme" />
        </section>

        <!-- 最新文章: 首页的主体 -->
        <section ref="postsAnchor" class="panel">
          <div class="panel-head">
            <h2 class="panel-title">最新文章</h2>
            <router-link to="/search" class="panel-link">查看全部 →</router-link>
          </div>
          <div v-loading="postsLoading" class="posts-list">
            <PostCard v-for="post in posts" :key="post.id" :post="post" />
            <el-empty v-if="!postsLoading && posts.length === 0" description="还没有发布文章" />
          </div>
          <ListPager v-model:page="page" :page-size="pageSize" :total="totalPosts" />
        </section>

        <!-- 发布记录(热力图需要整行宽度, 放在主列底部) -->
        <HomeContributionsSection v-if="settings && settings.show_contributions !== false" ref="contributionsRef" />
      </div>

      <!-- 右侧栏: 次级模块 -->
      <aside class="home-aside">
        <HomeHotPostsCard ref="hotPostsRef" />
        <HomeSiteLinksCard v-if="isAdmin && settings?.website_links?.length" :links="settings.website_links" />
        <HomeHistoryCard v-if="settings && settings.show_history !== false" ref="historyRef" />
      </aside>
    </div>

    <!-- 头像大图/更换 -->
    <el-dialog v-model="avatarDialog" title="头像" width="420px" align-center>
      <div style="text-align: center">
        <el-image
          :src="avatarUrl || undefined"
          :preview-src-list="avatarUrl ? [avatarUrl] : []"
          fit="contain"
          style="width: 220px; height: 220px; border-radius: var(--radius-card)"
        >
          <template #error>
            <div
              style="width: 220px; height: 220px; display: flex; align-items: center; justify-content: center"
              class="muted"
            >
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
.home-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: var(--space-6);
  align-items: start;
}

.home-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.home-aside {
  position: sticky;
  top: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* 三个指标: 只靠间距分组, 不画分隔线(资料卡片保持干净的整块白) */
.home-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-6) var(--space-8);
  margin-top: var(--space-8);
}

.panel-link {
  font-size: 14px;
  color: var(--muted);
}

.panel-link:hover {
  color: var(--link);
  text-decoration: none;
}

/* 文章列表紧贴面板标题, 行的内边距已经提供留白 */
.posts-list {
  min-height: 80px;
}

@media (max-width: 1100px) {
  .home-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .home-aside {
    position: static;
  }
}

@media (max-width: 640px) {
  .home-metrics {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-6);
  }
}
</style>
