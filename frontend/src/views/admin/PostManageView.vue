<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { postApi } from '@/api'
import type { PostItem } from '@/types'

const router = useRouter()
const statusFilter = ref<number | undefined>(undefined)
const keyword = ref('')
const posts = ref<PostItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const selected = ref<PostItem[]>([])
const importDialog = ref(false)
const exportDialog = ref(false)
const exportFmt = ref<'markdown' | 'html'>('markdown')
const exporting = ref(false)
const importing = ref(false)
const importFiles = ref<File[]>([])

const STATUS_TEXT = ['草稿', '审核中', '已发布', '私密', '回收站']
const STATUS_TYPE: Record<number, string> = { 0: 'info', 1: 'warning', 2: 'success', 3: 'danger', 4: 'info' }

async function load() {
  loading.value = true
  try {
    const data = await postApi.adminList({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value,
      keyword: keyword.value || undefined,
    })
    posts.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function changeStatus(post: PostItem, status: number, message: string) {
  await ElMessageBox.confirm(`确定${message}《${post.title}》吗?`, '确认', { type: 'warning' })
  await postApi.changeStatus(post.id, status)
  ElMessage.success('操作成功')
  load()
}

async function trash(post: PostItem) {
  await ElMessageBox.confirm(`确定删除《${post.title}》吗? 将移入回收站。`, '确认', { type: 'warning' })
  await postApi.trash(post.id)
  ElMessage.success('已移入回收站')
  load()
}

async function restore(post: PostItem) {
  await postApi.restore(post.id)
  ElMessage.success('已恢复')
  load()
}

async function forceDelete(post: PostItem) {
  await ElMessageBox.confirm(`彻底删除《${post.title}》? 该操作不可恢复!`, '危险操作', {
    type: 'error',
    confirmButtonText: '彻底删除',
  })
  await postApi.forceDelete(post.id)
  ElMessage.success('已彻底删除')
  load()
}

function onSelectionChange(rows: PostItem[]) {
  selected.value = rows
}

async function togglePrivate(post: PostItem) {
  const target = post.status === 2 ? 3 : 2
  await postApi.changeStatus(post.id, target)
  ElMessage.success(target === 3 ? '已设为私密(仅管理员可见)' : '已设为公开可见')
  load()
}

async function batchSetPrivate() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`将选中的 ${selected.value.length} 篇文章设为私密(仅管理员可见)吗?`, '确认', { type: 'warning' })
  for (const post of selected.value) {
    try {
      await postApi.changeStatus(post.id, 3)
    } catch {
      // 单篇失败继续处理其余文章
    }
  }
  ElMessage.success('批量设为私密完成')
  selected.value = []
  load()
}

async function batchTrash() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`将选中的 ${selected.value.length} 篇文章移入回收站吗?`, '确认', { type: 'warning' })
  for (const post of selected.value) {
    try {
      await postApi.trash(post.id)
    } catch {
      // 忽略单篇失败
    }
  }
  ElMessage.success('批量移入回收站完成')
  selected.value = []
  load()
}

async function batchForceDelete() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`彻底删除选中的 ${selected.value.length} 篇文章? 该操作不可恢复!`, '危险操作', {
    type: 'error',
    confirmButtonText: '彻底删除',
  })
  for (const post of selected.value) {
    try {
      await postApi.forceDelete(post.id)
    } catch {
      // 忽略单篇失败
    }
  }
  ElMessage.success('批量彻底删除完成')
  selected.value = []
  load()
}

function openExportDialog() {
  if (!selected.value.length) {
    ElMessage.warning('请先勾选要导出的文章')
    return
  }
  exportFmt.value = 'markdown'
  exportDialog.value = true
}

async function doExport() {
  exporting.value = true
  try {
    const blob = await postApi.exportPosts(selected.value.map((post) => post.id), exportFmt.value)
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `phxxblog-posts-${new Date().toISOString().slice(0, 10)}.zip`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
    ElMessage.success(`已导出 ${selected.value.length} 篇文章`)
    exportDialog.value = false
  } catch {
    // 错误已由拦截器提示
  } finally {
    exporting.value = false
  }
}

function onImportPick(event: Event) {
  const input = event.target as HTMLInputElement
  importFiles.value = input.files ? Array.from(input.files) : []
}

