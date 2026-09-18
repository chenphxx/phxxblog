<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Refresh } from '@element-plus/icons-vue'
import { miscApi } from '@/api'
import type { PostItem, PublicSettings } from '@/types'
import MetaIcon from '@/components/MetaIcon.vue'
import { formatDateTime } from '@/utils/datetime'

/**
 * @brief 首页的终端会话卡片(招牌元素)
 *
 * 自己负责"一言"的取数, 刷新与复制; 文章总数与"最新一篇"是页面文章列表的数据,
 * 由首页传进来, 避免为了终端里的两行输出再查一次文章接口。
 */
defineProps<{
  settings: PublicSettings | null
  totalPosts: number
  latestPost: PostItem | null
}>()

const saying = ref('')
const sayingLoading = ref(false)

/**
 * @brief 取一条一言
 * @param force 为真时让后端跳过"每天只刷一次"的缓存(用户手动点刷新)
 */
async function loadSaying(force = false) {
  sayingLoading.value = true
  try {
    const data = await miscApi.saying(force)
    saying.value = data.text
  } catch {
    saying.value = '一言暂时走神了, 点击右侧刷新重试'
  } finally {
    sayingLoading.value = false
  }
}

/** @brief 复制当前一言到剪贴板 */
async function copySaying() {
  if (!saying.value) return
  try {
    await navigator.clipboard.writeText(saying.value)
    ElMessage.success('一言已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

/** @brief 重新取一言; 也供首页在 keep-alive 重新激活时调用 */
async function refresh() {
  await loadSaying()
}

onMounted(() => loadSaying())

defineExpose({ refresh })
</script>

<template>
  <section class="term-card">
    <div class="term-head">
      <span class="term-dot term-dot-red" />
      <span class="term-dot term-dot-amber" />
      <span class="term-dot term-dot-green" />
      <span class="term-title">session — {{ settings?.site_name || 'blog' }}</span>
      <div class="term-actions">
        <el-button size="small" circle :disabled="!saying" :icon="CopyDocument" title="复制一言" @click="copySaying" />
        <el-button
          size="small"
          circle
          :loading="sayingLoading"
          :icon="Refresh"
          title="换一句"
          @click="loadSaying(true)"
        />
      </div>
    </div>
    <div class="term-body">
      <p class="term-line"><span class="term-prompt">$</span> whoami</p>
      <p class="term-out">
        {{ settings?.site_name || 'phxxblog' }}<span v-if="settings?.site_bio"> — {{ settings.site_bio }}</span>
      </p>
      <p class="term-line"><span class="term-prompt">$</span> ls posts | wc -l</p>
      <p class="term-out">{{ totalPosts }}</p>
      <p class="term-line"><span class="term-prompt">$</span> tail -n 1 posts/latest</p>
      <p v-if="latestPost" class="term-out">
        <router-link :to="`/post/${latestPost.id}`" class="term-link">
          <MetaIcon name="calendar" />
          <span>{{ formatDateTime(latestPost.published_at || latestPost.created_at) }}</span>
          <span class="term-sep">·</span>
          <span>{{ latestPost.title }}</span>
        </router-link>
      </p>
      <p v-else class="term-out">暂无文章</p>
      <p class="term-line"><span class="term-prompt">$</span> say</p>
      <p class="term-out">{{ saying || '一言加载中...' }}</p>
      <p class="term-line"><span class="term-prompt">$</span><span class="term-cursor" aria-hidden="true" /></p>
    </div>
  </section>
</template>

<style scoped>
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
  /* 悬停底色由终端令牌推导, 跟随主题而不是写死 #16222b */
  --el-button-hover-bg-color: color-mix(in srgb, var(--term-bg) 78%, var(--term-accent));
  --el-button-hover-border-color: color-mix(in srgb, var(--term-border) 55%, var(--term-accent));
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
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--term-text);
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-color: color-mix(in srgb, var(--term-text) 45%, transparent);
}
.term-link:hover {
  color: #ffffff;
}
.term-sep {
  color: var(--term-dim);
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

@media (prefers-reduced-motion: reduce) {
  .term-cursor {
    animation: none;
    opacity: 1;
  }
}
</style>
