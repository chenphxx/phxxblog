<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { chronicleApi } from '@/api'
import ImportExportDialogs from '@/components/ImportExportDialogs.vue'
import ListPager from '@/components/ListPager.vue'
import { useImportExport } from '@/composables/useImportExport'
import { usePagedList } from '@/composables/usePagedList'
import type { ChronicleItem } from '@/types'
import { formatDateTime } from '@/utils/datetime'
import { POST_STATUS_ORDERED, POST_STATUS_TEXT, POST_STATUS_TYPE } from '@/utils/postStatus'

const router = useRouter()
const statusFilter = ref<number | undefined>(undefined)
const keyword = ref('')
const selected = ref<ChronicleItem[]>([])

const { items, total, page, pageSize, loading, load, reset } = usePagedList<ChronicleItem>({
  fetch: (currentPage, currentPageSize) =>
    chronicleApi.adminList({
      page: currentPage,
      page_size: currentPageSize,
      status: statusFilter.value,
      keyword: keyword.value.trim() || undefined,
    }),
})

const io = useImportExport({
  filePrefix: 'phxxblog-chronicles',
  entity: '纪事',
  unit: '则',
  canExport: () => selected.value.length > 0,
  exportMessage: () => `已导出 ${selected.value.length} 则纪事`,
  exportFile: (fmt) =>
    chronicleApi.exportChronicles(
      selected.value.map((item) => item.id),
      fmt,
    ),
  checkImports: (files) => chronicleApi.checkImportChronicles(files),
  submitImports: (files, onDuplicate) => chronicleApi.importChronicles(files, onDuplicate),
  onImported: () => reset(),
})

async function changeStatus(item: ChronicleItem, status: number, message: string) {
  await ElMessageBox.confirm(`确定${message}《${item.title}》吗?`, '确认', { type: 'warning' })
  await chronicleApi.changeStatus(item.id, status)
  ElMessage.success('操作成功')
  load()
}

async function trash(item: ChronicleItem) {
  await ElMessageBox.confirm(`确定删除《${item.title}》吗? 将移入回收站。`, '确认', { type: 'warning' })
  await chronicleApi.remove(item.id)
  ElMessage.success('已移入回收站')
  load()
}

async function restore(item: ChronicleItem) {
  await chronicleApi.restore(item.id)
  ElMessage.success('已恢复')
  load()
}

async function forceDelete(item: ChronicleItem) {
  await ElMessageBox.confirm(`彻底删除《${item.title}》? 该操作不可恢复!`, '危险操作', {
    type: 'error',
    confirmButtonText: '彻底删除',
  })
  await chronicleApi.forceDelete(item.id)
  ElMessage.success('已彻底删除')
  load()
}

function onSelectionChange(rows: ChronicleItem[]) {
  selected.value = rows
}

async function togglePrivate(item: ChronicleItem) {
  const target = item.status === 2 ? 3 : 2
  await chronicleApi.changeStatus(item.id, target)
  ElMessage.success(target === 3 ? '已设为私密(仅管理员可见)' : '已设为公开可见')
  load()
}

async function batchSetPrivate() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`将选中的 ${selected.value.length} 则纪事设为私密(仅管理员可见)吗?`, '确认', {
    type: 'warning',
  })
  for (const item of selected.value) {
    try {
      await chronicleApi.changeStatus(item.id, 3)
    } catch {
      // 单条失败继续处理其余纪事
    }
  }
  ElMessage.success('批量设为私密完成')
  selected.value = []
  load()
}

async function batchTrash() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`将选中的 ${selected.value.length} 则纪事移入回收站吗?`, '确认', { type: 'warning' })
  for (const item of selected.value) {
    try {
      await chronicleApi.remove(item.id)
    } catch {
      // 单条失败继续处理其余纪事
    }
  }
  ElMessage.success('批量移入回收站完成')
  selected.value = []
  load()
}

async function batchForceDelete() {
  if (!selected.value.length) return
  await ElMessageBox.confirm(`彻底删除选中的 ${selected.value.length} 则纪事? 该操作不可恢复!`, '危险操作', {
    type: 'error',
    confirmButtonText: '彻底删除',
  })
  for (const item of selected.value) {
    try {
      await chronicleApi.forceDelete(item.id)
    } catch {
      // 单条失败继续处理其余纪事
    }
  }
  ElMessage.success('批量彻底删除完成')
  selected.value = []
  load()
}
</script>

