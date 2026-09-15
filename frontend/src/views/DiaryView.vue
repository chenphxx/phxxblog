<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { diaryApi, statsApi } from '@/api'
import type { ContributionPoint, DiaryEntry } from '@/types'
import MarkdownView from '@/components/MarkdownView.vue'
import VditorEditor from '@/components/VditorEditor.vue'
import ContributionsChart from '@/components/ContributionsChart.vue'
import MetaIcon from '@/components/MetaIcon.vue'
import ImportExportDialogs from '@/components/ImportExportDialogs.vue'
import { useImportExport } from '@/composables/useImportExport'
import { formatDateTime } from '@/utils/datetime'

const entries = ref<DiaryEntry[]>([])
const contributions = ref<ContributionPoint[]>([])
const loading = ref(true)
const dialog = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = ref({ content_md: '', entry_date: today() })
const contributionYear = ref<number | null>(null)
/** 编辑器实例: 保存时直接取编辑器内容, 避免 v-model 尚未同步导致"点两次才保存" */
const editorRef = ref<InstanceType<typeof VditorEditor> | null>(null)

const io = useImportExport({
  filePrefix: 'phxxblog-diaries',
  entity: '日记',
  unit: '条',
  exportMessage: () => '已导出全部日记',
  exportFile: (fmt) => diaryApi.exportDiaries([], fmt),
  checkImports: (files) => diaryApi.checkImportDiaries(files),
  submitImports: (files, onDuplicate) => diaryApi.importDiaries(files, onDuplicate),
  onImported: load,
})
const contributionYears = computed(() => {
  const current = new Date().getFullYear()
  return Array.from({ length: 6 }, (_, i) => current - i)
})

/** 按 年-月 分组用于时间轴 */
const groups = computed(() => {
  const map = new Map<string, DiaryEntry[]>()
  for (const entry of entries.value) {
    const key = entry.entry_date.slice(0, 7)
    const list = map.get(key) || []
    list.push(entry)
    map.set(key, list)
  }
  return map
})

const groupsList = computed(() => Array.from(groups.value.entries()))

/**
 * 本地日期(YYYY-MM-DD)。
 * 不能用 toISOString(): 它按 UTC 取日期, 在东八区 00:00~08:00 之间会得到"昨天"。
 */
