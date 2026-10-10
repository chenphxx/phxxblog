<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Refresh } from '@element-plus/icons-vue'
import { miscApi } from '@/api'
import type { PostItem, PublicSettings } from '@/types'
import { formatDate } from '@/utils/datetime'

/**
 * @brief 首页的终端会话(个性化模块, 不是首页的视觉主体)
 *
 * 只保留三段输出: 我是谁 / 有多少篇文章与最新一篇 / 一句一言, 高度约为原版的一半,
 * 并且放在个人介绍之后, 不再抢占首屏焦点
 *
 * 最后一段"一言"来自 saying 模块: 该模块被禁用时卡片仍然渲染, 只是不再请求上游,
 * 也不再显示对应的命令行与操作按钮(两个能力的生命周期互不绑定)
 *
 * 自己负责"一言"的取数, 刷新与复制; 文章总数与"最新一篇"是页面文章列表的数据,
 * 由首页传进来, 避免为了终端里的两行输出再查一次文章接口
 */
const props = defineProps<{
  settings: PublicSettings | null
  totalPosts: number
  latestPost: PostItem | null
  /** 一言模块是否启用 */
  sayingEnabled: boolean
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
  if (!props.sayingEnabled) return
  await loadSaying()
}

onMounted(() => {
  // 一言模块被禁用时连请求都不发
  if (props.sayingEnabled) loadSaying()
})

defineExpose({ refresh })
</script>

<template>
  <section class="term-card">
    <div class="term-head">
      <span class="term-dot term-dot-red" />
      <span class="term-dot term-dot-amber" />
      <span class="term-dot term-dot-green" />
      <span class="term-title">session — {{ settings?.site_name || 'blog' }}</span>
      <div v-if="sayingEnabled" class="term-actions">
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
      <p class="term-out">
        <span class="term-num">{{ totalPosts }}</span>
        <template v-if="latestPost">
          <span class="term-sep">·</span>
          <router-link :to="`/post/${latestPost.id}`" class="term-link" :title="latestPost.title">
            <span class="term-dim">{{ formatDate(latestPost.published_at || latestPost.created_at) }}</span>
            <span>{{ latestPost.title }}</span>
          </router-link>
        </template>
      </p>
      <template v-if="sayingEnabled">
        <p class="term-line"><span class="term-prompt">$</span> say</p>
        <p class="term-out">{{ saying || '一言加载中...' }}<span class="term-cursor" aria-hidden="true" /></p>
      </template>
    </div>
  </section>
</template>

<style scoped>
.term-card {
  background: var(--term-bg);
  border: 1px solid var(--term-border);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-panel);
  overflow: hidden;
}
.term-head {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--term-border);
}
.term-dot {
  width: 9px;
  height: 9px;
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
  font-size: 11.5px;
  color: var(--term-dim);
  flex: 1;
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
  /* 悬停底色由终端令牌推导, 跟随主题而不是写死颜色 */
  --el-button-hover-bg-color: color-mix(in srgb, var(--term-bg) 78%, var(--term-accent));
  --el-button-hover-border-color: color-mix(in srgb, var(--term-border) 55%, var(--term-accent));
  --el-button-hover-text-color: var(--term-text);
}
.term-body {
  padding: 12px 16px 14px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  line-height: 1.6;
}
.term-line {
  margin: 6px 0 0;
  color: var(--term-prompt);
}
.term-line:first-child {
  margin-top: 0;
}
.term-prompt {
  color: var(--term-accent);
  margin-right: 8px;
  user-select: none;
}
.term-out {
  margin: 0 0 0 18px;
  color: var(--term-text);
  overflow-wrap: anywhere;
}
.term-num {
  color: var(--term-accent);
}
.term-sep {
  margin: 0 6px;
  color: var(--term-dim);
}
.term-dim {
  color: var(--term-dim);
  margin-right: 6px;
}
.term-link {
  color: var(--term-text);
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-color: color-mix(in srgb, var(--term-text) 40%, transparent);
}
.term-link:hover {
  text-decoration-color: currentColor;
}
.term-cursor {
  display: inline-block;
  width: 7px;
  height: 13px;
  margin-left: 3px;
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
