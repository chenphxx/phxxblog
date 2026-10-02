<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mediaApi } from '@/api'
import type { MediaItem } from '@/types'
import MediaPreview from '@/components/MediaPreview.vue'
import ListPager from '@/components/ListPager.vue'
import { formatFileSize } from '@/utils/format'
import { mediaGridMetrics } from '@/utils/mediaGrid'
import { usePagedList } from '@/composables/usePagedList'

/**
 * 选中项存 id 而不是对象
 * el-checkbox 的值类型是标量(string | number | boolean), 传对象会被类型拒绝
 * (且运行时的勾选态比较也不可靠); 用 id 数组既符合它的设计, 也避免重复持有对象
 */
const selected = ref<number[]>([])
const uploading = ref(false)
/** 类型筛选(image/video/audio/file), 空值表示全部; 取值与 `/media` 的 `type` 参数一致 */
const typeFilter = ref('')

/*
 * 每页条数不能写死: 一行的格子数随容器宽度变化, 每页条数 = 列数 × 固定的 10 行,
 * 由 utils/mediaGrid.ts 按容器宽度换算
 * 写死成常数时, 窗口一宽就会出现"明明还有很多空位却已经翻页"
 */
const gridRef = ref<HTMLElement | null>(null)
const pageSize = ref(12)
let observer: ResizeObserver | null = null

/**
 * 列表分页与取数
 * autoLoad 关掉: 挂载时要先量一次栅格容量(它决定每页数量), 再按真实容量取数据,
 * 否则首屏会先按默认的 12 个取一次, 再按每页真实条数重取一次
 */
const { items, total, page, loading, load, reset } = usePagedList<MediaItem>({
  pageSize,
  autoLoad: false,
  fetch: (page, size) => mediaApi.list({ page, page_size: size, type: typeFilter.value || undefined }),
})

/** 量一次栅格宽度换算出每页条数; 量不到宽度(尚未布局)时返回 null */
function gridMetrics() {
  const el = gridRef.value
  if (!el) return null
  return mediaGridMetrics(el.getBoundingClientRect().width)
}

/** 容器宽度变化: 列数变了每页条数就要跟着变, 并回到第 1 页重新取数 */
function onGridResize() {
  const metrics = gridMetrics()
  if (!metrics || metrics.capacity === pageSize.value) return
  // 每页条数变了要回到第 1 页: 否则页码对应的区间会整体错位, 末页还可能越界取到空数据
  pageSize.value = metrics.capacity
  reset()
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files?.length) return
  uploading.value = true
  try {
    for (const file of Array.from(files)) {
      await mediaApi.upload(file)
    }
    ElMessage.success('上传成功')
    reset()
  } finally {
    uploading.value = false
    input.value = ''
  }
}

function downloadUrl(url: string, name: string) {
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = name
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
}

function downloadMedia(media: MediaItem) {
  downloadUrl(media.url, media.original_name)
}

function downloadSelected() {
  // 选中态存的是 id, 下载前映射回对象
  items.value.filter((m) => selected.value.includes(m.id)).forEach((media) => downloadMedia(media))
}

/** 全选当前页 */
function selectAll() {
  selected.value = items.value.map((m) => m.id)
}

/** 反选当前页 */
function invertSelect() {
  const pageIds = items.value.map((m) => m.id)
  const current = new Set(selected.value)
  // 保留其他页已选中的; 当前页做取反
  const kept = selected.value.filter((id) => !pageIds.includes(id))
  const flipped = pageIds.filter((id) => !current.has(id))
  selected.value = [...kept, ...flipped]
}

function copyUrl(media: MediaItem) {
  navigator.clipboard.writeText(media.url)
  ElMessage.success('URL 已复制')
}

async function removeMedia(media: MediaItem) {
  await ElMessageBox.confirm(`删除「${media.original_name}」? 磁盘文件将一并删除。`, '确认', { type: 'warning' })
  await mediaApi.remove(media.id)
  ElMessage.success('删除成功')
  load()
}

async function removeSelected() {
  if (!selected.value.length) {
    ElMessage.warning('请先勾选要删除的文件')
    return
  }
  await ElMessageBox.confirm(`确定删除选中的 ${selected.value.length} 个文件吗? 磁盘文件将一并删除。`, '确认', {
    type: 'warning',
  })
  for (const id of selected.value) {
    await mediaApi.remove(id)
  }
  ElMessage.success('批量删除完成')
  selected.value = []
  load()
}

/** 预览浮层的下标, null 表示未打开 */
const previewIndex = ref<number | null>(null)

