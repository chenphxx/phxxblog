<script setup lang="ts">
/**
 * @brief 系统设置 - SEO 卡片
 *
 * 表单状态由页面持有, 这里只读写本卡片用到的字段
 */
const props = defineProps<{
  form: {
    site_keywords: string
    site_desc: string
  }
}>()

/** 表单对象由页面持有, 这里取别名后直接读写其字段(与 PostFormFields 同一套做法) */
const form = props.form
</script>

<template>
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
</template>