function today(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/** 按年份二次分组, 生成侧边栏锚点 */
const yearGroups = computed(() => {
  const map = new Map<string, string[]>()
  for (const [month] of groupsList.value) {
    const year = month.slice(0, 4)
    const list = map.get(year) || []
    list.push(month)
    map.set(year, list)
  }
  return Array.from(map.entries())
})

function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function load() {
  loading.value = true
  try {
    const diaryData = await diaryApi.list({ page: 1, page_size: 100 })
    entries.value = diaryData.items
    await loadContributions()
  } finally {
    loading.value = false
  }
}

async function loadContributions() {
  contributions.value = await statsApi.contributions({
    source: 'diary',
    weeks: 52,
    year: contributionYear.value || undefined,
  })
}

watch(contributionYear, loadContributions)

function openCreate() {
  editingId.value = null
  form.value = { content_md: '', entry_date: today() }
  dialog.value = true
}

function openEdit(entry: DiaryEntry) {
  editingId.value = entry.id
  form.value = { content_md: entry.content_md, entry_date: entry.entry_date }
  dialog.value = true
}

async function save() {
  // 以编辑器内容为准: 中文输入法组字期间 Vditor 不会回调 input, 此时 v-model 可能还是空的
  const content = editorRef.value?.getValue() ?? form.value.content_md
  if (!content.trim()) {
    ElMessage.warning('请输入日记内容')
    return
  }
  saving.value = true
  try {
    const payload = { ...form.value, content_md: content }
    if (editingId.value) {
      await diaryApi.update(editingId.value, payload)
    } else {
      await diaryApi.create(payload)
    }
    // 同步回模型, 避免下次打开时编辑器与表单不一致
    form.value.content_md = content
    ElMessage.success('日记已保存')
    dialog.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(entry: DiaryEntry) {
  await ElMessageBox.confirm('确定删除这条日记吗?', '确认', { type: 'warning' })
  await diaryApi.remove(entry.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="diary-header">
      <div>
        <p class="eyebrow" style="margin: 0 0 4px">diary — 日记</p>
        <h1 style="margin: 0">日记</h1>
      </div>
      <div class="diary-actions-bar">
        <el-button @click="io.importDialog = true">导入日记</el-button>
        <el-button @click="io.openExportDialog">导出日记</el-button>
        <el-button type="primary" @click="openCreate">新增日记</el-button>
      </div>
    </div>

    <!-- 日记贡献热力图 -->
    <div class="card" style="margin-top: 16px">
      <p class="eyebrow" style="margin: 0 0 12px">activity — 日记记录</p>
      <ContributionsChart
        :points="contributions"
        :years="contributionYears"
        :year="contributionYear"
        @update:year="contributionYear = $event"
      />
    </div>

    <!-- 时间轴(类似归档页) -->
    <div class="diary-body">
      <aside class="diary-nav card">
        <div v-for="[year, months] in yearGroups" :key="year" class="nav-year">
          <a href="#" class="nav-year-title" @click.prevent="scrollToId(`diary-${year}`)">{{ year }}</a>
          <a
            v-for="month in months"
            :key="month"
            href="#"
            class="nav-month"
            @click.prevent="scrollToId(`diary-${month}`)"
          >
            {{ month.slice(5, 7) }} 月
          </a>
        </div>
      </aside>

      <main class="diary-main">
        <template v-for="[year, months] in yearGroups" :key="year">
          <h2 :id="`diary-${year}`" class="year-title">{{ year }}</h2>
          <div v-for="month in months" :key="month" class="month-block">
            <h3 :id="`diary-${month}`" class="month-title">{{ month }}</h3>
            <div class="timeline">
              <div v-for="entry in groups.get(month) || []" :key="entry.id" class="timeline-item">
                <div class="timeline-date muted">
                  <MetaIcon name="calendar" />
                  <span>{{ formatDateTime(entry.created_at) }}</span>
                </div>
                <div class="card diary-card">
                  <MarkdownView :content="entry.content_md" />
                  <div class="diary-actions">
                    <el-button size="small" @click="openEdit(entry)">编辑</el-button>
                    <el-button size="small" type="danger" @click="remove(entry)">删除</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
        <el-empty v-if="!loading && entries.length === 0" description="还没有日记, 点击右上角开始记录" />
      </main>
    </div>

    <ImportExportDialogs
      :io="io"
      import-title="导入日记"
      dup-title="检测到重复日记"
      export-title="导出日记"
      import-hint="支持 .md 文件或 .zip 压缩包(可多选)。zip 内需包含 .md 日记文件; 日记图片可放在任意目录, 在正文中用相对路径引用(如 images/xxx.png), 导入时图片会一并上传并自动改写为可访问的 URL。支持 YAML frontmatter 元信息: date(YYYY-MM-DD) / created_at。未提供日期时取文件名开头的日期, 仍取不到则记为今天。导入前会按正文查重(忽略空白与图片地址差异), 有重复时可选择仅导入不重复或全部导入。"
      dup-hint="重复依据为日记正文(忽略空白与图片地址差异)。可跳过重复内容, 也可全部导入。"
      export-hint="导出全部日记为 zip 压缩包, 正文引用的图片会一并打包, 并自动改写为相对路径。"
    />

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialog" :title="editingId ? '编辑日记' : '新增日记'" width="860px" top="5vh">
      <el-form label-position="top">
        <el-form-item label="日期">
          <el-date-picker v-model="form.entry_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="内容(Markdown, 支持图片/视频/附件/链接)">
          <VditorEditor ref="editorRef" v-model="form.content_md" :height="360" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.diary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.diary-actions-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.diary-body {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 20px;
  align-items: start;
  margin-top: 20px;
}
.diary-nav {
  position: sticky;
  top: 76px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}
.nav-year {
  margin-bottom: 12px;
}
.nav-year-title {
  display: block;
  font-weight: 700;
  margin-bottom: 6px;
  font-family: var(--font-mono);
  font-size: 14px;
}
.nav-month {
  display: block;
  padding: 3px 0 3px 12px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 12px;
}
.year-title {
  border-bottom: 2px solid var(--border);
  padding-bottom: 8px;
  font-size: 22px;
}
.month-title {
  color: var(--primary);
  font-family: var(--font-mono);
  font-size: 15px;
}
.timeline {
  position: relative;
  padding-left: 24px;
}
.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--border);
}
.timeline-item {
  position: relative;
  margin-bottom: 20px;
}
.timeline-item::before {
  content: '';
  position: absolute;
  left: -22px;
  top: 18px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
}
.timeline-date {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  margin-bottom: 4px;
}
.diary-card {
  padding: 12px;
}
.diary-actions {
  margin-top: 8px;
  text-align: right;
}
@media (max-width: 900px) {
  .diary-body {
    grid-template-columns: 1fr;
  }
  .diary-nav {
    position: static;
  }
}
</style>
