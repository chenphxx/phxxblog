<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star } from '@element-plus/icons-vue'
import { postApi } from '@/api'
import type { PostDetail } from '@/types'
import MarkdownView from '@/components/MarkdownView.vue'
import CommentSection from '@/components/CommentSection.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const post = ref<PostDetail | null>(null)
const liked = ref(false)
const loading = ref(true)

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

async function load() {
  loading.value = true
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
onMounted(load)
</script>

<template>
  <div class="page-container" v-loading="loading">
    <template v-if="post">
      <div class="post-column">
        <article class="post-detail">
          <div class="post-topbar">
            <button class="back-link" @click="goBack">← 返回</button>
            <el-button v-if="canEdit" size="small" @click="$router.push(`/write/${post.id}`)">编辑</el-button>
          </div>
          <h1 class="post-detail-title">{{ post.title }}</h1>
          <div class="post-detail-meta">
            <span class="meta-item">date: {{ (post.published_at || post.created_at).slice(0, 10) }}</span>
            <span class="meta-item">author: {{ post.author?.nickname || post.author?.username || '匿名' }}</span>
            <span class="meta-item">views: {{ post.views }}</span>
            <span class="meta-item">likes: {{ post.likes_count }}</span>
            <router-link v-if="post.category" :to="`/search?category=${post.category.id}`" class="cat-chip">
              {{ post.category.name }}/
            </router-link>
            <router-link v-for="tag in post.tags" :key="tag.id" :to="`/search?tag=${tag.id}`" class="tag-token">
              #{{ tag.name }}
            </router-link>
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

          <img v-if="post.cover_image" :src="post.cover_image" class="post-cover" alt="封面" />
          <MarkdownView :content="post.content_md" />
        </article>

        <CommentSection :post-id="post.id" />
      </div>
    </template>
    <el-empty v-else-if="!loading" description="文章不存在或未发布" />
  </div>
</template>

<style scoped>
.post-column {
  max-width: 880px;
  margin: 0 auto;
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
.cat-chip {
  color: var(--muted);
}
.cat-chip:hover {
  color: var(--primary);
  text-decoration: none;
}
.tag-token {
  color: var(--primary);
  background: var(--primary-weak);
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 11px;
}
.tag-token:hover {
  color: var(--primary-strong);
  text-decoration: none;
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
</style>