async function doImport() {
  if (!importFiles.value.length) {
    ElMessage.warning('请先选择文件')
    return
  }
  importing.value = true
  try {
    const result = await postApi.importPosts(importFiles.value)
    ElMessage.success(`导入完成: 成功 ${result.imported} 篇, 跳过 ${result.skipped} 篇`)
    if (result.errors?.length) {
      ElMessage.warning(`部分文件导入失败: ${result.errors.slice(0, 3).join('; ')}`)
    }
    importDialog.value = false
    importFiles.value = []
    page.value = 1
    load()
  } finally {
    importing.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2 style="margin: 0">文章管理</h2>
      <div class="toolbar-actions">
        <el-button @click="importDialog = true">导入文章</el-button>
        <el-button type="primary" @click="router.push('/admin/posts/new')">新建文章</el-button>
      </div>
    </div>

    <div class="toolbar" style="margin-top: 12px">
      <el-radio-group v-model="statusFilter" @change="page = 1; load()">
        <el-radio-button :value="undefined">全部</el-radio-button>
        <el-radio-button v-for="(text, index) in STATUS_TEXT" :key="index" :value="index">{{ text }}</el-radio-button>
      </el-radio-group>
      <el-input v-model="keyword" placeholder="搜索标题" style="max-width: 220px" clearable @keyup.enter="page = 1; load()" @clear="page = 1; load()" />
      <el-button @click="page = 1; load()">搜索</el-button>
    </div>

    <div class="card" style="margin-top: 16px">
      <div v-if="selected.length" class="batch-bar">
        <span class="muted">已选 {{ selected.length }} 篇</span>
        <el-button size="small" type="warning" @click="batchSetPrivate">设为私密</el-button>
        <el-button size="small" type="info" @click="batchTrash">移入回收站</el-button>
        <el-button size="small" @click="openExportDialog">导出选中</el-button>
        <el-button size="small" type="danger" @click="batchForceDelete">彻底删除</el-button>
      </div>
      <el-table :data="posts" v-loading="loading" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link :to="row.status === 2 || row.status === 3 ? `/post/${row.id}` : `/admin/posts/${row.id}/edit`">
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="STATUS_TYPE[row.status]">{{ STATUS_TEXT[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="views" label="阅读" width="70" />
        <el-table-column prop="likes_count" label="点赞" width="70" />
        <el-table-column label="作者" width="100">
          <template #default="{ row }">{{ row.author?.nickname || row.author?.username || '-' }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="110">
          <template #default="{ row }">{{ row.updated_at.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <div class="op-row">
              <el-button v-if="row.status === 2" size="small" type="warning" @click="togglePrivate(row)">私密</el-button>
              <el-button v-else-if="row.status === 3" size="small" type="success" @click="togglePrivate(row)">公开</el-button>
              <el-button size="small" @click="router.push(`/admin/posts/${row.id}/edit`)">编辑</el-button>
              <el-button v-if="row.status === 4" size="small" type="success" @click="restore(row)">恢复</el-button>
              <el-button v-if="row.status === 4" size="small" type="danger" @click="forceDelete(row)">彻底删除</el-button>
              <template v-else>
                <el-button v-if="row.status !== 2 && row.status !== 3" size="small" type="primary" @click="changeStatus(row, 2, '发布')">发布</el-button>
                <el-button v-if="row.status === 0" size="small" type="warning" @click="changeStatus(row, 1, '提交审核')">审核</el-button>
                <el-button size="small" type="danger" @click="trash(row)">删除</el-button>
              </template>
            </div>
          </template>
        </el-table-column>
      </el-table>
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

    <!-- 导入文章 -->
    <el-dialog v-model="importDialog" title="导入文章" width="600px">
      <el-alert type="info" :closable="false" show-icon>
        <template #title>文件要求</template>
        支持 .md 文件或 .zip 压缩包(可多选)。zip 内需包含 .md 文章文件; 文章图片可放在任意目录,
        在正文中用相对路径引用(如 images/xxx.png), 导入时图片会一并上传并自动改写为可访问的 URL。
        支持 YAML frontmatter 元信息: title / slug / status / date / summary / cover_image / category / tags。
        未提供标题时取文件名或首个 # 标题, 默认导入为草稿。
      </el-alert>
      <div class="import-picker">
        <label class="el-button">
          <input type="file" multiple accept=".md,.zip" hidden @change="onImportPick" />
          选择文件
        </label>
        <span v-if="importFiles.length" class="muted">已选 {{ importFiles.length }} 个文件</span>
        <ul v-if="importFiles.length" class="import-files">
          <li v-for="(file, index) in importFiles" :key="index">{{ file.name }}</li>
        </ul>
      </div>
      <template #footer>
        <el-button @click="importDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 导出选中 -->
    <el-dialog v-model="exportDialog" title="导出选中文章" width="460px">
      <el-form label-position="top">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFmt">
            <el-radio value="markdown">Markdown(.md)</el-radio>
            <el-radio value="html">HTML(.html)</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <p class="muted">导出为 zip 压缩包, 文章引用的图片会一并打包, 并自动改写为相对路径。</p>
      <template #footer>
        <el-button @click="exportDialog = false">取消</el-button>
        <el-button type="primary" :loading="exporting" @click="doExport">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
  flex-wrap: wrap;
}
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
}
.op-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  white-space: nowrap;
}
.op-row .el-button {
  margin-left: 0;
}
.import-picker {
  margin-top: 16px;
}
.import-files {
  margin: 10px 0 0;
  padding-left: 20px;
  max-height: 160px;
  overflow-y: auto;
  font-size: 13px;
}
</style>
