<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Calendar, View, Star } from '@element-plus/icons-vue'
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
      <article class="post-detail">
        <el-button size="small" class="back-button" @click="goBack">← 返回</el-button>
        <h1 class="post-detail-title">{{ post.title }}</h1>
        <el-button v-if="canEdit" size="small" type="primary" @click="$router.push(`/write/${post.id}`)">
          编辑
        </el-button>
        <div class="post-detail-meta muted">
          <span>
            <el-icon><Calendar /></el-icon>
            {{ (post.published_at || post.created_at).slice(0, 10) }}
          </span>
          <span>作者: {{ post.author?.nickname || post.author?.username || '匿名' }}</span>
          <router-link v-if="post.category" :to="`/search?category=${post.category.id}`">
            <el-tag size="small" effect="plain">{{ post.category.name }}</el-tag>
          </router-link>
          <router-link v-for="tag in post.tags" :key="tag.id" :to="`/search?tag=${tag.id}`">
            <el-tag size="small" type="info" effect="plain">#{{ tag.name }}</el-tag>
          </router-link>
          <span class="meta-right">
            <el-icon><View /></el-icon> {{ post.views }}
            <el-button
              size="small"
              :type="liked ? 'warning' : 'default'"
              :icon="Star"
              circle
              @click="toggleLike"
            />
            {{ post.likes_count }}
          </span>
        </div>

        <img v-if="post.cover_image" :src="post.cover_image" class="post-cover" alt="封面" />
        <MarkdownView :content="post.content_md" />
      </article>

      <CommentSection :post-id="post.id" />
    </template>
    <el-empty v-else-if="!loading" description="文章不存在或未发布" />
  </div>
</template>

<style scoped>
.post-detail-title {
  font-size: 30px;
  margin: 0 0 12px;
}
.back-button {
  margin-bottom: 12px;
}
.post-detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.meta-right {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.post-cover {
  width: 100%;
  border-radius: 8px;
  margin-bottom: 20px;
  max-height: 400px;
  object-fit: cover;
}
</style>
