<script setup lang="ts">
/**
 * 导入查重 / 导入 / 导出三个弹窗(admin/PostManageView 与 DiaryView 共用)。
 *
 * 状态与流程都在 useImportExport 里, 这里只做渲染; io 是稳定的 reactive 对象,
 * 因此直接引用 props.io 而不解构。文案差异(标题与说明)由各自的视图以 prop 传入,
 * 因为说明文字必须紧挨着对应的接口(字段要求、查重依据都不同)。
 */
import type { ImportExportState } from '@/composables/useImportExport'

const props = defineProps<{
  io: ImportExportState
  importTitle: string
  dupTitle: string
  exportTitle: string
  /** 导入弹窗的"文件要求"说明 */
  importHint: string
  /** 查重弹窗中"重复依据"的说明 */
  dupHint: string
  /** 导出弹窗的说明 */
  exportHint: string
}>()
const io = props.io
</script>

<template>
  <el-dialog v-model="io.importDialog" :title="importTitle" width="600px">
    <el-alert type="info" :closable="false" show-icon>
      <template #title>文件要求</template>
      {{ importHint }}
    </el-alert>
    <div class="io-picker">
      <label class="el-button">
        <input type="file" multiple accept=".md,.zip" hidden @change="io.onImportPick" />
        选择文件
      </label>
      <span v-if="io.importFiles.length" class="muted">已选 {{ io.importFiles.length }} 个文件</span>
      <ul v-if="io.importFiles.length" class="io-files">
        <li v-for="(file, index) in io.importFiles" :key="index">{{ file.name }}</li>
      </ul>
    </div>
    <template #footer>
      <el-button @click="io.importDialog = false">取消</el-button>
      <el-button type="primary" :loading="io.importing" @click="io.doImport">开始导入</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="io.dupDialog" :title="dupTitle" width="560px">
    <el-alert type="warning" :closable="false" show-icon>
      <template #title>
        共 {{ io.duplicateTotal }} {{ io.unit }}待导入, 其中 {{ io.duplicateCount }} {{ io.unit }}与已有{{
          io.entity
        }}重复
      </template>
      {{ dupHint }}
    </el-alert>
    <ul v-if="io.duplicates.length" class="io-files">
      <li v-for="(item, index) in io.duplicates" :key="index">{{ item }}</li>
    </ul>
    <template #footer>
      <el-button @click="io.dupDialog = false">取消</el-button>
      <el-button :loading="io.importing" @click="io.runImport('skip')">仅导入不重复</el-button>
      <el-button type="primary" :loading="io.importing" @click="io.runImport('all')">导入全部</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="io.exportDialog" :title="exportTitle" width="460px">
    <el-form label-position="top">
      <el-form-item label="导出格式">
        <el-radio-group v-model="io.exportFmt">
          <el-radio value="markdown">Markdown(.md)</el-radio>
          <el-radio value="html">HTML(.html)</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
    <p class="muted">{{ exportHint }}</p>
    <template #footer>
      <el-button @click="io.exportDialog = false">取消</el-button>
      <el-button type="primary" :loading="io.exporting" @click="io.doExport">导出</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.io-picker {
  margin-top: 16px;
}
.io-files {
  margin: 10px 0 0;
  padding-left: 20px;
  max-height: 160px;
  overflow-y: auto;
  font-size: 13px;
}
</style>
