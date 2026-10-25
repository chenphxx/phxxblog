<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { contributionsApi, diaryApi } from '@/api'
import type { ContributionPoint, DiaryEntry } from '@/types'
import MarkdownView from '@/components/MarkdownView.vue'
import VditorEditor from '@/components/VditorEditor.vue'
import ContributionsChart from '@/components/ContributionsChart.vue'
import { useAuthStore } from '@/stores/auth'
import { useModulesStore } from '@/stores/modules'
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
const modules = useModulesStore()
const auth = useAuthStore()

/**
 * 是否能管理日记(新增/编辑/删除/导入导出)
 *
 * 管理动作在后端要求 diary:manage 权限, 而项目里只有管理员角色持有它 - 因此前台按
 * 管理员身份隐藏这些入口 日记模块配成公开时, 访客仍能看列表, 但看不到管理按钮
 */
const canManage = computed(() => auth.user?.role_codes.includes('admin') ?? false)

const WEEKDAY_LABELS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

/** 发布记录模块未启用时, 日记的热力图取不到数据, 这块整体不渲染(接口会 404) */
/**
 * 日记页要不要展示发布记录
 *
 * 模块未启用时接口会 404; 页面级的"日记页展示"开关关掉时也不取数(与首页那块各自独立)
 */
const contributionsEnabled = computed(
  () => modules.isEnabled('contributions') && modules.moduleConfig('contributions').show_on_diary !== false,
)

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
 * 本地日期(YYYY-MM-DD)
 * 不能用 toISOString(): 它按 UTC 取日期, 在东八区 00:00~08:00 之间会得到"昨天"
 */
