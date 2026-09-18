<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { postApi } from '@/api'
import type { PostItem } from '@/types'
import HotPostsCard from '@/components/HotPostsCard.vue'

/**
 * @brief 首页左侧的热门文章模块
 *
 * 自己负责取数(按浏览量取 7 条)与失败兜底: 属于辅助模块, 失败时保持空列表即可
 * (请求拦截器已经提示过错误), 不让首页其它内容跟着停摆。
 * 首页在 keep-alive 重新激活时调用 refresh() 重取, 因为阅读量会随访问变化。
 */
const posts = ref<PostItem[]>([])

/** @brief 重新取热门文章; 也供首页在重新激活时调用 */
async function refresh() {
  try {
    posts.value = await postApi.hot(7)
  } catch {
    posts.value = []
  }
}

onMounted(refresh)

defineExpose({ refresh })
</script>

<template>
  <HotPostsCard :posts="posts" />
</template>
