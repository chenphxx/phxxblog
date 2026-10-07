<script setup lang="ts">
/**
 * @brief 系统设置 - 基础信息卡片
 *
 * 表单状态由页面持有, 这里只读写本卡片用到的字段(与 PostFormFields 同一套做法)
 */
const props = defineProps<{
  form: {
    site_name: string
    site_title: string
    site_icon: string
    site_bio: string
  }
  /** 站点图标是否正在上传 */
  uploadingIcon: boolean
  /** 上传站点图标; 由页面实现, 成功后直接改写 form.site_icon */
  uploadIcon: (file: File) => Promise<void>
}>()

/** 表单对象由页面持有, 这里取别名后直接读写其字段(与 PostFormFields 同一套做法) */
const form = props.form
</script>

<template>
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
          <el-upload
            :show-file-list="false"
            :http-request="(options: { file: File }) => uploadIcon(options.file)"
            accept="image/*"
          >
            <el-button :loading="uploadingIcon">本地上传</el-button>
          </el-upload>
        </div>
      </el-form-item>
      <el-form-item label="个人简介">
        <el-input v-model="form.site_bio" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
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
  border-radius: var(--radius-chip);
  object-fit: contain;
}
/* 未设置图标时占位, 避免这一行的高度随有无图标跳动 */
.icon-preview--empty {
  border: 1px solid var(--border-strong);
  background: var(--code-bg);
}
</style>
