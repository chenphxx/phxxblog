<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mediaApi, settingsApi } from '@/api'

const form = ref({
  site_name: '',
  site_desc: '',
  site_keywords: '',
  site_icon: '',
  site_avatar: '',
  site_bio: '',
  site_readme: '',
  tech_tags: [] as string[],
  social_links: [] as { name: string; url: string }[],
  website_links: [] as { name: string; url: string }[],
})
const saving = ref(false)
const uploadingIcon = ref(false)

function parseArray<T>(raw: string | undefined, fallback: T): T {
  if (!raw) return fallback
  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

async function load() {
  const data = await settingsApi.all()
  form.value = {
    site_name: data.site_name || '',
    site_desc: data.site_desc || '',
    site_keywords: data.site_keywords || '',
    site_icon: data.site_icon || '',
    site_avatar: data.site_avatar || '',
    site_bio: data.site_bio || '',
    site_readme: data.site_readme || '',
    tech_tags: parseArray<string[]>(data.tech_tags, []),
    social_links: parseArray<{ name: string; url: string }[]>(data.social_links, []),
    website_links: parseArray<{ name: string; url: string }[]>(data.website_links, []),
  }
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
    const payload: Record<string, unknown> = { ...form.value }
    await settingsApi.update(payload)
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2 style="margin: 0">系统设置</h2>
      <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
    </div>

    <div class="card" style="margin-top: 16px">
      <el-form label-position="top">
        <el-form-item label="站点名称">
          <el-input v-model="form.site_name" />
        </el-form-item>
        <el-form-item label="站点描述(SEO)">
          <el-input v-model="form.site_desc" />
        </el-form-item>
        <el-form-item label="SEO 关键词">
          <el-input v-model="form.site_keywords" />
        </el-form-item>
        <el-form-item label="站点图标(浏览器标签页图标, 可上传或填写 URL)">
          <div style="display: flex; gap: 12px; align-items: center; width: 100%">
            <img v-if="form.site_icon" :src="form.site_icon" alt="icon" style="width: 32px; height: 32px; border-radius: 4px" />
            <el-input v-model="form.site_icon" placeholder="/assets/uploads/... 或 https://..." style="flex: 1" />
            <el-upload :show-file-list="false" :http-request="uploadIcon" accept="image/*">
              <el-button :loading="uploadingIcon">本地上传</el-button>
            </el-upload>
          </div>
        </el-form-item>
        <el-form-item label="首页头像 URL">
          <el-input v-model="form.site_avatar" placeholder="/assets/images/秋白.png 或 https://..." />
        </el-form-item>
        <el-form-item label="个人简介">
          <el-input v-model="form.site_bio" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="主页 README(GitHub 风格, 支持 Markdown)">
          <el-input v-model="form.site_readme" type="textarea" :rows="8" placeholder="介绍自己/项目, 支持 Markdown 语法" />
        </el-form-item>
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
        <el-form-item label="社交链接(名称 + 链接)">
          <div style="width: 100%">
            <div v-for="(link, index) in form.social_links" :key="index" class="link-row">
              <el-input v-model="link.name" placeholder="名称(如 GitHub)" style="width: 200px" />
              <el-input v-model="link.url" placeholder="链接(https://...)" />
              <el-button type="danger" text @click="form.social_links.splice(index, 1)">删除</el-button>
            </div>
            <el-button size="small" @click="form.social_links.push({ name: '', url: '' })">添加链接</el-button>
          </div>
        </el-form-item>
        <el-form-item label="网站链接(名称 + 链接, 名称留空自动取网站名)">
          <div style="width: 100%">
            <div v-for="(link, index) in form.website_links" :key="index" class="link-row">
              <el-input v-model="link.name" placeholder="名称(留空自动取网站名)" style="width: 200px" />
              <el-input v-model="link.url" placeholder="链接(https://...)" />
              <el-button type="danger" text @click="form.website_links.splice(index, 1)">删除</el-button>
            </div>
            <el-button size="small" @click="form.website_links.push({ name: '', url: '' })">添加链接</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.link-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}
.link-row .el-input {
  flex: 1;
}
</style>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
