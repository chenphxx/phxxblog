<script setup lang="ts">
import { computed, ref } from 'vue'
import MarkdownView from '@/components/MarkdownView.vue'
import { countWords } from '@/utils/textStats'

/** 前台展示开关: 名称与一句说明由它驱动, 数组顺序即页面上的顺序 */
interface FrontModule {
  key: 'show_readme' | 'show_contributions' | 'show_history' | 'show_session' | 'show_kanbanniang'
  label: string
  desc: string
}

/** README 超过这个行数就折叠 */
const README_ROWS = 20
/** README 文本域的最小行数(空内容时也不至于只剩一条缝) */
const README_MIN_ROWS = 3

/**
 * @brief 系统设置 - 首页内容卡片(技术标签 / 主页 README / 前台展示开关)
 *
 * 表单状态由页面持有, README 的折叠与预览只是本卡片的展示状态, 因此放在这里
 */
const props = defineProps<{
  form: {
    tech_tags: string[]
    site_readme: string
    show_readme: boolean
    show_contributions: boolean
    show_history: boolean
    show_session: boolean
    show_kanbanniang: boolean
  }
}>()

/** 表单对象由页面持有, 这里取别名后直接读写其字段(与 PostFormFields 同一套做法) */
const form = props.form

/** README 是否已展开; 折叠只在内容超过 README_ROWS 行时生效 */
const readmeExpanded = ref(false)
/** README 是否切到渲染预览 */
const readmePreview = ref(false)

/** README 的逻辑行数(按换行符计) */
const readmeLineCount = computed(() => (form.site_readme ? form.site_readme.split('\n').length : 0))
/** 超过 README_ROWS 行才有折叠/展开这回事 */
const readmeFoldable = computed(() => readmeLineCount.value > README_ROWS)
/** 当前是否处于折叠展示(内容超长且未展开) */
const readmeCollapsed = computed(() => readmeFoldable.value && !readmeExpanded.value)
/** README 字数统计 */
const readmeWords = computed(() => countWords(form.site_readme))
/**
 * 高度始终跟着内容走(短内容不留空白), 只有"内容超过 README_ROWS 行且未展开"时才加上限,
 * 超出的部分靠 scoped 样式裁掉, 并叠一层底部渐隐; 两种状态都不会出现右侧滚动条
 *
 * 上限只按"逻辑行数"启用: 行数没超时干脆不封顶, 免得长段落自动换行后撑过 README_ROWS 行,
 * 在折叠态被悄悄裁掉又没有展开按钮可点
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
</script>

<template>
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
              展开那一刻值没有变, 不重建的话高度会停在 20 行, 把后面的行裁掉
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
</template>

<style scoped>
/*
 * 右侧不允许出现滚动条, 所以把 textarea 的 overflow 压成 hidden
 * el-input 在用 maxRows 封顶时会把 overflow-y 写成行内样式, 必须带 !important 才盖得住
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
</style>