function today(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/**
 * @brief 日记日期对应的星期
 *
 * @param value 日记归属日期(YYYY-MM-DD)
 * @return 星期文案; 日期不合法时返回空串
 */
function weekdayLabel(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  return Number.isNaN(date.getTime()) ? '' : (WEEKDAY_LABELS[date.getDay()] ?? '')
}

/**
 * @brief 日记的创建时刻
 *
 * @param value 创建时间
 * @return HH:mm; 无法解析时不展示
 */
function createdTime(value: string): string {
  const formatted = formatDateTime(value)
  return formatted.length >= 16 ? formatted.slice(11, 16) : ''
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
  // 发布记录模块被禁用时接口会 404: 这里就不取数, 也不渲染下面的热力图
  if (!contributionsEnabled.value) {
    contributions.value = []
    return
  }
  contributions.value = await contributionsApi.contributions({
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
  <div v-loading="loading" class="page-container">
    <div class="page-head diary-header">
      <div>
        <h1 class="page-title">日记</h1>
        <p class="page-subtitle">按时间记录日常与片刻</p>
      </div>
      <div v-if="canManage" class="diary-actions-bar">
        <el-button @click="io.importDialog = true">导入日记</el-button>
        <el-button @click="io.openExportDialog">导出日记</el-button>
        <el-button type="primary" @click="openCreate">新增日记</el-button>
      </div>
    </div>

    <!-- 日记贡献热力图 -->
    <div v-if="contributionsEnabled" class="card" style="margin-top: 16px">
      <p class="eyebrow" style="margin: 0 0 12px">ACTIVITY / 日记记录</p>
      <ContributionsChart
        :points="contributions"
        :years="contributionYears"
        :year="contributionYear"
        @update:year="contributionYear = $event"
      />
    </div>

    <!-- 按年份和月份分组的日记卡片 -->
    <div class="diary-body">
      <aside class="diary-nav" aria-label="日记时间导航">
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
            <div class="month-heading">
              <h3 :id="`diary-${month}`" class="month-title">{{ Number(month.slice(5, 7)) }} 月</h3>
              <span class="month-count">{{ (groups.get(month) || []).length }} 篇</span>
            </div>
            <div class="diary-list">
              <article v-for="entry in groups.get(month) || []" :key="entry.id" class="card diary-card">
                <header class="diary-card-head">
                  <time :datetime="entry.entry_date" class="diary-date">
                    <span class="diary-date-day">{{ Number(entry.entry_date.slice(8, 10)) }}</span>
                    <span class="diary-date-copy">
                      <span class="diary-date-label">{{ entry.entry_date.slice(0, 7).replace('-', ' / ') }}</span>
                      <span class="diary-date-note">
                        {{ weekdayLabel(entry.entry_date) }}
                        <template v-if="createdTime(entry.created_at)">
                          · 写于 {{ createdTime(entry.created_at) }}
                        </template>
                      </span>
                    </span>
                  </time>
                  <div v-if="canManage" class="diary-actions">
                    <el-button text size="small" @click="openEdit(entry)">编辑</el-button>
                    <el-button text size="small" type="danger" @click="remove(entry)">删除</el-button>
                  </div>
                </header>
                <div class="diary-content">
                  <MarkdownView :content="entry.content_md" />
                </div>
              </article>
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
  flex-wrap: wrap;
  margin-bottom: var(--space-6);
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
  top: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  max-height: calc(100vh - var(--space-12));
  overflow-y: auto;
}
.nav-year {
  min-width: 0;
}
.nav-year-title {
  display: block;
  margin-bottom: var(--space-1);
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
}
.nav-month {
  display: block;
  padding: 3px 0 3px 12px;
  border-left: 1px solid var(--border);
  color: var(--muted);
  font-size: 12.5px;
}
.nav-month:hover,
.nav-year-title:hover {
  color: var(--link);
  text-decoration: none;
}
.diary-main {
  min-width: 0;
}
.year-title {
  margin: 0 0 var(--space-5);
  border-bottom: 2px solid var(--border);
  padding-bottom: var(--space-2);
  font-size: 24px;
  font-weight: 650;
  letter-spacing: -0.03em;
  scroll-margin-top: var(--space-6);
}
.year-title:not(:first-child) {
  margin-top: var(--space-10);
}
.month-block + .month-block {
  margin-top: var(--space-8);
}
.month-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}
.month-title {
  margin: 0;
  color: var(--primary);
  font-size: 16px;
  font-weight: 600;
  scroll-margin-top: var(--space-6);
}
.month-count {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 12px;
}
.diary-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.diary-card {
  position: relative;
  overflow: hidden;
  padding: 0;
  transition:
    border-color var(--dur) var(--ease),
    box-shadow var(--dur) var(--ease);
}
.diary-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg, var(--primary), color-mix(in srgb, var(--primary) 28%, transparent));
  opacity: 0.72;
}
.diary-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-float);
}
.diary-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid color-mix(in srgb, var(--border) 72%, transparent);
  background: color-mix(in srgb, var(--primary) 3%, var(--card-bg));
}
.diary-date {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}
.diary-date-day {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 42px;
  height: 42px;
  border-radius: calc(var(--radius-control) + 3px);
  background: var(--primary-weak);
  color: var(--primary-strong);
  font-family: var(--font-mono);
  font-size: 19px;
  font-weight: 700;
  line-height: 1;
}
.diary-date-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.diary-date-label {
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.diary-date-note {
  color: var(--muted);
  font-size: 12px;
}
.diary-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
  flex-shrink: 0;
}
.diary-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}
.diary-content {
  padding: var(--space-5) var(--space-6) var(--space-6);
}
.diary-content :deep(.markdown-body) {
  font-size: 15.5px;
  line-height: 1.9;
}
.diary-content :deep(.markdown-body > :first-child) {
  margin-top: 0;
}
.diary-content :deep(.markdown-body > :last-child) {
  margin-bottom: 0;
}
@media (max-width: 900px) {
  .diary-body {
    grid-template-columns: 1fr;
    gap: var(--space-6);
  }
  .diary-nav {
    position: static;
    flex-direction: row;
    flex-wrap: wrap;
    gap: var(--space-2) var(--space-5);
    max-height: none;
  }
}
@media (max-width: 600px) {
  .diary-card-head {
    padding: var(--space-4);
  }
  .diary-content {
    padding: var(--space-4);
  }
}
</style>
