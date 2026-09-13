<script setup lang="ts">
/**
 * 媒体预览浮层: 在当前页面上覆盖显示图片 / 视频 / 音频 / PDF / 文本。
 *
 * 为什么不直接用 el-image-viewer + el-dialog 各管一类:
 *   媒体库同一个入口要预览四类文件, 两套浮层会长出两种关闭方式与两套键盘行为。
 *   这里统一成一个浮层: 点遮罩或 Esc 关闭, ← → 在当页媒体之间切换。
 * 渲染方式由 `utils/mediaPreview.ts` 的 previewKind() 判定, 该函数有单测。
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { MediaItem } from '@/types'
import { MAX_TEXT_PREVIEW, previewKind } from '@/utils/mediaPreview'
import { formatFileSize } from '@/utils/format'

const props = defineProps<{
  /** 当页媒体列表, ← → 只在当页内切换 */
  items: MediaItem[]
  /** 正在预览的下标, null 表示浮层关闭 */
  index: number | null
}>()

const emit = defineEmits<{
  (e: 'update:index', index: number | null): void
  (e: 'close'): void
  /** 下载交给调用方(媒体库已有 downloadMedia), 避免再写一份下载逻辑 */
  (e: 'download', item: MediaItem): void
}>()

const current = computed(() => (props.index === null ? null : props.items[props.index] ?? null))
const kind = computed(() => (current.value ? previewKind(current.value) : 'unsupported'))

/** 图片默认适应窗口, 需要看细节时可切到原始大小(超出部分滚动查看) */
const actualSize = ref(false)
const panelRef = ref<HTMLElement | null>(null)

const textContent = ref('')
const textLoading = ref(false)
const textError = ref('')

async function loadText(item: MediaItem) {
  textLoading.value = true
  textError.value = ''
  textContent.value = ''
  try {
    /*
     * /assets 是公开静态资源, 直接 fetch 即可, 不必走带鉴权的 http 实例。
     * 内容只通过模板插值输出({{ }}), 会被转义成纯文本, 不会当 HTML 执行。
     */
    const res = await fetch(item.url)
    if (!res.ok) throw new Error(String(res.status))
    textContent.value = await res.text()
  } catch {
    textError.value = '文本内容读取失败, 请下载后查看'
  } finally {
    textLoading.value = false
  }
}

/** 记录浮层上一次是否处于打开状态: 只在"刚打开"时抢焦点, 切换条目时不打断键盘操作 */
let wasOpen = false

/**
 * 切换条目时重置视图状态。
 * 另外: 列表变化(如窗口尺寸变化触发重新取数)导致当前下标失效时, 主动通知调用方关闭浮层,
 * 否则会停在一个空白浮层上。
 */
watch(
  current,
  async (item) => {
    actualSize.value = false
    textContent.value = ''
    textError.value = ''
    if (!item) {
      wasOpen = false
      if (props.index !== null) emit('update:index', null)
      return
    }
    if (kind.value === 'text') loadText(item)
    if (!wasOpen) {
      wasOpen = true
      await nextTick()
      panelRef.value?.focus()
    }
  },
  { immediate: true },
)

function close() {
  emit('update:index', null)
  emit('close')
}

/** 在当页媒体之间切换; 到头/到尾不循环 */
function step(delta: number) {
  if (props.index === null) return
  const next = props.index + delta
  if (next < 0 || next >= props.items.length) return
  emit('update:index', next)
}