<template>
  <div>
    <h2>互联网纪事管理</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <el-radio-group v-model="statusFilter" @change="reset()">
          <el-radio-button :value="undefined">全部</el-radio-button>
          <el-radio-button v-for="(text, index) in POST_STATUS_ORDERED" :key="index" :value="index">
            {{ text }}
          </el-radio-button>
        </el-radio-group>
      </div>
      <div class="admin-toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索标题" clearable @keyup.enter="reset()" @clear="reset()" />
        <el-button @click="reset()">搜索</el-button>
        <el-button @click="io.importDialog = true">导入纪事</el-button>
        <el-button type="primary" @click="router.push('/admin/chronicles/new')">新建纪事</el-button>
      </div>
    </div>

    <div class="card">
      <div v-if="selected.length" class="batch-bar">
        <span class="muted">已选 {{ selected.length }} 则</span>
        <el-button size="small" type="warning" @click="batchSetPrivate">设为私密</el-button>
        <el-button size="small" type="info" @click="batchTrash">移入回收站</el-button>
        <el-button size="small" @click="io.openExportDialog">导出选中</el-button>
        <el-button size="small" type="danger" @click="batchForceDelete">彻底删除</el-button>
      </div>
      <el-table v-loading="loading" :data="items" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="封面" width="112">
          <template #default="{ row }">
            <div class="cover-thumb">
              <img v-if="row.cover_image" :src="row.cover_image" :alt="row.title" />
              <span v-else>纪</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link
              :to="row.status === 2 || row.status === 3 ? `/chronicles/${row.id}` : `/admin/chronicles/${row.id}/edit`"
            >
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="POST_STATUS_TYPE[row.status]">{{ POST_STATUS_TEXT[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <div class="op-row">
              <el-button
                v-if="row.status === 2"
                size="small"
                type="warning"
                @click="togglePrivate(row as ChronicleItem)"
                >私密</el-button
              >
              <el-button
                v-else-if="row.status === 3"
                size="small"
                type="success"
                @click="togglePrivate(row as ChronicleItem)"
                >公开</el-button
              >
              <el-button size="small" @click="router.push(`/admin/chronicles/${row.id}/edit`)">编辑</el-button>
              <el-button v-if="row.status === 4" size="small" type="success" @click="restore(row as ChronicleItem)"
                >恢复</el-button
              >
              <el-button v-if="row.status === 4" size="small" type="danger" @click="forceDelete(row as ChronicleItem)"
                >彻底删除</el-button
              >
              <template v-else>
                <el-button
                  v-if="row.status !== 2 && row.status !== 3"
                  size="small"
                  type="primary"
                  @click="changeStatus(row as ChronicleItem, 2, '发布')"
                  >发布</el-button
                >
                <el-button
                  v-if="row.status === 0"
                  size="small"
                  type="warning"
                  @click="changeStatus(row as ChronicleItem, 1, '提交审核')"
                  >审核</el-button
                >
                <el-button size="small" type="danger" @click="trash(row as ChronicleItem)">删除</el-button>
              </template>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <ListPager v-model:page="page" :page-size="pageSize" :total="total" />
    </div>

    <ImportExportDialogs
      :io="io"
      import-title="导入互联网纪事"
      dup-title="检测到重复纪事"
      export-title="导出选中纪事"
      import-hint="支持 .md 文件或 .zip 压缩包(可多选)。zip 内需包含 .md 纪事文件; 图片可放在任意目录, 在正文中用相对路径引用(如 images/xxx.png), 导入时图片会一并上传到媒体库并自动改写为可访问的 URL。支持 YAML frontmatter 元信息: title / status / date / summary / cover_image。未提供标题时取文件名或首个一级标题; 未提供概览时从正文自动提取; 未提供状态时导入为草稿。导入前按标题查重(忽略大小写与首尾空格), 有重复时可选择仅导入不重复或全部导入。"
      dup-hint="重复依据为纪事标题(忽略大小写与首尾空格)。可跳过重复内容, 也可全部导入。"
      export-hint="导出所选纪事为 zip 压缩包, 正文引用的图片和封面会一并打包, 并自动改写为相对路径。"
    />
  </div>
</template>

<style scoped>
.cover-thumb {
  display: flex;
  width: 82px;
  height: 52px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 8px;
  background: var(--primary-weak);
  color: var(--primary-strong);
  font-family: serif;
  font-size: 24px;
}

.cover-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.op-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.op-row :deep(.el-button + .el-button) {
  margin-left: 0;
}
</style>