onMounted(() => {
  // 先量一次再取数据: 避免首屏先按默认 12 个取回来, 再按真实容量重取一次
  const metrics = gridMetrics()
  if (metrics) pageSize.value = metrics.capacity
  load()
  if (typeof ResizeObserver === 'undefined' || !gridRef.value) return
  observer = new ResizeObserver(onGridResize)
  observer.observe(gridRef.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})
</script>

<template>
  <div class="media-page">
    <h2>媒体库</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <el-select
          v-model="typeFilter"
          size="small"
          placeholder="按类型筛选"
          clearable
          style="width: 150px"
          @change="reset()"
        >
          <el-option label="图片" value="image" />
          <el-option label="视频" value="video" />
          <el-option label="音频" value="audio" />
          <el-option label="其他文件" value="file" />
        </el-select>
      </div>
      <div class="admin-toolbar-actions">
        <el-button size="small" @click="selectAll">全选</el-button>
        <el-button size="small" @click="invertSelect">反选</el-button>
        <el-button :disabled="!selected.length" @click="downloadSelected">下载选中({{ selected.length }})</el-button>
        <label class="el-button el-button--primary" :class="{ 'is-loading': uploading }">
          <input type="file" multiple hidden @change="onFileChange" />
          上传文件
        </label>
        <el-button type="danger" :disabled="!selected.length" @click="removeSelected">删除选中</el-button>
      </div>
    </div>

    <div ref="gridRef" v-loading="loading" class="media-grid">
      <!-- 点卡片任意位置预览; 勾选框与操作按钮上的点击不冒泡到这里 -->
      <div
        v-for="(media, i) in items"
        :key="media.id"
        class="card media-item"
        tabindex="0"
        :title="`点击预览 ${media.original_name}`"
        @click="previewIndex = i"
        @keydown.enter.self="previewIndex = i"
        @keydown.space.self.prevent="previewIndex = i"
      >
        <!--
          选中态存 id(:value 绑 id, 与 el-checkbox 的值类型一致)
          这里对 v-model 做一次断言: Element Plus 运行时的 isChecked 明确支持
          "modelValue 是数组" 的用法(见 use-checkbox-status.mjs), 但发布的 .d.ts 把
          modelValue 收窄成了标量, 因此类型上必须放行 - 断言只影响这一处
        -->
        <el-checkbox v-model="selected as never" :value="media.id" class="media-check" @click.stop />
        <div class="media-preview">
          <img v-if="media.type === 'image'" :src="media.url" :alt="media.original_name" loading="lazy" />
          <!-- 卡片里只当缩略图: 点任意位置进浮层播放(缩略图带 controls 会和"点击预览"打架) -->
          <template v-else-if="media.type === 'video'">
            <video :src="media.url" preload="metadata" muted />
            <span class="media-play-badge">▶</span>
          </template>
          <div v-else class="file-placeholder">{{ media.type === 'audio' ? '🎵' : '📄' }}</div>
        </div>
        <div class="media-name" :title="media.original_name">{{ media.original_name }}</div>
        <div class="muted" style="font-size: 12px">{{ formatFileSize(media.size) }} · {{ media.type }}</div>
        <div class="media-actions" @click.stop>
          <el-button size="small" @click="copyUrl(media)">复制URL</el-button>
          <el-button size="small" @click="downloadMedia(media)">下载</el-button>
          <el-button size="small" type="danger" @click="removeMedia(media)">删除</el-button>
        </div>
      </div>
    </div>

    <MediaPreview v-model:index="previewIndex" :items="items" @close="previewIndex = null" @download="downloadMedia" />

    <ListPager v-model:page="page" :page-size="pageSize" :total="total" />
  </div>
</template>

<style scoped>
.media-page {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 100px);
}
.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  /* 行高固定: 一页固定 10 行, 放不下的部分由后台主内容区滚动 */
  grid-auto-rows: 210px;
  gap: 16px;
}
.media-item {
  position: relative;
  padding: 12px;
  display: flex;
  flex-direction: column;
  /* 整张卡片可点击预览, 给出可点的指针反馈 */
  cursor: pointer;
}
.media-item:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
.media-check {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
}
.media-preview {
  position: relative;
  flex: 1;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--code-bg);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 8px;
}
.media-preview img,
.media-preview video {
  max-width: 100%;
  max-height: 100%;
}
/* 视频缩略图上的播放角标: 提示"点击可播放" */
.media-play-badge {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 13px;
  padding-left: 2px;
}
.file-placeholder {
  font-size: 40px;
}
.media-name {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.media-actions {
  margin-top: auto;
  padding-top: 8px;
  display: flex;
  gap: 6px;
  flex-wrap: nowrap;
  white-space: nowrap;
}
.media-actions .el-button {
  padding: 3px 8px;
  font-size: 12px;
  margin-left: 0;
}
.media-actions .el-button + .el-button {
  margin-left: 0;
}
</style>
