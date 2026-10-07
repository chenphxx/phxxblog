<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mediaApi, settingsApi } from '@/api'
import FooterLinksCard from './settings/FooterLinksCard.vue'
import HomeContentCard from './settings/HomeContentCard.vue'
import SeoCard from './settings/SeoCard.vue'
import SiteBasicCard from './settings/SiteBasicCard.vue'
import UploadCard from './settings/UploadCard.vue'

/** 三类"行列表"共用同一份列结构, 只有备案信息会多渲染一列可选图标 */
interface LinkRow {
  name: string
  url: string
  icon?: string
}

/** 单文件上传上限(MB)的默认值, 与后端 core/settings_schema.py 保持一致 */
const UPLOAD_SIZE_DEFAULT_MB = 100

/*
 * 表单状态由页面独占(各卡片只读写自己那几个字段), 这样"未保存修改"的判定
 * 与保存时的整体提交都只有一个来源
 */
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
  max_upload_size_mb: UPLOAD_SIZE_DEFAULT_MB,
})
/** 最近一次载入/保存后的表单快照, 与当前表单对比即可判断是否有未保存的修改 */
const snapshot = ref(JSON.stringify(form.value))
const saving = ref(false)
const uploadingIcon = ref(false)

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

async function load() {
  const data = await settingsApi.all()
  /*
   * 原地更新而不是整体替换: 各子卡片拿到的是同一个表单对象,
   * 替换对象会让它们继续指向旧值(表现为卡片里全是空的)
   */
  Object.assign(form.value, {
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
    max_upload_size_mb: Number(data.max_upload_size_mb) || UPLOAD_SIZE_DEFAULT_MB,
  })
  snapshot.value = currentSnapshot()
}

async function uploadIcon(file: File) {
  uploadingIcon.value = true
  try {
    const media = await mediaApi.upload(file)
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
      max_upload_size_mb: Number(form.value.max_upload_size_mb) || UPLOAD_SIZE_DEFAULT_MB,
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

    <!-- 页眉与其它后台页保持一致: h2 独占一行, 下面是"左侧说明 + 右侧操作"的工具条 -->
    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <span class="muted">
          <template v-if="dirty">有未保存的修改</template>
          <template v-else>所有修改都已保存</template>
        </span>
      </div>
      <div class="admin-toolbar-actions">
        <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
      </div>
    </div>

    <div class="settings-cards">
      <SiteBasicCard :form="form" :uploading-icon="uploadingIcon" :upload-icon="uploadIcon" />
      <SeoCard :form="form" />
      <HomeContentCard :form="form" />
      <FooterLinksCard :form="form" />
      <UploadCard :form="form" />
    </div>
  </div>
</template>

<style scoped>
/* 每张卡片一个配置域, 卡片间距与个人资料页保持一致 */
.settings-cards {
  display: grid;
  gap: 20px;
}
</style>
