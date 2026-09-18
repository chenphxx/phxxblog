<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { categoryApi, mediaApi, postApi, settingsApi } from '@/api'
import type { Category, PostItem, PublicSettings } from '@/types'
import PostCard from '@/components/PostCard.vue'
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
 * 只持有页面级数据与布局: 站点设置(含头像弹窗), 分类, 文章列表与分页。
 * 辅助模块(个人资料以外的热门文章, 终端会话, 历史上的今天, 发布记录)各自取数与转圈,
 * 因此任何一个慢接口都不会再把整页按在加载态; 模块开关只在模板里判断一处, 关掉的模块
 * 不挂载也就不会发请求。模块实例通过模板 ref 暴露 refresh(), 由 onActivated 统一重取。
 */

const settings = ref<PublicSettings | null>(null)
const latestPost = ref<PostItem | null>(null)
const categories = ref<Category[]>([])
const loading = ref(true)
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))

/**
 * 首页文章分页: 每页 10 篇, 第 1 页即最近 10 篇。
 * autoLoad 关掉是因为要与站点设置的请求一起发(见 onMounted), 便于统一收尾。
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

// keep-alive 缓存下, 从后台修改设置/发布文章后返回首页要刷新。
// 注意: 以前这里只重取 settings, 文章列表/totalPosts/latestPost 仍是旧数据 ——
// 而终端卡片里的 `ls posts | wc -l` 与"最新一篇"恰恰是首页最显眼的模块。
let firstActivate = true
onActivated(async () => {
  // onMounted 会先跑一次, 首次激活不必重复请求
  if (firstActivate) {
    firstActivate = false
    return
  }
  try {
    const [settingData, categoryData] = await Promise.all([settingsApi.public(), categoryApi.list()])
    settings.value = settingData
    categories.value = categoryData
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
    const [settingData, categoryData] = await Promise.all([settingsApi.public(), categoryApi.list()])
    settings.value = settingData
    categories.value = categoryData
    await loadPosts()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading" class="page-container home-page">
    <div class="home-grid">
      <!-- 左侧: 个人资料 + 常用网站 -->
      <div class="home-left">
        <HomeProfileCard :settings="settings" :categories="categories" @open-avatar="openAvatar" />

        <!-- 热门文章(位于个人信息与常用网站之间) -->
        <HomeHotPostsCard ref="hotPostsRef" />

        <!-- 常用网站(仅管理员可见, 位于个人信息下方) -->
        <HomeSiteLinksCard v-if="isAdmin && settings?.website_links?.length" :links="settings.website_links" />
      </div>

      <!-- 右侧: 终端会话 + 内容区块 -->
      <main class="home-main">
        <!-- 模块开关只在这里判断: 关掉的模块不挂载, 也就不会去请求接口 -->
        <HomeSessionCard
          v-if="settings && settings.show_session !== false"
          ref="sessionRef"
          :settings="settings"
          :total-posts="totalPosts"
          :latest-post="latestPost"
        />

        <HomeHistoryCard v-if="settings && settings.show_history !== false" ref="historyRef" />

        <section v-if="settings?.show_readme !== false && settings?.site_readme" class="card section-card">
          <p class="eyebrow" style="margin-bottom: 10px">readme — 关于</p>
          <MarkdownView :content="settings.site_readme" />
        </section>

        <HomeContributionsSection v-if="settings && settings.show_contributions !== false" ref="contributionsRef" />

        <section ref="postsAnchor" class="home-posts">
          <div class="posts-head">
            <div>
              <p class="eyebrow" style="margin-bottom: 4px">posts — 全部文章</p>
              <h2 class="posts-title">全部文章</h2>
            </div>
            <span class="count-label">共 {{ totalPosts }} 篇</span>
          </div>
          <div v-loading="postsLoading" style="min-height: 120px">
            <PostCard v-for="post in posts" :key="post.id" :post="post" />
            <el-empty v-if="!postsLoading && posts.length === 0" description="还没有发布文章" />
            <div v-if="totalPosts > pageSize" class="pagination-row">
              <el-pagination
                v-model:current-page="page"
                :page-size="pageSize"
                :total="totalPosts"
                layout="prev, pager, next, total"
                background
              />
            </div>
          </div>
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
.home-main {
  min-width: 0;
}
.home-posts {
  margin-top: 28px;
  /* 站点头部是 sticky 的, 翻页滚动时留出间距 */
  scroll-margin-top: 84px;
}
.count-label {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
}
.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: 20px;
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

@media (max-width: 900px) {
  .home-grid {
    grid-template-columns: 1fr;
  }
  .home-left {
    position: static;
  }
}
</style>
