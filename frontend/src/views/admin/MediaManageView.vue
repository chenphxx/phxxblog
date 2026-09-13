<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mediaApi } from '@/api'
import type { MediaItem } from '@/types'

const items = ref<MediaItem[]>([])
/**
 * 选中项存 id 而不是对象。
 * el-checkbox 的值类型是标量(string | number | boolean), 传对象会被类型拒绝
 * (且运行时的勾选态比较也不可靠); 用 id 数组既符合它的设计, 也避免重复持有对象。
 */
const selected = ref<number[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)
const uploading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await mediaApi.list({ page: page.value, page_size: pageSize })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
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
    page.value = 1
    load()
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
  await ElMessageBox.confirm(`确定删除选中的 ${selected.value.length} 个文件吗? 磁盘文件将一并删除。`, '确认', { type: 'warning' })
  for (const id of selected.value) {
    await mediaApi.remove(id)
  }
  ElMessage.success('批量删除完成')
  selected.value = []
  load()
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

onMounted(load)
</script>

<template>
  <div class="media-page">
    <div class="toolbar">
      <h2 style="margin: 0">媒体库</h2>
      <div class="toolbar-actions">
        <el-button size="small" @click="selectAll">全选</el-button>
        <el-button size="small" @click="invertSelect">反选</el-button>
        <el-button :disabled="!selected.length" @click="downloadSelected">下载选中({{ selected.length }})</el-button>
        <el-button type="danger" :disabled="!selected.length" @click="removeSelected">删除选中</el-button>
        <label class="el-button el-button--primary" :class="{ 'is-loading': uploading }">
          <input type="file" multiple hidden @change="onFileChange" />
          上传文件
        </label>
      </div>
    </div>

    <div class="media-grid" v-loading="loading">
      <div v-for="media in items" :key="media.id" class="card media-item">
        <!--
          选中态存 id(:value 绑 id, 与 el-checkbox 的值类型一致)。
          这里对 v-model 做一次断言: Element Plus 运行时的 isChecked 明确支持
          "modelValue 是数组" 的用法(见 use-checkbox-status.mjs), 但发布的 .d.ts 把
          modelValue 收窄成了标量, 因此类型上必须放行 —— 断言只影响这一处。
        -->
        <el-checkbox v-model="(selected as never)" :value="media.id" class="media-check" />
        <div class="media-preview">
          <img v-if="media.type === 'image'" :src="media.url" :alt="media.original_name" />
          <video v-else-if="media.type === 'video'" :src="media.url" controls />
          <div v-else class="file-placeholder">📄</div>
        </div>
        <div class="media-name" :title="media.original_name">{{ media.original_name }}</div>
        <div class="muted" style="font-size: 12px">
          {{ formatSize(media.size) }} · {{ media.type }}
        </div>
        <div class="media-actions">
          <el-button size="small" @click="copyUrl(media)">复制URL</el-button>
          <el-button size="small" @click="downloadMedia(media)">下载</el-button>
          <el-button size="small" type="danger" @click="removeMedia(media)">删除</el-button>
        </div>
      </div>
    </div>

    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next, total"
      style="justify-content: center; margin-top: 16px"
      @current-change="load"
    />
  </div>
</template>

<style scoped>
.media-page {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 100px);
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.toolbar-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  grid-auto-rows: minmax(210px, 1fr);
  height: calc(100vh - 210px);
  gap: 16px;
  align-content: stretch;
}
.media-item {
  position: relative;
  padding: 12px;
  display: flex;
  flex-direction: column;
}
.media-check {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
}
.media-preview {
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