function onKeydown(event: KeyboardEvent) {
  if (!current.value) return
  if (event.key === 'Escape') close()
  else if (event.key === 'ArrowLeft') step(-1)
  else if (event.key === 'ArrowRight') step(1)
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <!-- Teleport 到 body: 后台主区是 overflow:auto 的滚动容器, 挂在里面容易受层叠与滚动影响 -->
  <Teleport to="body">
    <div v-if="current" class="media-viewer" @click.self="close">
      <div
        ref="panelRef"
        class="viewer-panel"
        role="dialog"
        aria-modal="true"
        :aria-label="`预览 ${current.original_name}`"
        tabindex="-1"
      >
        <div class="viewer-head">
          <span class="viewer-name" :title="current.original_name">{{ current.original_name }}</span>
          <span class="viewer-meta muted">{{ formatFileSize(current.size) }} · {{ current.type }}</span>
          <span v-if="items.length > 1 && index !== null" class="viewer-count muted">
            {{ index + 1 }} / {{ items.length }}
          </span>
          <div class="viewer-tools">
            <el-button v-if="kind === 'image'" size="small" @click="actualSize = !actualSize">
              {{ actualSize ? '适应窗口' : '原始大小' }}
            </el-button>
            <el-button size="small" @click="emit('download', current)">下载</el-button>
            <el-button size="small" type="primary" @click="close">关闭</el-button>
          </div>
        </div>

        <!-- :key 绑 id: 切换条目时重建元素, 上一个视频/音频会随之停止播放 -->
        <div class="viewer-body" :class="{ 'is-fills': kind === 'pdf' || kind === 'text', 'is-actual': actualSize }">
          <img
            v-if="kind === 'image'"
            :key="`img-${current.id}`"
            :src="current.url"
            :alt="current.original_name"
            class="viewer-image"
          />
          <video
            v-else-if="kind === 'video'"
            :key="`video-${current.id}`"
            :src="current.url"
            class="viewer-video"
            controls
            autoplay
          />
          <div v-else-if="kind === 'audio'" :key="`audio-${current.id}`" class="viewer-audio-box">
            <div class="viewer-audio-icon">🎵</div>
            <audio :src="current.url" class="viewer-audio" controls autoplay />
          </div>
          <iframe
            v-else-if="kind === 'pdf'"
            :key="`pdf-${current.id}`"
            :src="current.url"
            class="viewer-frame"
            :title="`PDF 预览 ${current.original_name}`"
          />
          <pre v-else-if="kind === 'text'" v-loading="textLoading" class="viewer-text">{{ textError || textContent }}</pre>
          <div v-else class="viewer-fallback">
            <div class="viewer-fallback-icon">📄</div>
            <p>该格式无法在线预览, 请下载后查看</p>
            <p class="muted">
              可在线预览: 图片 / 视频 / 音频 / PDF / 文本文件({{ formatFileSize(MAX_TEXT_PREVIEW) }} 以内)
            </p>
          </div>
        </div>

        <div v-if="items.length > 1" class="viewer-foot muted">
          <el-button size="small" :disabled="index === 0" @click="step(-1)">上一个</el-button>
          <span>← → 切换 · Esc 关闭</span>
          <el-button size="small" :disabled="index === items.length - 1" @click="step(1)">下一个</el-button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/*
 * 遮罩刻意用深色而不是主题令牌: 预览浮层的遮罩在深浅色下都应当是暗的(与终端面板同理),
 * 它不属于"跟随主题的强调色"。
 */
.media-viewer {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3vh 3vw;
  background: rgba(0, 0, 0, 0.85);
}

.viewer-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  max-width: 1440px;
  overflow: hidden;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-hover);
  outline: none;
}

.viewer-head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
}

.viewer-name {
  max-width: 42%;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.viewer-meta,
.viewer-count {
  font-family: var(--font-mono);
}

.viewer-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.viewer-body {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 12px;
  background: var(--code-bg);
}

/* PDF / 文本自身铺满, 不再居中留白 */
.viewer-body.is-fills {
  align-items: stretch;
  padding: 0;
}

/* 图片切到原始大小: 取消压缩, 交给 .viewer-body 滚动 */
.viewer-body.is-actual {
  align-items: flex-start;
  justify-content: flex-start;
}

.viewer-image,
.viewer-video {
  max-width: 100%;
  max-height: 100%;
}

.viewer-body.is-actual .viewer-image {
  max-width: none;
  max-height: none;
}

.viewer-audio-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: min(560px, 100%);
  padding: 24px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.viewer-audio-icon {
  font-size: 44px;
}

.viewer-audio {
  width: 100%;
}

.viewer-frame {
  width: 100%;
  height: 100%;
  border: 0;
  /* PDF 阅读器自带白底, 这里跟着用白色以免深色主题下出现白边 */
  background: #fff;
}

.viewer-text {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 14px 16px;
  overflow: auto;
  background: var(--card-bg);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.viewer-fallback {
  text-align: center;
  color: var(--muted);
}

.viewer-fallback-icon {
  font-size: 44px;
  margin-bottom: 8px;
}

.viewer-foot {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px;
  border-top: 1px solid var(--border);
  font-size: 12px;
}
</style>
