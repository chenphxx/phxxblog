<script setup lang="ts">
/** 单文件上传上限(MB)的可配置范围与默认值, 与后端 core/settings_schema.py 保持一致 */
const UPLOAD_SIZE_MIN_MB = 1
const UPLOAD_SIZE_MAX_MB = 2048

/**
 * @brief 系统设置 - 上传卡片
 *
 * 表单状态由页面持有, 这里只读写单文件上传上限
 */
const props = defineProps<
{
    form:
    {
        max_upload_size_mb: number
    }
}>()

/** 表单对象由页面持有, 这里取别名后直接读写其字段(与 PostFormFields 同一套做法) */
const form = props.form
</script>

<template>
    <div class="card">
        <h3>上传</h3>
        <el-form label-position="top">
            <el-form-item label="单文件上限">
                <div class="upload-row">
                    <el-input-number
                        v-model="form.max_upload_size_mb"
                        :min="UPLOAD_SIZE_MIN_MB"
                        :max="UPLOAD_SIZE_MAX_MB"
                        :step="10"
                        :precision="0"
                        controls-position="right"
                    />
                    <span class="muted">MB</span>
                </div>
            </el-form-item>
        </el-form>
    </div>
</template>

<style scoped>
.upload-row
{
    display: flex;
    align-items: center;
    gap: 8px;
}
</style>
