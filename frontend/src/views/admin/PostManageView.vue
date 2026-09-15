<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { postApi } from '@/api'
import type { PostItem } from '@/types'
import { formatDateTime } from '@/utils/datetime'
import MetaIcon from '@/components/MetaIcon.vue'
import ImportExportDialogs from '@/components/ImportExportDialogs.vue'
import { useImportExport } from '@/composables/useImportExport'

const router = useRouter()
const statusFilter = ref<number | undefined>(undefined)
const keyword = ref('')
const posts = ref<PostItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const selected = ref<PostItem[]>([])

const io = useImportExport({
  filePrefix: 'phxxblog-posts',
  entity: '文章',
  unit: '篇',
  canExport: () => selected.value.length > 0,
  exportMessage: () => `已导出 ${selected.value.length} 篇文章`,
  exportFile: (fmt) => postApi.exportPosts(selected.value.map((post) => post.id), fmt),
  checkImports: (files) => postApi.checkImportPosts(files),
  submitImports: (files, onDuplicate) => postApi.importPosts(files, onDuplicate),
  onImported: () => {
    page.value = 1
    load()
  },
})

const STATUS_TEXT = ['草稿', '审核中', '已发布', '私密', '回收站']
/**
 * 文章状态 -> el-tag 的 type。
 * 用字面量联合而非 string: el-tag 的 type 只接受固定几个值(见 CommentManageView 同样处理)。
 */
type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'
const STATUS_TYPE: Record<number, TagType> = { 0: 'info', 1: 'warning', 2: 'success', 3: 'danger', 4: 'info' }

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

onMounted(load)
</script>

<template>
  <div>
    <h2>文章管理</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <el-radio-group v-model="statusFilter" @change="page = 1; load()">
          <el-radio-button :value="undefined">全部</el-radio-button>
          <el-radio-button v-for="(text, index) in STATUS_TEXT" :key="index" :value="index">{{ text }}</el-radio-button>
        </el-radio-group>
      </div>
      <div class="admin-toolbar-actions">
        <el-input
          v-model="keyword"
          placeholder="搜索标题"
          clearable
          @keyup.enter="page = 1; load()"
          @clear="page = 1; load()"
        />
        <el-button @click="page = 1; load()">搜索</el-button>
        <el-button @click="io.importDialog = true">导入文章</el-button>
        <el-button type="primary" @click="router.push('/admin/posts/new')">新建文章</el-button>
      </div>
    </div>

    <div class="card">
      <div v-if="selected.length" class="batch-bar">
        <span class="muted">已选 {{ selected.length }} 篇</span>
        <el-button size="small" type="warning" @click="batchSetPrivate">设为私密</el-button>
        <el-button size="small" type="info" @click="batchTrash">移入回收站</el-button>
        <el-button size="small" @click="io.openExportDialog">导出选中</el-button>
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
        <el-table-column prop="views" width="70">
          <template #header>
            <span class="th-icon" title="阅读量"><MetaIcon name="eye" /> 阅读</span>
          </template>
        </el-table-column>
        <el-table-column prop="likes_count" width="70">
          <template #header>
            <span class="th-icon" title="点赞数"><MetaIcon name="thumb" /> 点赞</span>
          </template>
        </el-table-column>
        <el-table-column label="作者" width="100">
          <template #default="{ row }">{{ row.author?.nickname || row.author?.username || '-' }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="170">
          <template #header>
            <span class="th-icon" title="最后更新时间"><MetaIcon name="calendar" /> 更新时间</span>
          </template>
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <!-- el-table 插槽的 row 是 DefaultRow(Record<string, any>),
                 显式断言成实际行类型以保留函数的类型约束 -->
            <div class="op-row">
              <el-button v-if="row.status === 2" size="small" type="warning" @click="togglePrivate(row as PostItem)">私密</el-button>
              <el-button v-else-if="row.status === 3" size="small" type="success" @click="togglePrivate(row as PostItem)">公开</el-button>
              <el-button size="small" @click="router.push(`/admin/posts/${row.id}/edit`)">编辑</el-button>
              <el-button v-if="row.status === 4" size="small" type="success" @click="restore(row as PostItem)">恢复</el-button>
              <el-button v-if="row.status === 4" size="small" type="danger" @click="forceDelete(row as PostItem)">彻底删除</el-button>
              <template v-else>
                <el-button v-if="row.status !== 2 && row.status !== 3" size="small" type="primary" @click="changeStatus(row as PostItem, 2, '发布')">发布</el-button>
                <el-button v-if="row.status === 0" size="small" type="warning" @click="changeStatus(row as PostItem, 1, '提交审核')">审核</el-button>
                <el-button size="small" type="danger" @click="trash(row as PostItem)">删除</el-button>
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

    <ImportExportDialogs
      :io="io"
      import-title="导入文章"
      dup-title="检测到重复文章"
      export-title="导出选中文章"
      import-hint="支持 .md 文件或 .zip 压缩包(可多选)。zip 内需包含 .md 文章文件; 文章图片可放在任意目录, 在正文中用相对路径引用(如 images/xxx.png), 导入时图片会一并上传并自动改写为可访问的 URL。支持 YAML frontmatter 元信息: title / slug / status / date / summary / cover_image / categories(可多个) / tags。未提供标题时取文件名或首个 # 标题, 默认导入为草稿。导入前会按标题查重(忽略大小写与首尾空格), 有重复时可选择仅导入不重复或全部导入。"
      dup-hint="重复依据为文章标题(忽略大小写与首尾空格)。可跳过重复内容, 也可全部导入。"
      export-hint="导出为 zip 压缩包, 文章引用的图片会一并打包, 并自动改写为相对路径。"
    />
  </div>
</template>

<style scoped>
/* 表头图标: 与文字垂直居中, 图标略淡 */
.th-icon {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.th-icon .meta-icon {
  opacity: 0.7;
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
</style>
