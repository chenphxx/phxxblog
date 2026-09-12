<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { diaryApi, statsApi } from '@/api'
import type { ContributionPoint, DiaryEntry } from '@/types'
import MarkdownView from '@/components/MarkdownView.vue'
import VditorEditor from '@/components/VditorEditor.vue'
import ContributionsChart from '@/components/ContributionsChart.vue'
import { formatDateTime } from '@/utils/datetime'

const entries = ref<DiaryEntry[]>([])
const contributions = ref<ContributionPoint[]>([])
const loading = ref(true)
const dialog = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = ref({ content_md: '', entry_date: new Date().toISOString().slice(0, 10) })
const contributionYear = ref<number | null>(null)
const importDialog = ref(false)
const importing = ref(false)
const importFiles = ref<File[]>([])
const dupDialog = ref(false)
const duplicates = ref<string[]>([])
const duplicateCount = ref(0)
const duplicateTotal = ref(0)
const exportDialog = ref(false)
const exporting = ref(false)
const exportFmt = ref<'markdown' | 'html'>('markdown')
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
  form.value = { content_md: '', entry_date: new Date().toISOString().slice(0, 10) }
  dialog.value = true
}

function openEdit(entry: DiaryEntry) {
  editingId.value = entry.id
  form.value = { content_md: entry.content_md, entry_date: entry.entry_date }
  dialog.value = true
}

async function save() {
  if (!form.value.content_md.trim()) {
    ElMessage.warning('请输入日记内容')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await diaryApi.update(editingId.value, form.value)
    } else {
      await diaryApi.create(form.value)
    }
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

function openExportDialog() {
  exportFmt.value = 'markdown'
  exportDialog.value = true
}

async function doExport() {
  exporting.value = true
  try {
    const blob = await diaryApi.exportDiaries([], exportFmt.value)
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `phxxblog-diaries-${new Date().toISOString().slice(0, 10)}.zip`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出全部日记')
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
    // 先查重(不写入), 有重复时交给用户决定如何导入
    const check = await diaryApi.checkImportDiaries(importFiles.value)
    if (check.duplicates_count > 0) {
      duplicates.value = check.duplicates
      duplicateCount.value = check.duplicates_count
      duplicateTotal.value = check.total
      importDialog.value = false
      dupDialog.value = true
      return
    }
    await runImport('skip')
  } finally {
    importing.value = false
  }
}

/** onDuplicate: skip=仅导入不重复, all=重复的也一并导入 */
async function runImport(onDuplicate: 'skip' | 'all') {
  importing.value = true
  try {
    const result = await diaryApi.importDiaries(importFiles.value, onDuplicate)
    ElMessage.success(`导入完成: 成功 ${result.imported} 条, 跳过 ${result.skipped} 条`)
    if (result.errors?.length) {
      ElMessage.warning(`部分文件导入失败: ${result.errors.slice(0, 3).join('; ')}`)
    }
    dupDialog.value = false
    importDialog.value = false
    importFiles.value = []
    load()
  } finally {
    importing.value = false
  }
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
        <el-button @click="importDialog = true">导入日记</el-button>
        <el-button @click="openExportDialog">导出日记</el-button>
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
                <div class="timeline-date muted">{{ formatDateTime(entry.created_at) }}</div>
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

    <!-- 导入日记 -->
    <el-dialog v-model="importDialog" title="导入日记" width="600px">
      <el-alert type="info" :closable="false" show-icon>
        <template #title>文件要求</template>
        支持 .md 文件或 .zip 压缩包(可多选)。zip 内需包含 .md 日记文件; 日记图片可放在任意目录,
        在正文中用相对路径引用(如 images/xxx.png), 导入时图片会一并上传并自动改写为可访问的 URL。
        支持 YAML frontmatter 元信息: date(YYYY-MM-DD) / created_at。
        未提供日期时取文件名开头的日期, 仍取不到则记为今天。
        导入前会按正文查重(忽略空白与图片地址差异), 有重复时可选择仅导入不重复或全部导入。
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

    <!-- 导入查重 -->
    <el-dialog v-model="dupDialog" title="检测到重复日记" width="560px">
      <el-alert type="warning" :closable="false" show-icon>
        <template #title>共 {{ duplicateTotal }} 条待导入, 其中 {{ duplicateCount }} 条与已有日记重复</template>
        重复依据为日记正文(忽略空白与图片地址差异)。可跳过重复内容, 也可全部导入。
      </el-alert>
      <ul v-if="duplicates.length" class="import-files">
        <li v-for="(item, index) in duplicates" :key="index">{{ item }}</li>
      </ul>
      <template #footer>
        <el-button @click="dupDialog = false">取消</el-button>
        <el-button :loading="importing" @click="runImport('skip')">仅导入不重复</el-button>
        <el-button type="primary" :loading="importing" @click="runImport('all')">导入全部</el-button>
      </template>
    </el-dialog>

    <!-- 导出日记 -->
    <el-dialog v-model="exportDialog" title="导出日记" width="460px">
      <el-form label-position="top">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFmt">
            <el-radio value="markdown">Markdown(.md)</el-radio>
            <el-radio value="html">HTML(.html)</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <p class="muted">导出全部日记为 zip 压缩包, 正文引用的图片会一并打包, 并自动改写为相对路径。</p>
      <template #footer>
        <el-button @click="exportDialog = false">取消</el-button>
        <el-button type="primary" :loading="exporting" @click="doExport">导出</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialog" :title="editingId ? '编辑日记' : '新增日记'" width="720px" top="5vh">
      <el-form label-position="top">
        <el-form-item label="日期">
          <el-date-picker v-model="form.entry_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="内容(Markdown, 支持图片/视频/附件/链接)">
          <VditorEditor v-model="form.content_md" />
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
