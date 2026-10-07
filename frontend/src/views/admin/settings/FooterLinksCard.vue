<script setup lang="ts">
import { Delete } from '@element-plus/icons-vue'

/** 三类"行列表"共用同一份列结构, 只有备案信息会多渲染一列可选图标 */
interface LinkRow {
  name: string
  url: string
  icon?: string
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

/**
 * @brief 系统设置 - 页脚与链接卡片
 *
 * 表单状态由页面持有, 三处行列表的结构与文案是本卡片自己的事
 */
const props = defineProps<{
  form: {
    footer_text: string
    social_links: LinkRow[]
    website_links: LinkRow[]
    beian_info: LinkRow[]
  }
}>()

/** 表单对象由页面持有, 这里取别名后直接读写其字段(与 PostFormFields 同一套做法) */
const form = props.form

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
  form[key].push({ name: '', url: '' })
}
</script>

<template>
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
</template>

<style scoped>
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
/* 每行常驻一个红色"删除"整屏都是噪音, 默认灰, 鼠标移到该行才变红 */
.link-row .link-row-remove {
  flex: 0 0 auto;
  color: var(--muted);
}
.link-row:hover .link-row-remove {
  color: var(--danger);
}
</style>
