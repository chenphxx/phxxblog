<script setup lang="ts">
/** 单文件上传上限(MB)的可配置范围与默认值, 与后端 core/settings_schema.py 保持一致 */
const UPLOAD_SIZE_MIN_MB = 1
const UPLOAD_SIZE_MAX_MB = 2048

/**
 * @brief 系统设置 - 上传卡片
 *
 * 表单状态由页面持有, 这里只读写单文件上传上限
 */
const props = defineProps<{
  form: {
    max_upload_size_mb: number
  }
}>()

/** 表单对象由页面持有, 这里取别名后直接读写其字段(与 PostFormFields 同一套做法) */
const form = props.form
</script>

<template>
  <div class="card">
    <h3>上传 <span class="vis-badge is-admin">仅管理员可见</span></h3>
    <p class="muted section-hint">限制单次上传文件的体积, 全站所有上传入口共用这个上限</p>
    <el-form label-position="top">
      <el-form-item label="单文件上传大小上限(MB)">
        <el-input-number
          v-model="form.max_upload_size_mb"
          :min="UPLOAD_SIZE_MIN_MB"
          :max="UPLOAD_SIZE_MAX_MB"
          :step="10"
          :precision="0"
          controls-position="right"
        />
        <div class="muted form-hint">可设置 {{ UPLOAD_SIZE_MIN_MB }} ~ {{ UPLOAD_SIZE_MAX_MB }} MB, 超出即上传失败</div>
      </el-form-item>
    </el-form>
  </div>
</template>
