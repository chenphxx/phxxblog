<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { mediaApi, settingsApi } from '@/api'
import MarkdownView from '@/components/MarkdownView.vue'
import { countWords } from '@/utils/textStats'

/** 三类"行列表"共用同一份列结构, 只有备案信息会多渲染一列可选图标 */
interface LinkRow {
  name: string
  url: string
  icon?: string
}

/** 前台展示开关: 名称与一句说明由它驱动, 数组顺序即页面上的顺序 */
interface FrontModule {
  key: 'show_readme' | 'show_contributions' | 'show_history' | 'show_session' | 'show_kanbanniang'
  label: string
  desc: string
}

/** 行列表的列定义: 三处列表结构同构, 只有文案与列数不同, 模板里只写一份 */
interface LinkList {
  key: 'social_links' | 'website_links' | 'beian_info'
  label: string
  addText: string
  namePlaceholder: string
  urlPlaceholder: string
  /** 是否多渲染一列"图标" */
  hasIcon: boolean
  /** 该列表是否只在前台对管理员展示(用于可见性说明) */
  adminOnly?: boolean
}

/** README 超过这个行数就折叠 */
const README_ROWS = 20
/** README 文本域的最小行数(空内容时也不至于只剩一条缝) */
const README_MIN_ROWS = 3

const form = ref({
  site_name: '',
  site_title: '',
  site_desc: '',
  site_keywords: '',
  site_icon: '',
  site_bio: '',
  site_readme: '',
  show_readme: true,
  show_contributions: true,
  show_history: true,
  show_session: true,
  show_kanbanniang: true,
  footer_text: '',
  tech_tags: [] as string[],
  social_links: [] as LinkRow[],
  website_links: [] as LinkRow[],
  beian_info: [] as LinkRow[],
})
/** 最近一次载入/保存后的表单快照, 与当前表单对比即可判断是否有未保存的修改 */
const snapshot = ref(JSON.stringify(form.value))
const saving = ref(false)
const uploadingIcon = ref(false)
/** README 是否已展开; 折叠只在内容超过 README_ROWS 行时生效 */
const readmeExpanded = ref(false)
/** README 是否切到渲染预览 */
const readmePreview = ref(false)

/** 布尔设置(数据库中存 1/0), 缺省按 true 处理 */
function parseBool(raw: string | undefined | null, fallback = true): boolean {
  if (raw === undefined || raw === null || raw === '') return fallback
  return ['1', 'true', 'yes', 'on'].includes(String(raw).toLowerCase())
}

