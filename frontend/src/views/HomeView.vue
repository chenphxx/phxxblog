<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { categoryApi, mediaApi, postApi, settingsApi, statsApi } from '@/api'
import type { Category, ContributionPoint, PostItem, PublicSettings } from '@/types'
import PostCard from '@/components/PostCard.vue'
import MarkdownView from '@/components/MarkdownView.vue'
import ContributionsChart from '@/components/ContributionsChart.vue'
import { useAuthStore } from '@/stores/auth'

const settings = ref<PublicSettings | null>(null)
const posts = ref<PostItem[]>([])
const categories = ref<Category[]>([])
const contributions = ref<ContributionPoint[]>([])
const loading = ref(true)
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role_codes.includes('admin'))
const contributionYear = ref<number | null>(null)
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
    categories.value = categoryData
    await loadContributions()
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

      <!-- 右侧: README + 贡献 + 最新文章 -->
      <main class="home-main">
        <section v-if="settings?.site_readme" class="card">
          <MarkdownView :content="settings.site_readme" />
        </section>

        <section class="card" style="margin-top: 20px">
          <h3 style="margin: 0 0 12px">文章发布记录</h3>
          <ContributionsChart
            :points="contributions"
            :years="contributionYears"
            :year="contributionYear"
            @update:year="contributionYear = $event"
          />
        </section>

        <section style="margin-top: 24px">
          <div class="posts-head">
            <h2 style="margin: 0">最新文章</h2>
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
  padding: 24px 16px;
}
.profile-avatar {
  margin-bottom: 12px;
}
.clickable-avatar {
  cursor: pointer;
}
.profile-name {
  margin: 0 0 6px;
  font-size: 20px;
}
.profile-bio {
  color: var(--muted);
  font-size: 13px;
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
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 16px;
  color: var(--text);
  font-size: 12px;
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
  font-size: 12px;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 12px;
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
</style>
