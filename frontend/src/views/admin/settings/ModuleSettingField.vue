<script setup lang="ts">
import { computed, ref } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import MarkdownView from '@/components/MarkdownView.vue'
import type { ConfigRow, ModuleSettingSpec, ModuleSettingValue } from '@/types'
import { rowsOf, textOf } from '@/utils/moduleConfig'
import { countWords } from '@/utils/textStats'

/**
 * @brief 后台 - 模块的一项配置
 *
 * 按配置声明的类型渲染控件: 开关 / 数字 / 单行文本 / 多行文本(带 Markdown 预览) /
 * 行列表 值由页面持有, 这里只做展示与回写
 *
 * 功能的开关在"模块管理"里, 参数在"系统设置"里, 所以本组件属于系统设置页
 */
const props = defineProps<{
  setting: ModuleSettingSpec
  value: ModuleSettingValue | undefined
}>()

const emit = defineEmits<{ (e: 'update:value', value: ModuleSettingValue): void }>()

/**
 * 行列表的列名是技术键名(name/url/icon), 后台要给人看
 *
 * 未登记的列名直接显示键名, 因此模块新增一列时不必同时改这里
 */
const COLUMN_LABELS: Record<string, string> = {
  name: '名称',
  url: '链接(https://...)',
  icon: '图标(选填)',
}

/** 多行文本是否切到渲染预览(与原先系统设置页的 README 编辑一致) */
const preview = ref(false)

const text = computed(() => textOf(props.value))
const rows = computed(() => rowsOf(props.value))
const words = computed(() => countWords(text.value))

/** 行列表里某个单元格的值(缺列按空串处理) */
function cellOf(row: ConfigRow, column: string): string {
  return row[column] ?? ''
}

/** 行列表列名的展示文案 */
function columnLabel(column: string): string {
  return COLUMN_LABELS[column] ?? column
}

/** 改写某一行的一列; 返回新数组, 让父组件的"未保存"判定能按内容比较 */
function updateCell(index: number, column: string, value: string) {
  emit(
    'update:value',
    rows.value.map((row, i) => (i === index ? { ...row, [column]: value } : row)),
  )
}

/** 在末尾追加一行空数据 */
function addRow() {
  const columns = props.setting.columns ?? []
  if (!columns.length) {
    // 后端没下发列名时说明前后端版本不一致: 直接说出来, 而不是抛一个看不懂的 TypeError
    // (列名由后端模块元数据声明, 见 app/modules/state.py 的 admin_state)
    ElMessage.error('这个配置项没有声明列名, 无法添加行')
    return
  }
  const empty = Object.fromEntries(columns.map((column) => [column, '']))
  emit('update:value', [...rows.value, empty])
}

/** 删除一行 */
function removeRow(index: number) {
  emit(
    'update:value',
    rows.value.filter((_, i) => i !== index),
  )
}
</script>

<template>
  <div class="setting-item" :class="{ 'is-wide': setting.kind === 'long_text' || setting.kind === 'rows' }">
    <label class="setting-label">
      {{ setting.name }}
      <span v-if="setting.kind === 'long_text'" class="muted setting-meta">{{ words }} 字</span>
      <span v-if="setting.kind === 'long_text'" class="setting-preview-switch">
        <el-switch v-model="preview" size="small" />
        <span class="muted">预览</span>
      </span>
      <span v-if="setting.description" class="muted setting-desc">{{ setting.description }}</span>
    </label>

    <el-switch
      v-if="setting.kind === 'bool'"
      :model-value="Boolean(value)"
      @update:model-value="(next: string | number | boolean) => emit('update:value', Boolean(next))"
    />

    <el-input-number
      v-else-if="setting.kind === 'int'"
      :model-value="Number(value)"
      :min="setting.minimum ?? undefined"
      :max="setting.maximum ?? undefined"
      controls-position="right"
      style="width: 160px"
      @update:model-value="(next: number | undefined) => emit('update:value', next ?? 0)"
    />

    <template v-else-if="setting.kind === 'long_text'">
      <div v-if="preview" class="long-text-preview">
        <MarkdownView :content="text" />
      </div>
      <el-input
        v-else
        type="textarea"
        :rows="12"
        :model-value="text"
        @update:model-value="(next: string) => emit('update:value', next)"
      />
    </template>

    <div v-else-if="setting.kind === 'rows'" class="rows-editor">
      <div v-for="(row, index) in rows" :key="index" class="rows-row">
        <span class="rows-index">{{ index + 1 }}</span>
        <el-input
          v-for="column in setting.columns"
          :key="column"
          class="rows-input"
          :model-value="cellOf(row, column)"
          :placeholder="columnLabel(column)"
          @update:model-value="(next: string) => updateCell(index, column, next)"
        />
        <el-button class="rows-remove" text :icon="Delete" title="删除这一行" @click="removeRow(index)" />
      </div>
      <el-button size="small" @click="addRow">添加一行</el-button>
    </div>

    <el-input
      v-else
      :model-value="text"
      style="max-width: 520px"
      clearable
      @update:model-value="(next: string) => emit('update:value', next)"
    />
  </div>
</template>

<style scoped>
/* 配置项: 一行一个, 名称在上、控件在下 */
.setting-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

/* 多行文本与行列表占满整行: 窄列里编辑 Markdown 与多列行列表都没法用 */
.setting-item.is-wide {
  grid-column: 1 / -1;
}

.setting-label {
  font-size: 13px;
  color: var(--text);
}

.setting-desc {
  margin-left: 6px;
  font-size: 12px;
}

.setting-meta {
  margin-left: 8px;
  font-size: 12px;
}

.setting-preview-switch {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 16px;
  font-size: 12px;
}

.long-text-preview {
  width: 100%;
  padding: 4px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--card-bg);
}

/* 行列表: 序号 + 各列输入 + 删除, "添加"按钮按序号列宽度缩进以对齐名称框 */
.rows-editor {
  width: 100%;
  max-width: 720px;
  --rows-index-width: 16px;
  --rows-gap: 10px;
}

.rows-row {
  display: flex;
  align-items: center;
  gap: var(--rows-gap);
  margin-bottom: 10px;
}

.rows-index {
  flex: 0 0 var(--rows-index-width);
  text-align: right;
  font-size: 12px;
  color: var(--muted);
}

.rows-row .el-input {
  flex: 1 1 auto;
}

/* 每行常驻一个红色"删除"整屏都是噪音, 默认灰, 鼠标移到该行才变红 */
.rows-row .rows-remove {
  flex: 0 0 auto;
  color: var(--muted);
}

.rows-row:hover .rows-remove {
  color: var(--danger);
}

.rows-editor > .el-button {
  margin-left: calc(var(--rows-index-width) + var(--rows-gap));
}
</style>