function parseArray<T>(raw: string | undefined, fallback: T): T {
  if (!raw) return fallback
  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

/** 序列化当前表单, 用于和快照比较 */
function currentSnapshot(): string {
  return JSON.stringify(form.value)
}

/** 是否存在未保存的修改 */
const dirty = computed(() => currentSnapshot() !== snapshot.value)

/** README 的逻辑行数(按换行符计) */
const readmeLineCount = computed(() => (form.value.site_readme ? form.value.site_readme.split('\n').length : 0))
/** 超过 README_ROWS 行才有折叠/展开这回事 */
const readmeFoldable = computed(() => readmeLineCount.value > README_ROWS)
/** 当前是否处于折叠展示(内容超长且未展开) */
const readmeCollapsed = computed(() => readmeFoldable.value && !readmeExpanded.value)
/** README 字数统计 */
const readmeWords = computed(() => countWords(form.value.site_readme))
/**
 * 高度始终跟着内容走(短内容不留空白), 只有"内容超过 README_ROWS 行且未展开"时才加上限,
 * 超出的部分靠 scoped 样式裁掉、并叠一层底部渐隐; 两种状态都不会出现右侧滚动条。
 *
 * 上限只按"逻辑行数"启用: 行数没超时干脆不封顶, 免得长段落自动换行后撑过 README_ROWS 行、
 * 在折叠态被悄悄裁掉又没有展开按钮可点。
 */
const readmeAutosize = computed(() => {
  if (readmeExpanded.value || !readmeFoldable.value) return { minRows: README_MIN_ROWS }
  return { minRows: README_MIN_ROWS, maxRows: README_ROWS }
})

/** 前台展示开关 */
const frontModules: FrontModule[] = [
  { key: 'show_readme', label: '主页 README 模块', desc: '首页的「关于」区块, 内容取自上面的主页 README' },
  { key: 'show_contributions', label: '文章发布记录(贡献热力图)', desc: '按年统计发文数量的热力图' },
  { key: 'show_history', label: '程序员历史上的今天', desc: '每天更新的历史事件卡片' },
  { key: 'show_session', label: 'session 终端卡片', desc: '首页顶部的终端风格卡片, 含一言' },
  { key: 'show_kanbanniang', label: '看板娘', desc: '全站的 Live2D 看板娘浮层, 关掉后顶栏的形象切换也一起隐藏' },
]

/** 页脚与链接里的三处行列表 */
const linkLists: LinkList[] = [
  {
    key: 'social_links',
    label: '社交链接(名称 + 链接)',
    addText: '添加链接',
    namePlaceholder: '名称(如 GitHub)',
    urlPlaceholder: '链接(https://...)',
    hasIcon: false,
  },
  {
    key: 'website_links',
    label: '网站链接(名称 + 链接, 名称留空自动取网站名)',
    addText: '添加链接',
    namePlaceholder: '名称(留空自动取网站名)',
    urlPlaceholder: '链接(https://...)',
    hasIcon: false,
    adminOnly: true,
  },
  {
    key: 'beian_info',
    label: '网站备案信息(选填, 显示在页脚)',
    addText: '添加备案信息',
    namePlaceholder: '备案名称(如: 蜀ICP备xxxxxxxx号-1)',
    urlPlaceholder: '链接(如: https://beian.miit.gov.cn/)',
    hasIcon: true,
  },
]

/** 在指定行列表末尾追加一行空数据 */
function addLinkRow(key: LinkList['key']) {
  form.value[key].push({ name: '', url: '' })
}

async function load() {
  const data = await settingsApi.all()
  form.value = {
    site_name: data.site_name || '',
    site_title: data.site_title || '',
    site_desc: data.site_desc || '',
    site_keywords: data.site_keywords || '',
    site_icon: data.site_icon || '',
    site_bio: data.site_bio || '',
    site_readme: data.site_readme || '',
    show_readme: parseBool(data.show_readme),
    show_contributions: parseBool(data.show_contributions),
    show_history: parseBool(data.show_history),
    show_session: parseBool(data.show_session),
    show_kanbanniang: parseBool(data.show_kanbanniang),
    footer_text: data.footer_text ?? '© {year} {site_name} · Vue3 + FastAPI',
    tech_tags: parseArray<string[]>(data.tech_tags, []),
    social_links: parseArray<LinkRow[]>(data.social_links, []),
    website_links: parseArray<LinkRow[]>(data.website_links, []),
    beian_info: parseArray<LinkRow[]>(data.beian_info, []),
  }
  readmeExpanded.value = false
  snapshot.value = currentSnapshot()
}

async function uploadIcon(options: { file: File }) {
  uploadingIcon.value = true
  try {
    const media = await mediaApi.upload(options.file)
    form.value.site_icon = media.url
    ElMessage.success('图标已上传')
  } finally {
    uploadingIcon.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      ...form.value,
      // 开关按 1/0 存库, 便于前台直接判断
      show_readme: form.value.show_readme ? '1' : '0',
      show_contributions: form.value.show_contributions ? '1' : '0',
      show_history: form.value.show_history ? '1' : '0',
      show_session: form.value.show_session ? '1' : '0',
      show_kanbanniang: form.value.show_kanbanniang ? '1' : '0',
    }
    await settingsApi.update(payload)
    snapshot.value = currentSnapshot()
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h2>系统设置</h2>

    <div class="admin-toolbar settings-toolbar">
      <span v-if="dirty" class="muted">有未保存的修改</span>
      <div class="admin-toolbar-actions">
        <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
      </div>
    </div>

    <div class="settings-cards">
      <div class="card">
        <h3>基础信息 <span class="vis-badge">公开可见</span></h3>
        <p class="muted section-hint">站点名称、标签页标题与图标显示在浏览器标签页, 个人简介显示在首页的个人资料卡</p>
        <el-form label-position="top">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="站点名称">
                <el-input v-model="form.site_name" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="浏览器标签页名称(留空则使用站点名称)">
                <el-input v-model="form.site_title" placeholder="显示在浏览器标签页上的文字" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="站点图标(浏览器标签页图标, 可上传或填写 URL)">
            <div class="icon-row">
              <img v-if="form.site_icon" :src="form.site_icon" alt="站点图标预览" class="icon-preview" />
              <span v-else class="icon-preview icon-preview--empty" title="尚未设置站点图标" />
              <el-input v-model="form.site_icon" placeholder="/assets/uploads/... 或 https://..." />
              <el-upload :show-file-list="false" :http-request="uploadIcon" accept="image/*">
                <el-button :loading="uploadingIcon">本地上传</el-button>
              </el-upload>
            </div>
          </el-form-item>
          <el-form-item label="个人简介">
            <el-input v-model="form.site_bio" type="textarea" :rows="2" />
          </el-form-item>
        </el-form>
      </div>

      <div class="card">
        <h3>SEO <span class="vis-badge">公开可见</span></h3>
        <p class="muted section-hint">站点描述会写进 RSS 订阅摘要, 关键词目前未在前台页面输出</p>
        <el-form label-position="top">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="SEO 关键词">
                <el-input v-model="form.site_keywords" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="站点描述(SEO)">
                <el-input v-model="form.site_desc" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>

      <div class="card">
        <h3>首页内容 <span class="vis-badge">公开可见</span></h3>
        <p class="muted section-hint">技术标签与主页 README 显示在首页, 下方开关控制各模块是否展示</p>
        <el-form label-position="top">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="技术标签(输入后回车新增)">
                <el-select
                  v-model="form.tech_tags"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  :reserve-keyword="false"
                  placeholder="如 Python、Vue, 输入后回车"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item>
            <template #label>
              <span>主页 README(GitHub 风格, 支持 Markdown)</span>
              <span class="muted form-label-meta">{{ readmeWords }} 字</span>
              <span class="form-label-switch">
                <el-switch v-model="readmePreview" size="small" />
                <span class="muted">预览</span>
              </span>
            </template>
            <div v-if="readmePreview" class="readme-preview">
              <MarkdownView :content="form.site_readme" />
            </div>
            <template v-else>
              <div class="readme-wrap" :class="{ 'is-collapsed': readmeCollapsed }">
                <!--
                  key 随折叠状态变化: el-input 只在 modelValue 变化时重算 autosize 高度,
                  展开那一刻值没有变, 不重建的话高度会停在 20 行、把后面的行裁掉。
                -->
                <el-input
                  :key="readmeExpanded ? 'expanded' : 'collapsed'"
                  v-model="form.site_readme"
                  class="readme-input"
                  type="textarea"
                  :autosize="readmeAutosize"
                  placeholder="介绍自己/项目, 支持 Markdown 语法"
                />
              </div>
              <div v-if="readmeFoldable" class="readme-toggle">
                <el-button text type="primary" size="small" @click="readmeExpanded = !readmeExpanded">
                  {{ readmeExpanded ? '收起' : `展开全部(共 ${readmeLineCount} 行)` }}
                </el-button>
              </div>
            </template>
          </el-form-item>
          <el-form-item label="前台展示">
            <div class="switch-grid">
              <label v-for="item in frontModules" :key="item.key" class="switch-item">
                <el-switch v-model="form[item.key]" />
                <span class="switch-text">
                  <span class="switch-label">{{ item.label }}</span>
                  <span class="muted switch-desc">{{ item.desc }}</span>
                </span>
              </label>
            </div>
          </el-form-item>
        </el-form>
      </div>

      <div class="card">
        <h3>页脚与链接 <span class="vis-badge">公开可见</span></h3>
        <p class="muted section-hint">社交链接显示在首页的个人资料卡, 网站链接仅管理员可见, 备案与版权信息显示在页脚</p>
        <el-form label-position="top">
          <el-form-item v-for="list in linkLists" :key="list.key">
            <template #label>
              <span>{{ list.label }}</span>
              <span v-if="list.adminOnly" class="vis-badge is-admin">仅管理员可见</span>
            </template>
            <div class="link-list">
              <div v-for="(row, index) in form[list.key]" :key="index" class="link-row">
                <span class="link-row-index">{{ index + 1 }}</span>
                <el-input v-model="row.name" class="link-row-name" :placeholder="list.namePlaceholder" />
                <el-input v-model="row.url" :placeholder="list.urlPlaceholder" />
                <el-input v-if="list.hasIcon" v-model="row.icon" class="link-row-icon" placeholder="图标(选填)" />
                <el-button
                  class="link-row-remove"
                  text
                  :icon="Delete"
                  title="删除这一行"
                  @click="form[list.key].splice(index, 1)"
                />
              </div>
              <el-button size="small" @click="addLinkRow(list.key)">{{ list.addText }}</el-button>
            </div>
          </el-form-item>
          <el-form-item label="页脚版权信息">
            <el-input v-model="form.footer_text" placeholder="留空则不显示, 支持 {year} 与 {site_name} 占位符" />
            <div class="muted form-hint">
              支持 <code>{year}</code> 与 <code>{site_name}</code> 占位符, 留空则页脚不显示版权信息
            </div>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/*
 * 设置页是后台里最长的表单: 工具条吸顶后, 滚到页脚/备案处也能直接保存。
 *
 * sticky 的吸附边界是滚动容器(.admin-main)的内容盒, 而它自带 20px 上内边距,
 * 若直接把 top 设为 0, 工具条上方会留出一条 20px 的缝, 卡片文字会从缝里露出来;
 * 用 top: -20px 抵消这段内边距即可(卡片不会延伸到这里, 所以不会有内容穿透)。
 */
.settings-toolbar {
  position: sticky;
  top: -20px;
  z-index: 2;
  margin-bottom: 16px;
  padding: 12px 0 14px;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}

/* 每张卡片一个配置域, 卡片间距与个人资料页保持一致 */
.settings-cards {
  display: grid;
  gap: 20px;
}

/* 卡片标题下的一句说明 */
.section-hint {
  margin: -4px 0 16px;
}

/* 配置域的可见性说明: 默认"公开可见", is-admin 表示仅管理员可见 */
.vis-badge {
  margin-left: 8px;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 400;
  vertical-align: 2px;
  color: var(--primary);
  background: var(--primary-weak);
}
.vis-badge.is-admin {
  color: var(--warn);
  background: color-mix(in srgb, var(--warn) 12%, transparent);
}

/* 站点图标: 预览 + 地址输入 + 上传按钮同一行, 输入框占满剩余宽度 */
.icon-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}
.icon-row .el-input {
  flex: 1;
}
.icon-preview {
  flex: 0 0 32px;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  object-fit: contain;
}
/* 未设置图标时占位, 避免这一行的高度随有无图标跳动 */
.icon-preview--empty {
  border: 1px dashed var(--border-strong);
  background: var(--code-bg);
}

/*
 * 右侧不允许出现滚动条, 所以把 textarea 的 overflow 压成 hidden。
 * el-input 在用 maxRows 封顶时会把 overflow-y 写成行内样式, 必须带 !important 才盖得住。
 */
.readme-input :deep(textarea) {
  overflow-y: hidden !important;
}
.readme-wrap {
  position: relative;
  width: 100%;
}
/* 折叠时做一层底部渐隐, 顺带遮住被裁到一半的那一行 */
.readme-wrap.is-collapsed::after {
  content: '';
  position: absolute;
  right: 1px;
  bottom: 1px;
  left: 1px;
  height: 26px;
  pointer-events: none;
  border-radius: 0 0 var(--radius-sm) var(--radius-sm);
  background: linear-gradient(to bottom, transparent, var(--card-bg));
}
.readme-toggle {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}
.readme-preview {
  width: 100%;
  padding: 4px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--card-bg);
}

/* el-form-item 的 label 插槽里混排标题/字数/预览开关 */
.form-label-meta {
  margin-left: 8px;
  font-size: 12px;
}
.form-label-switch {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 16px;
  font-size: 12px;
}
/* 字段下方的补充说明: 统一字号, 不再写内联样式 */
.form-hint {
  font-size: 12px;
  line-height: 1.6;
}

/* 前台展示: 两列网格, 每格是"开关 + 名称 + 一句说明" */
.switch-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 24px;
  width: 100%;
}
.switch-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
}
.switch-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.switch-label {
  font-size: 14px;
  color: var(--el-text-color-regular, var(--text));
}
.switch-desc {
  font-size: 12px;
  line-height: 1.5;
}

/* 行列表: 序号 + 名称(定宽) + 链接(自适应) + 可选图标 + 删除 */
.link-list {
  width: 100%;
  /* 序号列宽与行间距抽成变量: "添加"按钮要按这两项缩进, 才能和上面名称输入框的左边缘对齐 */
  --link-index-width: 16px;
  --link-row-gap: 10px;
}
.link-row {
  display: flex;
  align-items: center;
  gap: var(--link-row-gap);
  margin-bottom: 10px;
}
.link-row-index {
  flex: 0 0 var(--link-index-width);
  text-align: right;
  font-size: 12px;
  color: var(--muted);
}
.link-row .el-input {
  flex: 1 1 auto;
}
/* 名称列固定 200px: 内联 width 会被同一行 .el-input 的 flex 覆盖, 所以用 flex-basis 表达 */
.link-row .el-input.link-row-name {
  flex: 0 0 200px;
}
.link-row .el-input.link-row-icon {
  flex: 0 0 150px;
}
/* "添加"按钮跳过序号列, 与上面输入行的名称框左对齐 */
.link-list > .el-button {
  margin-left: calc(var(--link-index-width) + var(--link-row-gap));
}
/* 每行常驻一个红色"删除"整屏都是噪音, 默认灰、鼠标移到该行才变红 */
.link-row .link-row-remove {
  flex: 0 0 auto;
  color: var(--muted);
}
.link-row:hover .link-row-remove {
  color: var(--danger);
}
</style>
